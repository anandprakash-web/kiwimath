import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/question_v2.dart';
import '../models/user_profile.dart';

/// Kiwimath backend API client (v2-only).
///
/// Base URL resolution:
/// - Web debug: http://localhost:8000
/// - Android emulator: http://10.0.2.2:8000
/// - iOS simulator / real device: override via --dart-define=KIWIMATH_API=http://<your-mac-ip>:8000
class ApiClient {
  /// Production Cloud Run URL (asia-south1, Mumbai).
  static const _productionUrl = 'https://kiwimath-api-deufqab6gq-el.a.run.app';

  static String get baseUrl {
    const override = String.fromEnvironment('KIWIMATH_API', defaultValue: '');
    if (override.isNotEmpty) return override;

    if (kIsWeb) {
      if (kDebugMode) return 'http://localhost:8000';
      return _productionUrl;
    }

    if (kDebugMode) {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000';
      return 'http://localhost:8000';
    }
    return _productionUrl;
  }

  /// Retry wrapper — retries up to 2 times on timeout/5xx with increasing delay.
  Future<http.Response> _withRetry(Future<http.Response> Function() request) async {
    const maxAttempts = 3;
    for (int attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        final res = await request();
        if (res.statusCode >= 500 && attempt < maxAttempts) {
          await Future.delayed(Duration(milliseconds: 500 * attempt));
          continue;
        }
        return res;
      } on Exception catch (e) {
        if (attempt == maxAttempts) rethrow;
        await Future.delayed(Duration(milliseconds: 500 * attempt));
      }
    }
    return await request();
  }

  Future<Map<String, dynamic>> health() async {
    final uri = Uri.parse('$baseUrl/health');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 5)));
    if (res.statusCode != 200) {
      throw ApiException('health check failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // User Profile API
  // ---------------------------------------------------------------------------

  /// Load user profile (streak, XP, gems, daily progress).
  Future<UserProfile> getProfile(String userId) async {
    final uri = Uri.parse('$baseUrl/user/profile')
        .replace(queryParameters: {'user_id': userId});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException('GET /user/profile failed: ${res.statusCode} ${res.body}');
    }
    return UserProfile.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // v2 API — adaptive practice with behavioral engine
  // ---------------------------------------------------------------------------

  /// Fetch all available topics, optionally filtered by grade.
  Future<List<TopicV2>> getTopicsV2({int? grade}) async {
    final params = <String, String>{};
    if (grade != null) params['grade'] = grade.toString();
    final uri = Uri.parse('$baseUrl/v2/topics')
        .replace(queryParameters: params.isNotEmpty ? params : null);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/topics failed: ${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list
        .map((e) => TopicV2.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Fetch the next question for a topic with adaptive difficulty.
  Future<QuestionV2> nextQuestionV2({
    String? topic,
    int? difficulty,
    int window = 10,
    List<String>? exclude,
    String? userId,
    int? grade,
  }) async {
    final params = <String, String>{};
    if (topic != null) params['topic'] = topic;
    if (difficulty != null) params['difficulty'] = difficulty.toString();
    params['window'] = window.toString();
    if (exclude != null && exclude.isNotEmpty) {
      params['exclude'] = exclude.join(',');
    }
    if (userId != null) params['user_id'] = userId;
    if (grade != null) params['grade'] = grade.toString();
    final uri = Uri.parse('$baseUrl/v2/questions/next')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/questions/next failed: ${res.statusCode} ${res.body}');
    }
    return QuestionV2.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  /// Fetch a specific v2 question by ID.
  Future<QuestionV2> getQuestionV2(String id) async {
    final uri = Uri.parse('$baseUrl/v2/questions/$id');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/questions/$id failed: ${res.statusCode} ${res.body}');
    }
    return QuestionV2.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  /// Check an answer for a v2 question.
  Future<AnswerCheckResponse> checkAnswerV2({
    required String questionId,
    required int selectedAnswer,
    String? userId,
    int timeTakenMs = 0,
    int hintsUsed = 0,
  }) async {
    final body = <String, dynamic>{
      'question_id': questionId,
      'selected_answer': selectedAnswer,
    };
    if (userId != null) body['user_id'] = userId;
    if (timeTakenMs > 0) body['time_taken_ms'] = timeTakenMs;
    if (hintsUsed > 0) body['hints_used'] = hintsUsed;
    final uri = Uri.parse('$baseUrl/v2/answer/check');
    final res = await _withRetry(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/answer/check failed: ${res.statusCode} ${res.body}');
    }
    return AnswerCheckResponse.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  /// Build the full URL for a v2 question's SVG visual.
  String visualUrlV2(String questionId) =>
      '$baseUrl/v2/questions/$questionId/visual';

  // ── Companion API ─────────────────────────────────────────────────

  /// Fetch companion config bundle (once per session).
  Future<Map<String, dynamic>> getCompanionConfig({
    String chosenPrimary = 'kiwi',
    String ageTier = 'k2',
    int appVersion = 1,
  }) async {
    final resp = await _withRetry(() => http.get(
          Uri.parse('$baseUrl/companion/config'
              '?chosen_primary=$chosenPrimary'
              '&age_tier=$ageTier'
              '&app_version=$appVersion'),
        ));
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// Summon a companion for a surface (server-side, for telemetry).
  Future<Map<String, dynamic>> summonCompanion({
    required String surface,
    String chosenPrimary = 'kiwi',
    String ageTier = 'k2',
    String? lessonId,
    int problemStepsRequired = 1,
    int picoAppearancesInLesson = 0,
  }) async {
    final resp = await _withRetry(() => http.post(
          Uri.parse('$baseUrl/companion/summon'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'surface': surface,
            'chosen_primary': chosenPrimary,
            'age_tier': ageTier,
            'lesson_id': lessonId,
            'problem_steps_required': problemStepsRequired,
            'pico_appearances_in_lesson': picoAppearancesInLesson,
          }),
        ));
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// Get full cast list with ship status.
  Future<Map<String, dynamic>> getCompanionCast({int appVersion = 1}) async {
    final resp = await _withRetry(() => http.get(
          Uri.parse('$baseUrl/companion/cast?app_version=$appVersion'),
        ));
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  /// Send a companion telemetry event.
  Future<void> sendCompanionTelemetry({
    required String event,
    required String companionId,
    required String surface,
    Map<String, dynamic> extra = const {},
  }) async {
    await _withRetry(() => http.post(
          Uri.parse('$baseUrl/companion/telemetry'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'event': event,
            'companion_id': companionId,
            'surface': surface,
            'extra': extra,
          }),
        ));
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}
