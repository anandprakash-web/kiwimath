import 'dart:convert';

import 'authed_http.dart' as http;
import 'api_client.dart' show ApiClient, ApiException;

/// Client for the v3 adaptive Challenge — "The Climb" (a sequential mini-CAT).
///
/// Mirrors [ContestService]: authed HTTP (Bearer + idempotency injected by
/// authed_http), `ApiClient.baseUrl` for host resolution. Separate from the
/// skill-ladder Practice — it measures + stretches; it never touches the ladder.
class ChallengeService {
  String get _base => ApiClient.baseUrl;

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final res = await http
        .post(Uri.parse('$_base$path'),
            headers: {'Content-Type': 'application/json'}, body: jsonEncode(body))
        .timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) {
      throw ApiException('POST $path failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> _get(String path) async {
    final res =
        await http.get(Uri.parse('$_base$path')).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      throw ApiException('GET $path failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Start (or resume) a climb at [level]. Returns the first/pending question
  /// (no answer leaked).
  Future<Map<String, dynamic>> start(String userId, String level) =>
      _post('/v3/challenge/start', {'user_id': userId, 'level': level});

  /// Answer the current item; returns the next item, or `{done:true, result}`.
  Future<Map<String, dynamic>> answer({
    required String userId,
    required String sessionId,
    required String qid,
    int? selectedIndex,
    String? selectedValue,
    int timeMs = 0,
  }) {
    final body = <String, dynamic>{
      'user_id': userId,
      'session_id': sessionId,
      'qid': qid,
      'time_ms': timeMs,
    };
    if (selectedIndex != null) body['selected_index'] = selectedIndex;
    if (selectedValue != null) body['selected_value'] = selectedValue;
    return _post('/v3/challenge/answer', body);
  }

  /// Best rating + recent history for [level].
  Future<Map<String, dynamic>> me(String userId, String level) =>
      _get('/v3/challenge/me?user_id=$userId&level=$level');
}
