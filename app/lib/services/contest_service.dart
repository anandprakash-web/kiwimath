import 'dart:convert';

import 'authed_http.dart' as http;
import 'api_client.dart' show ApiClient, ApiException;

/// Client for the v3 Daily Contest + Weekly League API.
///
/// Mirrors [LevelService]: authed HTTP (Bearer + X-Idempotency-Key injected by
/// authed_http), `ApiClient.baseUrl` for host resolution. The contest is the
/// flagship daily event; the league is the weekly cohort race. Both feed the
/// one economy (coins/gems/xp come back through /v3/answer/check as usual).
class ContestService {
  String get _base => ApiClient.baseUrl;

  Future<Map<String, dynamic>> _getJson(String path) async {
    final res =
        await http.get(Uri.parse('$_base$path')).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      throw ApiException('GET $path failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Today's contest for the student's level: status (upcoming/live/closed),
  /// the question set (answers NOT included) when live, and the attempt state.
  Future<Map<String, dynamic>> getContestToday(String userId, String level) =>
      _getJson('/v3/contest/today?user_id=$userId&level=$level');

  /// Submit the contest. One attempt — a repeat returns the same result.
  /// [answers] = [{qid, selected_index?|selected_value?, time_ms?}].
  Future<Map<String, dynamic>> submitContest({
    required String userId,
    required String level,
    required List<Map<String, dynamic>> answers,
    String? name,
  }) async {
    final body = <String, dynamic>{
      'user_id': userId,
      'level': level,
      'answers': answers,
    };
    if (name != null) body['name'] = name;
    final res = await http
        .post(
          Uri.parse('$_base/v3/contest/submit'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) {
      throw ApiException('contest/submit failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Today's contest leaderboard for a level.
  Future<Map<String, dynamic>> contestLeaderboard(String level) =>
      _getJson('/v3/contest/leaderboard?level=$level');

  /// The student's weekly league cohort standings (rank + promotion/relegation
  /// zones + week end).
  Future<Map<String, dynamic>> leagueMe(String userId, String level) =>
      _getJson('/v3/league/me?user_id=$userId&level=$level');
}
