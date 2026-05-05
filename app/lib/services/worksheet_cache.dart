import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;

import '../models/olympiad_worksheet.dart';
import 'api_client.dart';

/// Spotify-style offline cache for olympiad worksheets.
///
/// Downloads worksheet JSON + pre-fetches SVG visuals for offline use.
/// Persists to device storage so worksheets work without internet.
class WorksheetCache {
  final ApiClient _api = ApiClient();

  static WorksheetCache? _instance;
  static WorksheetCache get instance => _instance ??= WorksheetCache._();
  WorksheetCache._();

  /// In-memory cache of loaded worksheets.
  final Map<String, OlympiadWorksheet> _memCache = {};

  /// Download state per grade: grade → set of downloaded days.
  final Map<int, Set<int>> _downloadedDays = {};

  /// Whether initial load from disk has happened.
  bool _initialized = false;

  // ── Initialization ──────────────────────────────────────────────────────

  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;
    await _loadDownloadState();
  }

  // ── Cache directory ─────────────────────────────────────────────────────

  Future<Directory> get _cacheDir async {
    final appDir = await getApplicationDocumentsDirectory();
    final dir = Directory('${appDir.path}/olympiad_cache');
    if (!await dir.exists()) await dir.create(recursive: true);
    return dir;
  }

  String _worksheetKey(int grade, int day) => 'g${grade}_d$day';

  Future<File> _worksheetFile(int grade, int day) async {
    final dir = await _cacheDir;
    return File('${dir.path}/g${grade}_d$day.json');
  }

  Future<File> _stateFile() async {
    final dir = await _cacheDir;
    return File('${dir.path}/_download_state.json');
  }

  Future<Directory> _svgDir(int grade) async {
    final dir = await _cacheDir;
    final svgDir = Directory('${dir.path}/svg_g$grade');
    if (!await svgDir.exists()) await svgDir.create(recursive: true);
    return svgDir;
  }

  // ── Download state persistence ──────────────────────────────────────────

  Future<void> _loadDownloadState() async {
    try {
      final file = await _stateFile();
      if (await file.exists()) {
        final data = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
        for (final entry in data.entries) {
          final grade = int.parse(entry.key);
          final days = (entry.value as List<dynamic>).map((d) => d as int).toSet();
          _downloadedDays[grade] = days;
        }
      }
    } catch (e) {
      debugPrint('WorksheetCache: failed to load state: $e');
    }
  }

  Future<void> _saveDownloadState() async {
    try {
      final file = await _stateFile();
      final data = <String, dynamic>{};
      for (final entry in _downloadedDays.entries) {
        data['${entry.key}'] = entry.value.toList();
      }
      await file.writeAsString(jsonEncode(data));
    } catch (e) {
      debugPrint('WorksheetCache: failed to save state: $e');
    }
  }

  // ── Public API ──────────────────────────────────────────────────────────

  /// Check if a worksheet is available offline.
  bool isDownloaded(int grade, int day) {
    return _downloadedDays[grade]?.contains(day) ?? false;
  }

  /// Get all downloaded days for a grade.
  Set<int> downloadedDays(int grade) {
    return _downloadedDays[grade] ?? {};
  }

  /// Get download progress for a grade (0.0 - 1.0).
  double downloadProgress(int grade) {
    final downloaded = _downloadedDays[grade]?.length ?? 0;
    return downloaded / 100.0;
  }

  /// Fetch worksheet — from cache if available, else from API.
  Future<OlympiadWorksheet> getWorksheet(int grade, int day) async {
    final key = _worksheetKey(grade, day);

    // 1. Memory cache
    if (_memCache.containsKey(key)) return _memCache[key]!;

    // 2. Disk cache
    try {
      final file = await _worksheetFile(grade, day);
      if (await file.exists()) {
        final data = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
        final ws = OlympiadWorksheet.fromJson(data);
        _memCache[key] = ws;
        return ws;
      }
    } catch (e) {
      debugPrint('WorksheetCache: disk read failed for $key: $e');
    }

    // 3. Fetch from API
    final ws = await _api.getOlympiadWorksheet(grade, day);
    _memCache[key] = ws;
    return ws;
  }

  /// Download a single worksheet for offline use.
  Future<void> downloadWorksheet(int grade, int day) async {
    final ws = await _api.getOlympiadWorksheet(grade, day);
    final key = _worksheetKey(grade, day);
    _memCache[key] = ws;

    // Save JSON to disk
    final file = await _worksheetFile(grade, day);
    await file.writeAsString(jsonEncode(ws.toJson()));

    // Pre-fetch SVGs
    await _downloadSvgs(grade, ws);

    // Update state
    _downloadedDays.putIfAbsent(grade, () => {});
    _downloadedDays[grade]!.add(day);
    await _saveDownloadState();
  }

  /// Download all worksheets for a grade (batch download).
  /// Returns a stream of progress (0.0 - 1.0).
  Stream<double> downloadGrade(int grade) async* {
    List<int> days;
    try {
      days = await _api.getOlympiadWorksheetDays(grade);
    } catch (e) {
      // Fallback: assume 1-100
      days = List.generate(100, (i) => i + 1);
    }

    int done = 0;
    for (final day in days) {
      if (!isDownloaded(grade, day)) {
        try {
          await downloadWorksheet(grade, day);
        } catch (e) {
          debugPrint('WorksheetCache: failed to download G$grade D$day: $e');
        }
      }
      done++;
      yield done / days.length;
    }
  }

  /// Delete all cached data for a grade.
  Future<void> deleteGrade(int grade) async {
    // Remove from memory
    _memCache.removeWhere((k, _) => k.startsWith('g${grade}_'));

    // Remove files
    for (int day = 1; day <= 100; day++) {
      try {
        final file = await _worksheetFile(grade, day);
        if (await file.exists()) await file.delete();
      } catch (_) {}
    }

    // Remove SVG directory
    try {
      final dir = await _svgDir(grade);
      if (await dir.exists()) await dir.delete(recursive: true);
    } catch (_) {}

    // Update state
    _downloadedDays.remove(grade);
    await _saveDownloadState();
  }

  /// Get total cache size in MB.
  Future<double> cacheSizeMb() async {
    try {
      final dir = await _cacheDir;
      int totalBytes = 0;
      await for (final entity in dir.list(recursive: true)) {
        if (entity is File) {
          totalBytes += await entity.length();
        }
      }
      return totalBytes / (1024 * 1024);
    } catch (_) {
      return 0.0;
    }
  }

  // ── SVG pre-fetch ───────────────────────────────────────────────────────

  Future<void> _downloadSvgs(int grade, OlympiadWorksheet ws) async {
    final dir = await _svgDir(grade);
    for (final q in ws.questions) {
      if (q.visualUrl != null || q.visualRef != null) {
        try {
          final url = _api.olympiadVisualUrl(q.id);
          final res = await http.get(Uri.parse(url))
              .timeout(const Duration(seconds: 10));
          if (res.statusCode == 200) {
            final file = File('${dir.path}/${q.id}.svg');
            await file.writeAsString(res.body);
          }
        } catch (e) {
          // Non-fatal — SVG will be fetched on demand
          debugPrint('WorksheetCache: SVG fetch failed for ${q.id}: $e');
        }
      }
    }
  }

  /// Get cached SVG string for a question (or null).
  Future<String?> getCachedSvg(int grade, String questionId) async {
    try {
      final dir = await _svgDir(grade);
      final file = File('${dir.path}/$questionId.svg');
      if (await file.exists()) return await file.readAsString();
    } catch (_) {}
    return null;
  }

  // ── Worksheet completion tracking ───────────────────────────────────────

  /// Save completion result for a worksheet.
  Future<void> saveResult(int grade, int day, WorksheetResult result) async {
    final dir = await _cacheDir;
    final file = File('${dir.path}/results_g$grade.json');
    Map<String, dynamic> results = {};
    try {
      if (await file.exists()) {
        results = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      }
    } catch (_) {}
    results['$day'] = result.toJson();
    await file.writeAsString(jsonEncode(results));
  }

  /// Load completion result for a worksheet (or null if not attempted).
  Future<WorksheetResult?> getResult(int grade, int day) async {
    try {
      final dir = await _cacheDir;
      final file = File('${dir.path}/results_g$grade.json');
      if (!await file.exists()) return null;
      final results = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      final data = results['$day'];
      if (data == null) return null;
      return WorksheetResult.fromJson(data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  /// Load all results for a grade.
  Future<Map<int, WorksheetResult>> getAllResults(int grade) async {
    try {
      final dir = await _cacheDir;
      final file = File('${dir.path}/results_g$grade.json');
      if (!await file.exists()) return {};
      final results = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      return results.map((k, v) =>
          MapEntry(int.parse(k), WorksheetResult.fromJson(v as Map<String, dynamic>)));
    } catch (_) {
      return {};
    }
  }
}

/// Result of completing a worksheet.
class WorksheetResult {
  final int correctCount;
  final int totalCount;
  final int timeSeconds;
  final DateTime completedAt;
  final int stars; // 0-3 based on score

  WorksheetResult({
    required this.correctCount,
    required this.totalCount,
    required this.timeSeconds,
    required this.completedAt,
    required this.stars,
  });

  double get accuracy => totalCount > 0 ? correctCount / totalCount : 0.0;

  factory WorksheetResult.fromJson(Map<String, dynamic> json) {
    return WorksheetResult(
      correctCount: json['correct_count'] as int? ?? 0,
      totalCount: json['total_count'] as int? ?? 0,
      timeSeconds: json['time_seconds'] as int? ?? 0,
      completedAt: DateTime.tryParse(json['completed_at'] as String? ?? '') ?? DateTime.now(),
      stars: json['stars'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'correct_count': correctCount,
        'total_count': totalCount,
        'time_seconds': timeSeconds,
        'completed_at': completedAt.toIso8601String(),
        'stars': stars,
      };
}
