import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/engagement.dart';
import 'api_client.dart';

/// Flutter API client for the Kiwimath Engagement system (v4 endpoints).
///
/// Uses [ApiClient.baseUrl] for URL resolution and mirrors the retry /
/// error-handling patterns from [ApiClient].
class EngagementService {
  EngagementService._();
  static final EngagementService instance = EngagementService._();

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
  // 1. GET /v4/daily-puzzle  --  Get today's puzzle
  // ---------------------------------------------------------------------------

  /// Fetch the daily puzzle for a grade. Optionally pass a [date] (YYYY-MM-DD).
  /// Returns `null` when no puzzle is available.
  Future<DailyPuzzle?> getDailyPuzzle({
    required int grade,
    String? date,
  }) async {
    final params = <String, String>{
      'grade': grade.toString(),
    };
    if (date != null) params['date'] = date;
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/daily-puzzle')
        .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/daily-puzzle failed: ${res.statusCode} ${res.body}');
    }
    return DailyPuzzle.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 2. POST /v4/daily-puzzle/submit  --  Submit puzzle answer
  // ---------------------------------------------------------------------------

  /// Submit an answer for the daily puzzle.
  Future<PuzzleSubmissionResult> submitPuzzleAnswer({
    required String uid,
    required String puzzleId,
    required String answer,
    required int timeTakenSeconds,
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/daily-puzzle/submit');
    final body = {
      'uid': uid,
      'puzzle_id': puzzleId,
      'answer': answer,
      'time_taken_seconds': timeTakenSeconds,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/daily-puzzle/submit failed: ${res.statusCode} ${res.body}');
    }
    return PuzzleSubmissionResult.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 3. GET /v4/daily-puzzle/leaderboard  --  Daily leaderboard
  // ---------------------------------------------------------------------------

  /// Fetch the daily puzzle leaderboard for a grade.
  Future<List<Map<String, dynamic>>> getDailyLeaderboard({
    required int grade,
    String period = 'daily',
  }) async {
    final params = <String, String>{
      'grade': grade.toString(),
      'period': period,
    };
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/daily-puzzle/leaderboard')
            .replace(queryParameters: params);
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/daily-puzzle/leaderboard failed: '
          '${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list.map((e) => e as Map<String, dynamic>).toList();
  }

  // ---------------------------------------------------------------------------
  // 4. GET /v4/streaks/{uid}  --  Get streak data
  // ---------------------------------------------------------------------------

  /// Fetch streak data for a user. Returns `null` if no streak data exists.
  Future<StreakData?> getStreak({required String uid}) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/streaks/$uid');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/streaks/$uid failed: ${res.statusCode} ${res.body}');
    }
    return StreakData.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 5. POST /v4/streaks/{uid}/freeze  --  Use streak freeze
  // ---------------------------------------------------------------------------

  /// Use a streak freeze for the user.
  Future<Map<String, dynamic>> useStreakFreeze({
    required String uid,
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/streaks/$uid/freeze');
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders)
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/streaks/$uid/freeze failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 6. GET /v4/leagues/status  --  Get league status
  // ---------------------------------------------------------------------------

  /// Fetch the league status for a user. Returns `null` if not in any league.
  Future<LeagueStatus?> getLeagueStatus({required String uid}) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/leagues/status')
        .replace(queryParameters: {'uid': uid});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/leagues/status failed: ${res.statusCode} ${res.body}');
    }
    return LeagueStatus.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 7. GET /v4/clan-wars/current  --  Get current clan war
  // ---------------------------------------------------------------------------

  /// Fetch the current clan war for a clan. Returns `null` if no war is active.
  Future<ClanWar?> getCurrentWar({required String clanId}) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/clan-wars/current')
            .replace(queryParameters: {'clan_id': clanId});
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/clan-wars/current failed: ${res.statusCode} ${res.body}');
    }
    return ClanWar.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 8. POST /v4/clan-wars/{war_id}/submit  --  Submit war answer
  // ---------------------------------------------------------------------------

  /// Submit an answer for a clan war puzzle.
  Future<Map<String, dynamic>> submitWarAnswer({
    required String warId,
    required String uid,
    required String clanId,
    required String puzzleId,
    required String answer,
    required int timeTaken,
  }) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/clan-wars/$warId/submit');
    final body = {
      'uid': uid,
      'clan_id': clanId,
      'puzzle_id': puzzleId,
      'answer': answer,
      'time_taken': timeTaken,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/clan-wars/$warId/submit failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 9. GET /v4/rewards/{uid}  --  Get rewards data
  // ---------------------------------------------------------------------------

  /// Fetch rewards data for a user. Returns `null` if no rewards exist.
  Future<RewardData?> getRewards({required String uid}) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/rewards/$uid');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/rewards/$uid failed: ${res.statusCode} ${res.body}');
    }
    return RewardData.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 10. POST /v4/rewards/{uid}/open-mystery-box  --  Open mystery box
  // ---------------------------------------------------------------------------

  /// Open a mystery box for the user. Returns `null` if no boxes available.
  Future<MysteryBoxResult?> openMysteryBox({required String uid}) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/rewards/$uid/open-mystery-box');
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders)
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode == 404) return null;
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/rewards/$uid/open-mystery-box failed: '
          '${res.statusCode} ${res.body}');
    }
    return MysteryBoxResult.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 11. POST /v4/rewards/{uid}/claim-daily  --  Claim daily reward
  // ---------------------------------------------------------------------------

  /// Claim the daily reward for a user.
  Future<Map<String, dynamic>> claimDailyReward({
    required String uid,
  }) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/rewards/$uid/claim-daily');
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders)
        .timeout(const Duration(seconds: 10)));
    if (res.statusCode != 200) {
      throw ApiException(
          'POST /v4/rewards/$uid/claim-daily failed: '
          '${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ---------------------------------------------------------------------------
  // 12. POST /v4/pledges/{uid}  --  Create a pledge
  // ---------------------------------------------------------------------------

  /// Create a new puzzle pledge for a user.
  Future<Pledge?> createPledge({
    required String uid,
    required int targetPuzzles,
  }) async {
    final uri = Uri.parse('${ApiClient.baseUrl}/v4/pledges/$uid');
    final body = {
      'target_puzzles': targetPuzzles,
    };
    final res = await _withRetry(() => http
        .post(uri, headers: _jsonHeaders, body: jsonEncode(body))
        .timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200 && res.statusCode != 201) {
      throw ApiException(
          'POST /v4/pledges/$uid failed: ${res.statusCode} ${res.body}');
    }
    return Pledge.fromJson(
        jsonDecode(res.body) as Map<String, dynamic>);
  }

  // ---------------------------------------------------------------------------
  // 13. GET /v4/pledges/clan/{clan_id}  --  Get clan pledges
  // ---------------------------------------------------------------------------

  /// Fetch all pledges for members of a clan.
  Future<List<Pledge>> getClanPledges({required String clanId}) async {
    final uri =
        Uri.parse('${ApiClient.baseUrl}/v4/pledges/clan/$clanId');
    final res = await _withRetry(
        () => http.get(uri).timeout(const Duration(seconds: 15)));
    if (res.statusCode != 200) {
      throw ApiException(
          'GET /v4/pledges/clan/$clanId failed: '
          '${res.statusCode} ${res.body}');
    }
    final list = jsonDecode(res.body) as List<dynamic>;
    return list
        .map((e) => Pledge.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
