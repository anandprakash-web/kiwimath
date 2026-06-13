import 'dart:async';
import 'dart:convert';
import 'dart:io' show Platform, SocketException;

import 'package:flutter/foundation.dart';

import '../models/olympiad_worksheet.dart';
import '../models/question_v2.dart';
import '../models/student_levels.dart';
import '../models/user_profile.dart';
import 'auth_token.dart';
import 'authed_http.dart' as http;
import 'offline_store.dart';

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

  /// Retry wrapper for IDEMPOTENT requests (GETs only) — retries up to
  /// 2 extra times on timeout/5xx with increasing delay.
  ///
  /// Do NOT route mutations (POST/DELETE) through this: retrying a
  /// non-idempotent request can double-submit answers or reward claims.
  /// Use [_postOnce] for those instead.
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
      } on Exception {
        if (attempt == maxAttempts) rethrow;
        await Future.delayed(Duration(milliseconds: 500 * attempt));
      }
    }
    // Unreachable: the final attempt either returned or rethrew above.
    throw ApiException('retry loop exhausted unexpectedly');
  }

  /// Execute a mutation (POST/DELETE) exactly once — NO automatic retries.
  /// Callers that need dedupe protection attach an X-Idempotency-Key header
  /// (see [newIdempotencyKey]) so the backend can discard duplicates.
  Future<http.Response> _postOnce(Future<http.Response> Function() request) =>
      request();

  // ---------------------------------------------------------------------------
  // Offline-aware fetch with Hive cache fallback
  // ---------------------------------------------------------------------------

  /// Try a network call first; on success cache the result in [OfflineStore].
  /// On failure (SocketException, TimeoutException), fall back to the cache.
  /// Returns null if both network and cache miss.
  ///
  /// Usage:
  /// ```dart
  /// final questions = await api.fetchWithCache(
  ///   'topic_grade_3_arithmetic',
  ///   () async {
  ///     final res = await http.get(uri);
  ///     return List<Map<String, dynamic>>.from(jsonDecode(res.body));
  ///   },
  /// );
  /// ```
  Future<List<Map<String, dynamic>>?> fetchWithCache(
    String cacheKey,
    Future<List<Map<String, dynamic>>> Function() fetcher,
  ) async {
    try {
      final result = await fetcher();
      // Cache on success
      try {
        OfflineStore.instance.cacheQuestions(cacheKey, result);
      } catch (e) {
        debugPrint('ApiClient.fetchWithCache: cache write failed: $e');
      }
      return result;
    } on SocketException catch (_) {
      debugPrint('ApiClient.fetchWithCache: SocketException, falling back to cache ($cacheKey)');
    } on TimeoutException catch (_) {
      debugPrint('ApiClient.fetchWithCache: TimeoutException, falling back to cache ($cacheKey)');
    } on http.ClientException catch (_) {
      debugPrint('ApiClient.fetchWithCache: ClientException, falling back to cache ($cacheKey)');
    } catch (e) {
      // For other errors (e.g. ApiException for 4xx), don't fall back to cache
      // unless it's a network-related issue.
      if (e.toString().contains('SocketException') ||
          e.toString().contains('Connection refused') ||
          e.toString().contains('Network is unreachable')) {
        debugPrint('ApiClient.fetchWithCache: network error, falling back to cache ($cacheKey)');
      } else {
        rethrow;
      }
    }

    // Network failed — try cache
    try {
      final cached = OfflineStore.instance.getCachedQuestions(cacheKey);
      if (cached != null) {
        final age = OfflineStore.instance.getQuestionsCachedAt(cacheKey);
        debugPrint('ApiClient.fetchWithCache: serving from cache ($cacheKey, cached at $age)');
        return cached;
      }
    } catch (e) {
      debugPrint('ApiClient.fetchWithCache: cache read failed: $e');
    }

    return null;
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
    // Mutation: sent exactly once, with an idempotency key for backend dedupe.
    final idemHeaders = {
      'Content-Type': 'application/json',
      'X-Idempotency-Key': newIdempotencyKey(),
    };
    final res = await _postOnce(() => http
        .post(
          uri,
          headers: idemHeaders,
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
    final res = await _postOnce(() => http
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
    final res = await _postOnce(() => http
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
    final resp = await _postOnce(() => http.post(
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
    await _postOnce(() => http.post(
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
    final res = await _postOnce(() => http
        .post(uri,
            headers: {
              'Content-Type': 'application/json',
              'X-Idempotency-Key': newIdempotencyKey(),
            },
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
    String? childName,
    int? grade,
    String? avatar,
    String? curriculum,
  }) async {
    final body = <String, dynamic>{};
    if (name != null) body['display_name'] = name;
    if (childName != null) body['child_name'] = childName;
    if (grade != null) body['grade'] = grade;
    if (avatar != null) body['avatar'] = avatar;
    if (curriculum != null) body['curriculum'] = curriculum;
    final uri = Uri.parse('$baseUrl/v2/student/profile')
        .replace(queryParameters: {'user_id': userId});
    final res = await _postOnce(() => http
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
    final res = await _postOnce(() => http
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
    final res = await _postOnce(() => http
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
    final res = await _postOnce(() => http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': newIdempotencyKey(),
      },
      body: jsonEncode({'user_id': userId, 'topic_id': topicId}),
    ));
    return Map<String, dynamic>.from(jsonDecode(res.body));
  }

  // ---------------------------------------------------------------------------
  // v4 API — grade-topic structured adaptive content
  // ---------------------------------------------------------------------------

  /// List all grades with topic and question counts.
  Future<List<Map<String, dynamic>>> getGradesV4() async {
    final uri = Uri.parse('$baseUrl/v4/grades');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException('GET /v4/grades failed: ${res.statusCode}');
    }
    return List<Map<String, dynamic>>.from(jsonDecode(res.body));
  }

  /// List all adaptive topics for a grade.
  Future<List<Map<String, dynamic>>> getTopicsV4(int grade) async {
    final uri = Uri.parse('$baseUrl/v4/topics/$grade');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException('GET /v4/topics/$grade failed: ${res.statusCode}');
    }
    return List<Map<String, dynamic>>.from(jsonDecode(res.body));
  }

  /// Get the next adaptive question from v4 content.
  Future<Map<String, dynamic>> nextQuestionV4({
    required int grade,
    required String topicId,
    double theta = 0.0,
    List<String>? exclude,
  }) async {
    final params = <String, String>{
      'grade': grade.toString(),
      'topic_id': topicId,
      'theta': theta.toString(),
    };
    if (exclude != null && exclude.isNotEmpty) {
      params['exclude'] = exclude.join(',');
    }
    final uri = Uri.parse('$baseUrl/v4/next')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException('GET /v4/next failed: ${res.statusCode}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// List school curricula available for a grade.
  Future<List<String>> getCurriculaV4(int grade) async {
    final uri = Uri.parse('$baseUrl/v4/school/curricula/$grade');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException('GET /v4/school/curricula/$grade failed: ${res.statusCode}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return List<String>.from(data['curricula'] ?? []);
  }

  /// List chapters for a curriculum + grade from v4.
  Future<List<Map<String, dynamic>>> getChaptersV4({
    required String curriculum,
    required int grade,
  }) async {
    final uri = Uri.parse('$baseUrl/v4/school/$curriculum/$grade');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/school/$curriculum/$grade failed: ${res.statusCode}');
    }
    return List<Map<String, dynamic>>.from(jsonDecode(res.body));
  }

  /// School tab chapter list (v4 bank).
  ///
  /// GET /v4/school/{curriculum}/{grade} → list of
  /// {name, question_count, skill_ids, adaptive_topic_ids}.
  /// A 404 (no chapters for this combination) is returned as an empty list
  /// so the UI can show its friendly "coming soon" state instead of an error.
  Future<List<Map<String, dynamic>>> fetchSchoolChaptersV4({
    required String curriculum,
    required int grade,
  }) async {
    final uri = Uri.parse('$baseUrl/v4/school/$curriculum/$grade');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return [];
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/school/$curriculum/$grade failed: ${res.statusCode} ${res.body}');
    }
    return List<Map<String, dynamic>>.from(jsonDecode(res.body));
  }

  /// Questions for a single school chapter (v4 bank).
  ///
  /// GET /v4/school/{curriculum}/{grade}/{chapter} →
  /// {curriculum, grade, chapter, total, questions: [{id, stem, options/choices,
  /// skill_id, difficulty_tier, irt_b}]}.
  /// A 404 (chapter resolves to zero questions) is returned as an empty list.
  Future<List<Map<String, dynamic>>> fetchChapterQuestionsV4({
    required String curriculum,
    required int grade,
    required String chapter,
  }) async {
    final encodedChapter = Uri.encodeComponent(chapter);
    final uri =
        Uri.parse('$baseUrl/v4/school/$curriculum/$grade/$encodedChapter');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode == 404) return [];
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/school/$curriculum/$grade/$chapter failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return List<Map<String, dynamic>>.from(data['questions'] ?? []);
  }

  /// Download an offline question bundle for a topic.
  Future<Map<String, dynamic>> downloadOfflineBundle({
    required int grade,
    required String topicId,
    double theta = 0.0,
    int size = 15,
  }) async {
    final params = <String, String>{
      'grade': grade.toString(),
      'topic_id': topicId,
      'theta': theta.toString(),
      'size': size.toString(),
    };
    final uri = Uri.parse('$baseUrl/v4/offline/bundle')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException('GET /v4/offline/bundle failed: ${res.statusCode}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Sync offline session results back to server.
  Future<Map<String, dynamic>> syncOfflineResults({
    required String userId,
    required int grade,
    required String topicId,
    required List<Map<String, dynamic>> results,
    required double thetaAtDownload,
    required String downloadedAt,
  }) async {
    final uri = Uri.parse('$baseUrl/v4/offline/sync');
    final body = {
      'user_id': userId,
      'grade': grade,
      'topic_id': topicId,
      'results': results,
      'theta_at_download': thetaAtDownload,
      'downloaded_at': downloadedAt,
    };
    final res = await _postOnce(() => http
        .post(uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException('POST /v4/offline/sync failed: ${res.statusCode}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Acquire a session lock (multi-device protection).
  Future<Map<String, dynamic>> acquireSessionLock({
    required String userId,
    required String deviceId,
    String? topicId,
    int? grade,
  }) async {
    final uri = Uri.parse('$baseUrl/v4/session/lock');
    final body = <String, dynamic>{
      'user_id': userId,
      'device_id': deviceId,
    };
    if (topicId != null) body['topic_id'] = topicId;
    if (grade != null) body['grade'] = grade;
    final res = await _postOnce(() => http
        .post(uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body))
        .timeout(const Duration(seconds: 5)));
    if (res.statusCode == 409) {
      throw SessionLockException(jsonDecode(res.body)['detail']);
    }
    if (res.statusCode != 200) {
      throw ApiException('POST /v4/session/lock failed: ${res.statusCode}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Send heartbeat to keep session lock alive.
  Future<void> sessionHeartbeat({
    required String userId,
    required String deviceId,
  }) async {
    final params = {'user_id': userId, 'device_id': deviceId};
    final uri = Uri.parse('$baseUrl/v4/session/heartbeat')
        .replace(queryParameters: params);
    await _postOnce(() => http.post(uri).timeout(const Duration(seconds: 5)));
  }

  /// Release session lock when play ends.
  Future<void> releaseSessionLock({
    required String userId,
    required String deviceId,
  }) async {
    final uri = Uri.parse('$baseUrl/v4/session/unlock');
    await _postOnce(() => http
        .post(uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'user_id': userId, 'device_id': deviceId}))
        .timeout(const Duration(seconds: 5)));
  }

  // ---------------------------------------------------------------------------
  // Proficiency & Growth (Learning Outcomes)
  // ---------------------------------------------------------------------------

  /// Get student's proficiency level, scale score, and competency breakdown.
  Future<Map<String, dynamic>> getProficiency({
    required String userId,
    int grade = 0,
  }) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
    };
    final uri = Uri.parse('$baseUrl/v2/proficiency')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/proficiency failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Get all proficiency level definitions.
  Future<Map<String, dynamic>> getProficiencyLevels() async {
    final uri = Uri.parse('$baseUrl/v2/proficiency/levels');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/proficiency/levels failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Benchmark Tests (Learning Outcomes)
  // ---------------------------------------------------------------------------

  /// Create a structured benchmark/diagnostic test.
  Future<Map<String, dynamic>> createBenchmarkTest({
    required String userId,
    int grade = 1,
    String benchmarkType = 'diagnostic',
  }) async {
    final params = <String, String>{
      'user_id': userId,
      'grade': grade.toString(),
      'benchmark_type': benchmarkType,
    };
    final uri = Uri.parse('$baseUrl/v2/benchmark/create')
        .replace(queryParameters: params);
    final res = await _postOnce(
        () => http.post(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/benchmark/create failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Submit benchmark test responses and get scored results.
  Future<Map<String, dynamic>> submitBenchmarkTest({
    required String userId,
    required String testId,
    required List<Map<String, dynamic>> responses,
  }) async {
    final uri = Uri.parse('$baseUrl/v2/benchmark/submit');
    final res = await _postOnce(() => http
        .post(uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'user_id': userId,
              'test_id': testId,
              'responses': responses,
            }))
        .timeout(const Duration(seconds: 30)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/benchmark/submit failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Get benchmark test history and growth comparison.
  Future<Map<String, dynamic>> getBenchmarkHistory({
    required String userId,
  }) async {
    final params = <String, String>{'user_id': userId};
    final uri = Uri.parse('$baseUrl/v2/benchmark/history')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/benchmark/history failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Olympiad Worksheet API
  // ---------------------------------------------------------------------------

  /// Fetch a single olympiad worksheet for a grade and day.
  Future<OlympiadWorksheet> getOlympiadWorksheet(int grade, int day) async {
    final uri = Uri.parse('$baseUrl/olympiad/worksheets')
        .replace(queryParameters: {'grade': '$grade', 'day': '$day'});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /olympiad/worksheets failed: ${res.statusCode} ${res.body}');
    }
    return OlympiadWorksheet.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  /// List all available worksheet days for a grade (legacy — returns day numbers only).
  Future<List<int>> getOlympiadWorksheetDays(int grade) async {
    final uri = Uri.parse('$baseUrl/olympiad/worksheets/list')
        .replace(queryParameters: {'grade': '$grade'});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /olympiad/worksheets/list failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    final days = data['days'] as List<dynamic>;
    return days.map((d) => d as int).toList();
  }

  /// List all worksheets with rich metadata for a grade.
  Future<List<WorksheetMeta>> getOlympiadWorksheetList(int grade) async {
    final uri = Uri.parse('$baseUrl/olympiad/worksheets/list')
        .replace(queryParameters: {'grade': '$grade'});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /olympiad/worksheets/list failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    final worksheets = data['worksheets'] as List<dynamic>? ?? [];
    return worksheets
        .map((w) => WorksheetMeta.fromJson(w as Map<String, dynamic>))
        .toList();
  }

  /// Get SVG visual URL for an olympiad question.
  String olympiadVisualUrl(String questionId) =>
      '$baseUrl/olympiad/questions/$questionId/visual';

  /// Get olympiad stats for a grade (or all grades if null).
  Future<Map<String, dynamic>> getOlympiadStats({int? grade}) async {
    final params = <String, String>{};
    if (grade != null) params['grade'] = '$grade';
    final uri = Uri.parse('$baseUrl/olympiad/stats')
        .replace(queryParameters: params.isNotEmpty ? params : null);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /olympiad/stats failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
  // ─── Wavebook (live class worksheet MCQs) ──────────────

  /// Get wavebook topics for a grade (G3-6 only).
  Future<Map<String, dynamic>> getWavebookTopics(int grade) async {
    final uri = Uri.parse('$baseUrl/wavebook/topics')
        .replace(queryParameters: {'grade': '$grade'});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /wavebook/topics failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Get wavebook questions for a specific topic.
  Future<Map<String, dynamic>> getWavebookQuestions(int grade, String topic) async {
    final uri = Uri.parse('$baseUrl/wavebook/questions')
        .replace(queryParameters: {'grade': '$grade', 'topic': topic});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /wavebook/questions failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Download wavebook topic as JSON file content.
  Future<String> downloadWavebookTopic(int grade, String topic) async {
    final uri = Uri.parse('$baseUrl/wavebook/download')
        .replace(queryParameters: {'grade': '$grade', 'topic': topic});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 30)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /wavebook/download failed: ${res.statusCode} ${res.body}');
    }
    return res.body;
  }

  // ---------------------------------------------------------------------------
  // Bookmarks API
  // ---------------------------------------------------------------------------

  /// Toggle bookmark on/off for a question.
  /// Returns {bookmarked: bool, total_bookmarks: int}.
  Future<Map<String, dynamic>> toggleBookmark(String userId, String questionId) async {
    final uri = Uri.parse('$baseUrl/v2/bookmarks/toggle');
    final res = await _postOnce(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'user_id': userId, 'question_id': questionId}),
        )
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v2/bookmarks/toggle failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Get paginated list of bookmarked questions with full question data.
  Future<Map<String, dynamic>> getBookmarks(String userId, {int page = 1, int perPage = 20}) async {
    final params = <String, String>{
      'user_id': userId,
      'page': page.toString(),
      'per_page': perPage.toString(),
    };
    final uri = Uri.parse('$baseUrl/v2/bookmarks/list')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/bookmarks/list failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Check if a specific question is bookmarked by the user.
  Future<bool> isBookmarked(String userId, String questionId) async {
    final params = <String, String>{
      'user_id': userId,
      'question_id': questionId,
    };
    final uri = Uri.parse('$baseUrl/v2/bookmarks/check')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v2/bookmarks/check failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return data['bookmarked'] as bool? ?? false;
  }

  // ---------------------------------------------------------------------------
  // Admin Review API
  // ---------------------------------------------------------------------------

  Future<bool> isAdmin(String email) async {
    final uri = Uri.parse('$baseUrl/admin/verify')
        .replace(queryParameters: {'email': email});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) return false;
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return data['is_admin'] as bool? ?? false;
  }

  Future<List<Map<String, dynamic>>> getReviewQuestions({
    int? grade,
    String? topic,
    int page = 1,
  }) async {
    final params = <String, String>{'page': page.toString()};
    if (grade != null) params['grade'] = grade.toString();
    if (topic != null) params['topic'] = topic;
    final uri = Uri.parse('$baseUrl/admin/review/questions')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/review/questions failed: ${res.statusCode} ${res.body}');
    }
    return List<Map<String, dynamic>>.from(jsonDecode(res.body));
  }

  Future<void> approveQuestion(String questionId, String email) async {
    final uri = Uri.parse('$baseUrl/admin/review/approve');
    final res = await _postOnce(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'question_id': questionId, 'email': email}),
        )
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /admin/review/approve failed: ${res.statusCode} ${res.body}');
    }
  }

  Future<void> adminFlagQuestion(
    String questionId,
    String email,
    String flagType,
    String comment, {
    String? correctAnswer,
  }) async {
    final body = <String, dynamic>{
      'question_id': questionId,
      'email': email,
      'flag_type': flagType,
      'comment': comment,
    };
    if (correctAnswer != null) body['correct_answer'] = correctAnswer;
    final uri = Uri.parse('$baseUrl/admin/review/flag');
    final res = await _postOnce(() => http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /admin/review/flag failed: ${res.statusCode} ${res.body}');
    }
  }

  Future<Map<String, dynamic>> getReviewStats() async {
    final uri = Uri.parse('$baseUrl/admin/review/stats');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/review/stats failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // Admin Analytics API
  // ---------------------------------------------------------------------------

  /// Fetch top-level analytics KPIs.
  Future<Map<String, dynamic>> getAnalyticsOverview(String email) async {
    final uri = Uri.parse('$baseUrl/admin/analytics/overview')
        .replace(queryParameters: {'email': email});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/analytics/overview failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch content quality analytics.
  Future<Map<String, dynamic>> getAnalyticsContent(String email) async {
    final uri = Uri.parse('$baseUrl/admin/analytics/content')
        .replace(queryParameters: {'email': email});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/analytics/content failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch user engagement analytics.
  Future<Map<String, dynamic>> getAnalyticsEngagement(String email, {int days = 30}) async {
    final uri = Uri.parse('$baseUrl/admin/analytics/engagement')
        .replace(queryParameters: {'email': email, 'days': days.toString()});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/analytics/engagement failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch learning outcomes analytics.
  Future<Map<String, dynamic>> getAnalyticsLearning(String email, {int? grade}) async {
    final params = <String, String>{'email': email};
    if (grade != null) params['grade'] = grade.toString();
    final uri = Uri.parse('$baseUrl/admin/analytics/learning')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/analytics/learning failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch revenue and growth analytics.
  Future<Map<String, dynamic>> getAnalyticsRevenue(String email) async {
    final uri = Uri.parse('$baseUrl/admin/analytics/revenue')
        .replace(queryParameters: {'email': email});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 20)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /admin/analytics/revenue failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}

class SessionLockException implements Exception {
  final Map<String, dynamic> detail;
  SessionLockException(this.detail);
  @override
  String toString() => 'SessionLockException: active on device ${detail['active_device']}';
}
