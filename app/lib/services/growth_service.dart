import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/growth.dart';
import 'api_client.dart';

/// Flutter API client for the Kiwimath Growth Journey system.
///
/// Uses [ApiClient.baseUrl] for URL resolution and mirrors the retry /
/// error-handling patterns from [ApiClient] and [EngagementService].
class GrowthService {
  GrowthService._();
  static final GrowthService instance = GrowthService._();

  static const _jsonHeaders = {'Content-Type': 'application/json'};

  // ---------------------------------------------------------------------------
  // Retry helper (same semantics as ApiClient._withRetry)
  // ---------------------------------------------------------------------------

  Future<http.Response> _withRetry(
      Future<http.Response> Function() request) async {
    const maxAttempts = 3;
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        final res = await request();
        if (res.statusCode >= 500 && attempt < maxAttempts) {
          await Future.delayed(Duration(milliseconds: 500 * attempt));
          continue;
        }
        return res;
      } on Exception {
        if (attempt == maxAttempts) rethrow;
        await Future.delayed(Duration(milliseconds: 500 * attempt));
      }
    }
    return await request();
  }

  // ---------------------------------------------------------------------------
  // 1. GET /growth/journey — Full growth journey aggregate
  // ---------------------------------------------------------------------------

  /// Fetch the student's full growth journey including current/baseline levels,
  /// deltas, engagement stats, and milestone count.
  /// Returns `null` when no journey data exists (no diagnostic taken).
  Future<GrowthJourney?> getJourney({
    required String userId,
    required int grade,
  }) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
    };
    final uri = Uri.parse('${ApiClient.baseUrl}/growth/journey')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /growth/journey failed: ${res.statusCode} ${res.body}');
    }
    return GrowthJourney.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 2. GET /growth/topics — Per-topic growth deltas
  // ---------------------------------------------------------------------------

  /// Fetch per-topic growth data: current vs baseline level, trend, accuracy.
  Future<List<TopicGrowth>> getTopics({
    required String userId,
    required int grade,
  }) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
    };
    final uri = Uri.parse('${ApiClient.baseUrl}/growth/topics')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /growth/topics failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    final list = data['topics'] as List<dynamic>;
    return list
        .map((e) => TopicGrowth.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---------------------------------------------------------------------------
  // 3. GET /growth/timeline — Scale score history for sparkline
  // ---------------------------------------------------------------------------

  /// Fetch timeline data (theta snapshots over time) for the sparkline chart.
  /// Returns a map with `snapshots` (List), `growth_summary`, and `engagement_milestones`.
  Future<Map<String, dynamic>> getTimeline({
    required String userId,
  }) async {
    final params = <String, String>{'user_id': userId};
    final uri = Uri.parse('${ApiClient.baseUrl}/growth/timeline')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /growth/timeline failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 4. GET /growth/milestones — Achievement timeline events
  // ---------------------------------------------------------------------------

  /// Fetch milestone events for the journey timeline.
  Future<List<GrowthMilestone>> getMilestones({
    required String userId,
    required int grade,
  }) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
    };
    final uri = Uri.parse('${ApiClient.baseUrl}/growth/milestones')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /growth/milestones failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    final list = data['milestones'] as List<dynamic>;
    return list
        .map((e) => GrowthMilestone.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---------------------------------------------------------------------------
  // 5. GET /growth/has-diagnostic — Check if diagnostic exists
  // ---------------------------------------------------------------------------

  /// Quick check whether the student has completed at least one diagnostic.
  Future<bool> hasDiagnostic({required String userId}) async {
    final params = <String, String>{'user_id': userId};
    final uri = Uri.parse('${ApiClient.baseUrl}/growth/has-diagnostic')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) return false;
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return data['has_diagnostic'] as bool? ?? false;
  }

  // ---------------------------------------------------------------------------
  // 6. POST /growth/diagnostic/save-baseline — Save diagnostic baseline
  // ---------------------------------------------------------------------------

  /// Save diagnostic results as a growth baseline.
  Future<void> saveDiagnosticBaseline({
    required String userId,
    required int grade,
    required String benchmarkId,
    required double theta,
    required Map<String, double> perTopicTheta,
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/growth/diagnostic/save-baseline');
    final body = {
      'user_id': userId,
      'grade': grade,
      'benchmark_id': benchmarkId,
      'theta': theta,
      'per_topic_theta': perTopicTheta,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /growth/diagnostic/save-baseline failed: ${res.statusCode} ${res.body}');
    }
  }
}
