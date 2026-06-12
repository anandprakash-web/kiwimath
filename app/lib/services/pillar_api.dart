import 'dart:convert';

import '../models/olympiad_worksheet.dart';
import '../models/pillar_progress.dart';
import 'api_client.dart';
import 'authed_http.dart' as http;

/// API client for the Olympiad v2 pillar-based system.
///
/// All endpoints live under /olympiad/v2/ on the same backend.
class PillarApi {
  static String get _base => '${ApiClient.baseUrl}/olympiad/v2';

  // ── Pillars & topics ────────────────────────────────────────────────────

  /// GET /olympiad/v2/pillars → list of pillars with level metadata
  static Future<List<Map<String, dynamic>>> fetchPillars({
    required int grade,
  }) async {
    final url = Uri.parse('$_base/pillars?grade=$grade');
    final res = await http.get(url).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) throw Exception('Failed to load pillars');
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return (body['pillars'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  /// GET /olympiad/v2/levels?pillar=X&grade=N → levels with topics
  static Future<List<Map<String, dynamic>>> fetchLevels({
    required String pillar,
    required int grade,
  }) async {
    final url = Uri.parse('$_base/levels?pillar=$pillar&grade=$grade');
    final res = await http.get(url).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) throw Exception('Failed to load levels');
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return (body['levels'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  /// GET /olympiad/v2/topics?pillar=X&level=N → topic list for a level
  static Future<List<Map<String, dynamic>>> fetchTopics({
    required String pillar,
    required int level,
  }) async {
    final url = Uri.parse('$_base/topics?pillar=$pillar&level=$level');
    final res = await http.get(url).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) throw Exception('Failed to load topics');
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return (body['topics'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  }

  // ── Worksheets ──────────────────────────────────────────────────────────

  /// GET /olympiad/v2/worksheet?pillar=X&level=N&topic=T → questions
  static Future<OlympiadWorksheet> fetchWorksheet({
    required String pillar,
    required int level,
    required String topic,
  }) async {
    final url = Uri.parse(
        '$_base/worksheet?pillar=$pillar&level=$level&topic=$topic');
    final res = await http.get(url).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) throw Exception('Failed to load worksheet');
    return OlympiadWorksheet.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ── Submission ──────────────────────────────────────────────────────────

  /// POST /olympiad/v2/submit → submit answer for a question
  static Future<Map<String, dynamic>> submitAnswer({
    required String userId,
    required String questionId,
    required dynamic answer,
    required int timeTakenSeconds,
  }) async {
    final url = Uri.parse('$_base/submit');
    final res = await http
        .post(
          url,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'user_id': userId,
            'question_id': questionId,
            'answer': answer,
            'time_taken_seconds': timeTakenSeconds,
          }),
        )
        .timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) throw Exception('Submit failed');
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// POST /olympiad/v2/submit-proof → submit subjective proof for AI grading
  static Future<Map<String, dynamic>> submitProof({
    required String userId,
    required String questionId,
    required String proofText,
    List<String>? imageUrls,
  }) async {
    final url = Uri.parse('$_base/submit-proof');
    final res = await http
        .post(
          url,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'user_id': userId,
            'question_id': questionId,
            'proof_text': proofText,
            if (imageUrls != null) 'image_urls': imageUrls,
          }),
        )
        .timeout(const Duration(seconds: 30)); // longer for AI grading
    if (res.statusCode != 200) throw Exception('Proof submission failed');
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ── Progress ────────────────────────────────────────────────────────────

  /// GET /olympiad/v2/progress?user_id=X → PillarSummary
  static Future<PillarSummary> fetchProgress({
    required String userId,
  }) async {
    final url = Uri.parse('$_base/progress?user_id=$userId');
    final res = await http.get(url).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) throw Exception('Failed to load progress');
    return PillarSummary.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ── Daily Challenge ─────────────────────────────────────────────────────

  /// GET /olympiad/v2/daily-challenge?grade=N → today's challenge question
  static Future<OlympiadQuestion?> fetchDailyChallenge({
    required int grade,
  }) async {
    final url = Uri.parse('$_base/daily-challenge?grade=$grade');
    final res = await http.get(url).timeout(const Duration(seconds: 10));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) throw Exception('Failed to load daily challenge');
    final body = jsonDecode(res.body) as Map<String, dynamic>;
    return OlympiadQuestion.fromJson(body['question'] as Map<String, dynamic>);
  }
}
