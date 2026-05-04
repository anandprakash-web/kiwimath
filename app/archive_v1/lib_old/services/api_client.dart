import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/question_v2.dart';
import '../models/student_levels.dart';
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

  /// Fetch chapters for a curriculum + grade (e.g. NCERT Grade 1 → Ch1..Ch13).
  Future<List<Map<String, dynamic>>> getChapters({
    required String curriculum,
    required int grade,
  }) async {
    final params = <String, String>{
      'curriculum': curriculum,
      'grade': grade.toString(),
    };
    final uri = Uri.parse('$baseUrl/v2/chapters')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/chapters failed: ${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list.cast<Map<String, dynamic>>();
  }

  /// Fetch the next question for a topic with adaptive difficulty.
  Future<QuestionV2> nextQuestionV2({
    String? topic,
    int? difficulty,
    int window = 10,
    List<String>? exclude,
    String? userId,
    int? grade,
    String? chapter,
    String? curriculum,
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
    if (chapter != null) params['chapter'] = chapter;
    if (curriculum != null) params['curriculum'] = curriculum;
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
    int? integerAnswer,
    List<int>? dragOrder,
    String? userId,
    int timeTakenMs = 0,
    int hintsUsed = 0,
  }) async {
    final body = <String, dynamic>{
      'question_id': questionId,
      'selected_answer': selectedAnswer,
    };
    if (integerAnswer != null) body['integer_answer'] = integerAnswer;
    if (dragOrder != null) body['drag_order'] = dragOrder;
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

  // ---------------------------------------------------------------------------
  // Question Feedback API (Task #194)
  // ---------------------------------------------------------------------------

  /// Submit user feedback on a question (flag/report).
  ///
  /// [feedbackType] must be one of: wrong_answer, unclear_stem, bad_visual,
  /// too_easy, too_hard, other.
  Future<Map<String, dynamic>> submitQuestionFeedback({
    required String questionId,
    required String feedbackType,
    String? userId,
    String? comment,
  }) async {
    final body = <String, dynamic>{
      'feedback_type': feedbackType,
    };
    if (userId != null) body['user_id'] = userId;
    if (comment != null && comment.trim().isNotEmpty) {
      body['comment'] = comment.trim();
    }
    final uri = Uri.parse('$baseUrl/v2/questions/$questionId/feedback');
    final res = await _withRetry(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/questions/$questionId/feedback failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Onboarding Benchmark (Task #196)
  // ---------------------------------------------------------------------------

  /// Fetch a list of benchmark questions for the diagnostic onboarding flow.
  Future<List<QuestionV2>> getBenchmarkQuestions({
    required int grade,
    int count = 10,
    String? userId,
  }) async {
    final params = <String, String>{
      'grade': grade.toString(),
      'count': count.toString(),
    };
    if (userId != null) params['user_id'] = userId;
    final uri = Uri.parse('$baseUrl/v2/onboarding/benchmark/questions')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/onboarding/benchmark/questions failed: ${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list
        .map((e) => QuestionV2.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Submit benchmark answers and get an initial ability profile.
  Future<Map<String, dynamic>> submitBenchmark({
    required String userId,
    required int grade,
    required List<Map<String, dynamic>> answers,
  }) async {
    final body = <String, dynamic>{
      'user_id': userId,
      'grade': grade,
      'answers': answers,
    };
    final uri = Uri.parse('$baseUrl/v2/onboarding/benchmark');
    final res = await _withRetry(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 30)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/onboarding/benchmark failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Parent Dashboard (Task #199)
  // ---------------------------------------------------------------------------

  /// Fetch parent dashboard summary for a child.
  Future<Map<String, dynamic>> getParentDashboard({
    required String userId,
    String? curriculum,
  }) async {
    final params = <String, String>{'user_id': userId};
    if (curriculum != null && curriculum.isNotEmpty) {
      params['curriculum'] = curriculum;
    }
    final uri = Uri.parse('$baseUrl/v2/parent/dashboard')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/parent/dashboard failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Adaptive Learning Path (Task #197)
  // ---------------------------------------------------------------------------

  /// Get a personalized topic + difficulty plan for the user.
  Future<Map<String, dynamic>> getLearningPath({required String userId, int? grade}) async {
    final params = <String, String>{'user_id': userId};
    if (grade != null) params['grade'] = grade.toString();
    final uri = Uri.parse('$baseUrl/v2/learning-path')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/learning-path failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

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

  // ---------------------------------------------------------------------------
  // Paywall / Topic Lock API
  // ---------------------------------------------------------------------------

  /// Get unlock status for all topics.
  Future<List<Map<String, dynamic>>> getPaywallStatus(String userId) async {
    final uri = Uri.parse('$baseUrl/v2/paywall/status').replace(
      queryParameters: {'user_id': userId},
    );
    final res = await _withRetry(() => http.get(uri));
    if (res.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(res.body));
    }
    return [];
  }

  // ---------------------------------------------------------------------------
  // Smart Session Engine
  // ---------------------------------------------------------------------------

  /// Fetch a smart session plan with questions across all topics.
  Future<Map<String, dynamic>> getSessionPlan(String userId, int grade, {int size = 10}) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
      'size': size.toString(),
    };
    final uri = Uri.parse('$baseUrl/v2/session/plan')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/session/plan failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch a unified cross-curriculum adaptive session (the new engine).
  /// Returns questions drawn from all curricula via the 37-node skill graph.
  Future<Map<String, dynamic>> getUnifiedSession(String userId, int grade, {int size = 10}) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
      'size': size.toString(),
    };
    final uri = Uri.parse('$baseUrl/v2/session/unified')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 25)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/session/unified failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Submit results for a completed unified session.
  /// Returns parent-facing summary with mastery updates.
  Future<Map<String, dynamic>> completeUnifiedSession({
    required String userId,
    required int grade,
    required List<Map<String, dynamic>> results,
  }) async {
    final uri = Uri.parse('$baseUrl/v2/session/unified/complete');
    final body = {
      'user_id': userId,
      'grade': grade,
      'results': results,
    };
    final res = await _withRetry(() => http
        .post(uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/session/unified/complete failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch cluster mastery overview for the home screen.
  Future<Map<String, dynamic>> getMasteryOverview(String userId, int grade) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
    };
    final uri = Uri.parse('$baseUrl/v2/mastery/overview')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/mastery/overview failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Student Profile & Levels (Task #285)
  // ---------------------------------------------------------------------------

  /// Save student profile (kid's name, grade, avatar).
  Future<Map<String, dynamic>> updateStudentProfile({
    required String userId,
    String? name,
    int? grade,
    String? avatar,
    String? curriculum,
  }) async {
    final body = <String, dynamic>{};
    if (name != null) body['display_name'] = name;
    if (grade != null) body['grade'] = grade;
    if (avatar != null) body['avatar'] = avatar;
    if (curriculum != null) body['curriculum'] = curriculum;
    final uri = Uri.parse('$baseUrl/v2/student/profile')
        .replace(queryParameters: {'user_id': userId});
    final res = await _withRetry(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/student/profile failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch student level progression (10 micro-levels per topic per grade).
  Future<StudentLevels> getStudentLevels({
    required String userId,
    int? grade,
  }) async {
    final params = <String, String>{'user_id': userId};
    if (grade != null) params['grade'] = grade.toString();
    final uri = Uri.parse('$baseUrl/v2/student/levels')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/student/levels failed: ${res.statusCode} ${res.body}');
    }
    return StudentLevels.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // Question Flagging API (closed-loop quality system)
  // ---------------------------------------------------------------------------

  /// Flag a problematic question for quality review.
  ///
  /// [flagType] must be one of: answer_error, hint_not_good, visual_missing,
  /// visual_mismatch, question_error, other.
  Future<Map<String, dynamic>> flagQuestion({
    required String questionId,
    required String studentId,
    required String flagType,
    String? comment,
    String? sessionId,
  }) async {
    final body = <String, dynamic>{
      'question_id': questionId,
      'student_id': studentId,
      'flag_type': flagType,
    };
    if (comment != null && comment.trim().isNotEmpty) {
      body['comment'] = comment.trim();
    }
    if (sessionId != null) body['session_id'] = sessionId;
    final uri = Uri.parse('$baseUrl/flag/submit');
    final res = await _withRetry(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /flag/submit failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Submit a batch of diagnostic review flags with reasons.
  ///
  /// Used by admin (Anand) to flag questions during diagnostic test review.
  /// Each flag item includes question_id, reason, severity, and optional grade.
  Future<Map<String, dynamic>> submitDiagnosticReview({
    required String reviewerId,
    required List<Map<String, dynamic>> flags,
    String? sessionNotes,
  }) async {
    final items = flags.map((f) => <String, dynamic>{
      'question_id': f['question_id'],
      'flag_type': 'diagnostic_review',
      'reason': f['reason'] ?? '',
      'severity': f['severity'] ?? 'medium',
      if (f['grade'] != null) 'grade': f['grade'],
    }).toList();

    final body = <String, dynamic>{
      'reviewer_id': reviewerId,
      'items': items,
    };
    if (sessionNotes != null) body['session_notes'] = sessionNotes;

    final uri = Uri.parse('$baseUrl/flag/diagnostic-review');
    final res = await _withRetry(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /flag/diagnostic-review failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Unlock a topic using Kiwi Coins (500 coins).
  Future<Map<String, dynamic>> unlockTopic(String userId, String topicId) async {
    final uri = Uri.parse('$baseUrl/v2/paywall/unlock');
    final res = await _withRetry(() => http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'user_id': userId, 'topic_id': topicId}),
    ));
    return Map<String, dynamic>.from(jsonDecode(res.body));
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}
