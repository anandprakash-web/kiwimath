import 'dart:convert';

import 'authed_http.dart' as http;
import 'api_client.dart' show ApiClient, ApiException;

/// Client for the v3 Level/Grade API (the remapped Olympiad + School banks
/// with the unified server-side economy). Mirrors the `ApiClient` style:
/// authed HTTP (Bearer token + X-Idempotency-Key injected by authed_http),
/// `ApiClient.baseUrl` for host resolution.
///
/// Olympiad is LEVEL-based (L1–L8). School is GRADE-based (board × grade ×
/// chapter). Coins/gems/XP/streak/awards and performance all come from one
/// source — see [checkAnswer], [getWallet], [getProgress].
class LevelService {
  String get _base => ApiClient.baseUrl;

  Future<Map<String, dynamic>> _getJson(String path) async {
    final res = await http
        .get(Uri.parse('$_base$path'))
        .timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      throw ApiException('GET $path failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------- olympiad
  /// All 8 levels with availability + topic counts (the app hides counts).
  Future<List<dynamic>> getLevels() async =>
      (await _getJson('/v3/olympiad/levels'))['levels'] as List<dynamic>;

  /// Topics for a level (friendly display names; empty levels return []).
  Future<List<dynamic>> getLevelTopics(String level) async =>
      (await _getJson('/v3/olympiad/levels/$level/topics'))['topics']
          as List<dynamic>;

  /// Next adaptive question (answer NOT included — comes from [checkAnswer]).
  Future<Map<String, dynamic>> getNextQuestion(
    String level,
    String topicKey, {
    String? userId,
    double theta = 0.0,
    List<String> exclude = const [],
  }) async {
    final q = <String, String>{'theta': '$theta'};
    if (userId != null) q['user_id'] = userId;
    if (exclude.isNotEmpty) q['exclude'] = exclude.join(',');
    final uri = Uri.parse('$_base/v3/olympiad/levels/$level/topics/$topicKey/next')
        .replace(queryParameters: q);
    final res = await http.get(uri).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      throw ApiException('next failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getQuestion(String qid) =>
      _getJson('/v3/olympiad/question/$qid');

  /// URL for the inline SVG visual (use with the AuthedSvg widget).
  String visualUrl(String qid) => '$_base/v3/olympiad/question/$qid/visual';

  // -------------------------------------------------------------- curriculum
  Future<List<dynamic>> getBoards() async =>
      (await _getJson('/v3/curriculum/boards'))['boards'] as List<dynamic>;

  Future<List<int>> getGrades(String board) async {
    final g = (await _getJson('/v3/curriculum/$board/grades'))['grades']
        as List<dynamic>;
    return g.map((e) => e as int).toList();
  }

  /// Chapters for a board+grade, already numerically sequenced by the server.
  Future<Map<String, dynamic>> getChapters(String board, int grade) =>
      _getJson('/v3/curriculum/$board/grade/$grade/chapters');

  Future<Map<String, dynamic>> getChapterQuestions(
          String board, int grade, String chapter) =>
      _getJson(
          '/v3/curriculum/$board/grade/$grade/chapter/${Uri.encodeComponent(chapter)}/questions');

  // ------------------------------------------------------------- settings
  /// The user's app-scoping settings: chosen level (L1-L8), grade, curriculum,
  /// and `onboarded` (true once a level is picked).
  Future<Map<String, dynamic>> getSettings(String userId) {
    final uri = Uri.parse('$_base/v3/me/settings')
        .replace(queryParameters: {'user_id': userId});
    return http.get(uri).timeout(const Duration(seconds: 15)).then((res) {
      if (res.statusCode != 200) {
        throw ApiException('me/settings failed: ${res.statusCode}');
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    });
  }

  /// Persist the chosen level / grade (onboarding + the in-app level switcher).
  Future<void> setSettings(String userId,
      {String? selectedLevel, int? grade, String? curriculum}) async {
    final body = <String, dynamic>{'user_id': userId};
    if (selectedLevel != null) body['selected_level'] = selectedLevel;
    if (grade != null) body['grade'] = grade;
    if (curriculum != null) body['curriculum'] = curriculum;
    final res = await http
        .post(Uri.parse('$_base/v3/me/settings'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body))
        .timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      throw ApiException('set settings failed: ${res.statusCode} ${res.body}');
    }
  }

  // ------------------------------------------------------- unified economy
  /// Grade an answer server-side. Drives the ONE economy (coins/gems/XP/
  /// streak/awards) AND mastery, and returns the updated [wallet] so the
  /// caller can refresh every tab from a single response.
  Future<Map<String, dynamic>> checkAnswer({
    required String userId,
    required String questionId,
    int? selectedIndex,
    Object? selectedValue,
    int hintsUsed = 0,
    int timeTakenMs = 0,
  }) async {
    final body = <String, dynamic>{
      'user_id': userId,
      'question_id': questionId,
      'hints_used': hintsUsed,
      'time_taken_ms': timeTakenMs,
    };
    if (selectedIndex != null) body['selected_index'] = selectedIndex;
    if (selectedValue != null) body['selected_value'] = selectedValue;
    final res = await http
        .post(
          Uri.parse('$_base/v3/answer/check'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      throw ApiException('answer/check failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Single source of truth for the wallet — read by the Olympiad header,
  /// Progress, and Profile so the numbers never diverge.
  Future<Map<String, dynamic>> getWallet(String userId) {
    final uri = Uri.parse('$_base/v3/me/wallet')
        .replace(queryParameters: {'user_id': userId});
    return http.get(uri).timeout(const Duration(seconds: 15)).then((res) {
      if (res.statusCode != 200) {
        throw ApiException('me/wallet failed: ${res.statusCode}');
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    });
  }

  /// Academic height + strand mastery, derived from the same state as the
  /// wallet (and now fed by /v3 answer-check), so performance never disagrees.
  Future<Map<String, dynamic>> getProgress(String userId, {String? level}) {
    final uri = Uri.parse('$_base/v3/me/progress').replace(queryParameters: {
      'user_id': userId,
      if (level != null) 'level': level,
    });
    return http.get(uri).timeout(const Duration(seconds: 15)).then((res) {
      if (res.statusCode != 200) {
        throw ApiException('me/progress failed: ${res.statusCode}');
      }
      return jsonDecode(res.body) as Map<String, dynamic>;
    });
  }
}
