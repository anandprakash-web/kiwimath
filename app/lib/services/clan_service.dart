import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/clan.dart';
import 'api_client.dart';

/// Flutter API client for the Kiwimath Clan system (v4 endpoints).
///
/// Uses [ApiClient.baseUrl] for URL resolution and mirrors the retry /
/// error-handling patterns from [ApiClient].
class ClanService {
  ClanService._();
  static final ClanService instance = ClanService._();

  static const _jsonHeaders = {'Content-Type': 'application/json'};

  // ---------------------------------------------------------------------------
  // Retry helper (same semantics as ApiClient._withRetry)
  // ---------------------------------------------------------------------------

  /// Retries up to 2 times on timeout / 5xx with increasing delay.
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
    // Final fallback (should never reach here).
    return await request();
  }

  // ---------------------------------------------------------------------------
  // 1. POST /v4/clans  --  Create a clan
  // ---------------------------------------------------------------------------

  /// Create a new clan. Returns the newly created [Clan].
  Future<Clan> createClan({
    required String name,
    required int grade,
    required String leaderUid,
    required String parentUid,
    String crestShape = 'bolt',
    String crestColor = '#FF6D00',
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/clans');
    final body = {
      'name': name,
      'grade': grade,
      'leader_uid': leaderUid,
      'parent_uid': parentUid,
      'crest_shape': crestShape,
      'crest_color': crestColor,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200 && res.statusCode != 201) {
      throw ApiException(
          'POST /v4/clans failed: ${res.statusCode} ${res.body}');
    }
    return Clan.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 2. POST /v4/clans/join  --  Join a clan via invite code
  // ---------------------------------------------------------------------------

  /// Join an existing clan using an invite code. Returns the joined [Clan].
  Future<Clan> joinClan({
    required String inviteCode,
    required String userUid,
    required String parentUid,
    required int userGrade,
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/clans/join');
    final body = {
      'invite_code': inviteCode,
      'uid': userUid,
      'parent_uid': parentUid,
      'grade': userGrade,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/clans/join failed: ${res.statusCode} ${res.body}');
    }
    return Clan.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 3. DELETE /v4/clans/{clan_id}/members/{user_uid}  --  Remove / leave clan
  // ---------------------------------------------------------------------------

  /// Remove a member from a clan, or leave the clan.
  Future<void> removeMember({
    required String clanId,
    required String userUid,
    String? requesterUid,
  }) async {
    final uri = Uri.parse(
        '${ApiClient.baseUrl}/v4/clans/$clanId/members/$userUid')
        .replace(queryParameters: {'requester_uid': requesterUid ?? userUid});
    final res = await _withRetry(() => http
        .delete(uri, headers: _jsonHeaders)
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200 && res.statusCode != 204) {
      throw ApiException(
          'DELETE /v4/clans/$clanId/members/$userUid failed: '
          '${res.statusCode} ${res.body}');
    }
  }

  // ---------------------------------------------------------------------------
  // 4. POST /v4/clans/{clan_id}/invite  --  Regenerate invite code
  // ---------------------------------------------------------------------------

  /// Regenerate the invite code for a clan. Returns the new invite code and
  /// expiry as a raw map.
  Future<Map<String, dynamic>> regenerateInvite({
    required String clanId,
    required String requesterUid,
  }) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/clans/$clanId/invite')
            .replace(queryParameters: {'uid': requesterUid});
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders)
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/clans/$clanId/invite failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 5. GET /v4/clans/{clan_id}  --  Get clan details
  // ---------------------------------------------------------------------------

  /// Fetch full clan details. [userUid] is passed so the backend can annotate
  /// leader-specific fields (e.g. invite code visibility).
  Future<Clan> getClan({
    required String clanId,
    required String userUid,
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/clans/$clanId')
        .replace(queryParameters: {'user_uid': userUid});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/clans/$clanId failed: ${res.statusCode} ${res.body}');
    }
    return Clan.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 5b. GET /v4/clans/mine  --  Look up user's clan
  // ---------------------------------------------------------------------------

  /// Look up the user's clan. Returns null if user is not in any clan.
  Future<Clan?> getMyClan({required String userUid}) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/clans/mine')
        .replace(queryParameters: {'user_uid': userUid});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/clans/mine failed: ${res.statusCode} ${res.body}');
    }
    return Clan.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 6. GET /v4/leaderboard  --  Grade leaderboard
  // ---------------------------------------------------------------------------

  /// Fetch the clan leaderboard for a grade, optionally scoped to a challenge.
  Future<List<LeaderboardEntry>> getLeaderboard({
    required int grade,
    String? challengeId,
    int limit = 20,
  }) async {
    final params = <String, String>{
      'limit': limit.toString(),
    };
    if (challengeId != null) params['challenge_id'] = challengeId;
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/clans/leaderboard/$grade')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/leaderboard failed: ${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list
        .map((e) => LeaderboardEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---------------------------------------------------------------------------
  // 7. POST /v4/clans/{clan_id}/reactions  --  Send reaction
  // ---------------------------------------------------------------------------

  /// Send a reaction (e.g. cheer, high-five) within a clan.
  Future<Map<String, dynamic>> sendReaction({
    required String clanId,
    required String userUid,
    required String emoji,
  }) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/clans/$clanId/react');
    final body = {
      'uid': userUid,
      'emoji': emoji,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/clans/$clanId/reactions failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 8. GET /v4/challenges/active  --  Get active challenge
  // ---------------------------------------------------------------------------

  /// Fetch the currently active challenge for a grade.
  /// Returns `null` when no challenge is running.
  Future<ChallengeInfo?> getActiveChallenge({required int grade}) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/challenges/active')
        .replace(queryParameters: {'grade': grade.toString()});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/challenges/active failed: ${res.statusCode} ${res.body}');
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    // Backend may return {"status": "none"} when no active challenge exists.
    if (data['status'] == 'none') return null;
    return ChallengeInfo.fromJson(data);
  }

  // ---------------------------------------------------------------------------
  // 9. GET /v4/challenges/{challenge_id}/progress/{clan_id}
  // ---------------------------------------------------------------------------

  /// Get the progress of a clan in a specific challenge.
  Future<ChallengeProgress> getChallengeProgress({
    required String challengeId,
    required String clanId,
  }) async {
    final uri = Uri.parse(
        '${ApiClient.baseUrl}/v4/challenges/$challengeId/progress/$clanId');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/challenges/$challengeId/progress/$clanId failed: '
          '${res.statusCode} ${res.body}');
    }
    return ChallengeProgress.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 10. POST /v4/challenges/{challenge_id}/answer  --  Submit answer
  // ---------------------------------------------------------------------------

  /// Submit the clan leader's answer for a challenge.
  Future<Map<String, dynamic>> submitAnswer({
    required String challengeId,
    required String clanId,
    required String leaderUid,
    required String answerText,
  }) async {
    final uri = Uri.parse(
        '${ApiClient.baseUrl}/v4/challenges/$challengeId/answer');
    final body = {
      'clan_id': clanId,
      'uid': leaderUid,
      'answer': answerText,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/challenges/$challengeId/answer failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 11. GET /v4/challenges/{challenge_id}/guesses/{clan_id}
  // ---------------------------------------------------------------------------

  /// Fetch the guess board for a clan in a challenge.
  Future<List<GuessEntry>> getGuessBoard({
    required String challengeId,
    required String clanId,
  }) async {
    final uri = Uri.parse(
        '${ApiClient.baseUrl}/v4/challenges/$challengeId/guesses/$clanId');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/challenges/$challengeId/guesses/$clanId failed: '
          '${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list
        .map((e) => GuessEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ---------------------------------------------------------------------------
  // 12. POST /v4/challenges/{challenge_id}/guesses  --  Submit guess
  // ---------------------------------------------------------------------------

  /// Submit a guess from a clan member for a challenge.
  Future<Map<String, dynamic>> submitGuess({
    required String challengeId,
    required String clanId,
    required String userUid,
    required String guessText,
  }) async {
    final uri = Uri.parse(
        '${ApiClient.baseUrl}/v4/challenges/$challengeId/guess');
    final body = {
      'clan_id': clanId,
      'uid': userUid,
      'guess_text': guessText,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/challenges/$challengeId/guesses failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }
}
