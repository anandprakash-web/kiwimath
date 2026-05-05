/// Kiwimath Engagement data models — v1.0
///
/// Covers: DailyPuzzle, PuzzleSubmissionResult, StreakData, DayEntry,
/// LeagueStatus, ClanWar, WarMemberScore, RewardData, MysteryBoxResult, Pledge.

// ---------------------------------------------------------------------------
// Daily Puzzle
// ---------------------------------------------------------------------------

class DailyPuzzle {
  final String puzzleId;
  final String title;
  final String storyNarrative;
  final String puzzleType;
  final String questionText;
  final int grade;
  final int difficulty;
  final List<String> options;
  final String hint1;
  final String hint2;
  final String svgTemplate;
  final String gradeBandStyle;
  final String dropsAt;
  final String closesAt;
  final bool isActive;

  const DailyPuzzle({
    required this.puzzleId,
    required this.title,
    required this.storyNarrative,
    required this.puzzleType,
    required this.questionText,
    required this.grade,
    required this.difficulty,
    required this.options,
    required this.hint1,
    required this.hint2,
    required this.svgTemplate,
    required this.gradeBandStyle,
    required this.dropsAt,
    required this.closesAt,
    required this.isActive,
  });

  factory DailyPuzzle.fromJson(Map<String, dynamic> json) => DailyPuzzle(
        puzzleId: json['puzzle_id'] as String? ?? '',
        title: json['title'] as String? ?? '',
        storyNarrative: json['story_narrative'] as String? ?? '',
        puzzleType: json['puzzle_type'] as String? ?? '',
        questionText: json['question_text'] as String? ?? '',
        grade: json['grade'] as int? ?? 1,
        difficulty: json['difficulty'] as int? ?? 1,
        options: (json['options'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        hint1: json['hint1'] as String? ?? '',
        hint2: json['hint2'] as String? ?? '',
        svgTemplate: json['svg_template'] as String? ?? '',
        gradeBandStyle: json['grade_band_style'] as String? ?? '',
        dropsAt: json['drops_at'] as String? ?? '',
        closesAt: json['closes_at'] as String? ?? '',
        isActive: json['is_active'] as bool? ?? false,
      );
}

// ---------------------------------------------------------------------------
// Puzzle Submission Result
// ---------------------------------------------------------------------------

class PuzzleSubmissionResult {
  final bool correct;
  final int pointsEarned;
  final int streakCount;
  final int streakBonus;
  final int totalScore;
  final String streakTier;

  const PuzzleSubmissionResult({
    required this.correct,
    required this.pointsEarned,
    required this.streakCount,
    required this.streakBonus,
    required this.totalScore,
    required this.streakTier,
  });

  factory PuzzleSubmissionResult.fromJson(Map<String, dynamic> json) =>
      PuzzleSubmissionResult(
        correct: json['correct'] as bool? ?? false,
        pointsEarned: json['points_earned'] as int? ?? 0,
        streakCount: json['streak_count'] as int? ?? 0,
        streakBonus: json['streak_bonus'] as int? ?? 0,
        totalScore: json['total_score'] as int? ?? 0,
        streakTier: json['streak_tier'] as String? ?? '',
      );
}

// ---------------------------------------------------------------------------
// Streak Data
// ---------------------------------------------------------------------------

class DayEntry {
  final String date;
  final bool completed;
  final int points;

  const DayEntry({
    required this.date,
    required this.completed,
    required this.points,
  });

  factory DayEntry.fromJson(Map<String, dynamic> json) => DayEntry(
        date: json['date'] as String? ?? '',
        completed: json['completed'] as bool? ?? false,
        points: json['points'] as int? ?? 0,
      );
}

class StreakData {
  final int currentStreak;
  final int longestStreak;
  final bool streakFreezeAvailable;
  final String? lastPuzzleDate;
  final String? streakTier;
  final List<DayEntry> dailyCalendar;

  const StreakData({
    required this.currentStreak,
    required this.longestStreak,
    required this.streakFreezeAvailable,
    this.lastPuzzleDate,
    this.streakTier,
    required this.dailyCalendar,
  });

  factory StreakData.fromJson(Map<String, dynamic> json) => StreakData(
        currentStreak: json['current_streak'] as int? ?? 0,
        longestStreak: json['longest_streak'] as int? ?? 0,
        streakFreezeAvailable:
            json['streak_freeze_available'] as bool? ?? false,
        lastPuzzleDate: json['last_puzzle_date'] as String?,
        streakTier: json['streak_tier'] as String?,
        dailyCalendar: (json['daily_calendar'] as List<dynamic>?)
                ?.map((e) => DayEntry.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
      );
}

// ---------------------------------------------------------------------------
// League Status
// ---------------------------------------------------------------------------

class LeagueStatus {
  final String league;
  final int leaguePoints;
  final int rankInLeague;
  final int promotionThreshold;
  final int demotionThreshold;
  final int seasonNumber;
  final String seasonEndsAt;
  final int trophiesEarned;

  const LeagueStatus({
    required this.league,
    required this.leaguePoints,
    required this.rankInLeague,
    required this.promotionThreshold,
    required this.demotionThreshold,
    required this.seasonNumber,
    required this.seasonEndsAt,
    required this.trophiesEarned,
  });

  factory LeagueStatus.fromJson(Map<String, dynamic> json) => LeagueStatus(
        league: json['league'] as String? ?? 'bronze',
        leaguePoints: json['league_points'] as int? ?? 0,
        rankInLeague: json['rank_in_league'] as int? ?? 0,
        promotionThreshold: json['promotion_threshold'] as int? ?? 0,
        demotionThreshold: json['demotion_threshold'] as int? ?? 0,
        seasonNumber: json['season_number'] as int? ?? 1,
        seasonEndsAt: json['season_ends_at'] as String? ?? '',
        trophiesEarned: json['trophies_earned'] as int? ?? 0,
      );
}

// ---------------------------------------------------------------------------
// Clan War
// ---------------------------------------------------------------------------

class WarMemberScore {
  final String uid;
  final int score;
  final bool submitted;

  const WarMemberScore({
    required this.uid,
    required this.score,
    required this.submitted,
  });

  factory WarMemberScore.fromJson(Map<String, dynamic> json) =>
      WarMemberScore(
        uid: json['uid'] as String? ?? '',
        score: json['score'] as int? ?? 0,
        submitted: json['submitted'] as bool? ?? false,
      );
}

class ClanWar {
  final String warId;
  final String status;
  final Map<String, dynamic> opponentClan;
  final int ourScore;
  final int theirScore;
  final List<String> puzzleSet;
  final String startTime;
  final String endTime;
  final List<WarMemberScore> memberScores;
  final double comebackBoost;

  const ClanWar({
    required this.warId,
    required this.status,
    required this.opponentClan,
    required this.ourScore,
    required this.theirScore,
    required this.puzzleSet,
    required this.startTime,
    required this.endTime,
    required this.memberScores,
    required this.comebackBoost,
  });

  factory ClanWar.fromJson(Map<String, dynamic> json) => ClanWar(
        warId: json['war_id'] as String? ?? '',
        status: json['status'] as String? ?? 'upcoming',
        opponentClan:
            json['opponent_clan'] as Map<String, dynamic>? ?? {},
        ourScore: json['our_score'] as int? ?? 0,
        theirScore: json['their_score'] as int? ?? 0,
        puzzleSet: (json['puzzle_set'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        startTime: json['start_time'] as String? ?? '',
        endTime: json['end_time'] as String? ?? '',
        memberScores: (json['member_scores'] as List<dynamic>?)
                ?.map(
                    (e) => WarMemberScore.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        comebackBoost:
            (json['comeback_boost'] as num?)?.toDouble() ?? 0.0,
      );
}

// ---------------------------------------------------------------------------
// Rewards
// ---------------------------------------------------------------------------

class RewardData {
  final List<Map<String, dynamic>> stickersCollected;
  final double stickerAlbumProgress;
  final int mysteryBoxesAvailable;
  final List<Map<String, dynamic>> badges;
  final List<Map<String, dynamic>> dailyCalendar;
  final Map<String, dynamic>? pledge;
  final int totalGems;

  const RewardData({
    required this.stickersCollected,
    required this.stickerAlbumProgress,
    required this.mysteryBoxesAvailable,
    required this.badges,
    required this.dailyCalendar,
    this.pledge,
    required this.totalGems,
  });

  factory RewardData.fromJson(Map<String, dynamic> json) => RewardData(
        stickersCollected: (json['stickers_collected'] as List<dynamic>?)
                ?.map((e) => e as Map<String, dynamic>)
                .toList() ??
            [],
        stickerAlbumProgress:
            (json['sticker_album_progress'] as num?)?.toDouble() ?? 0.0,
        mysteryBoxesAvailable:
            json['mystery_boxes_available'] as int? ?? 0,
        badges: (json['badges'] as List<dynamic>?)
                ?.map((e) => e as Map<String, dynamic>)
                .toList() ??
            [],
        dailyCalendar: (json['daily_calendar'] as List<dynamic>?)
                ?.map((e) => e as Map<String, dynamic>)
                .toList() ??
            [],
        pledge: json['pledge'] as Map<String, dynamic>?,
        totalGems: json['total_gems'] as int? ?? 0,
      );
}

// ---------------------------------------------------------------------------
// Mystery Box Result
// ---------------------------------------------------------------------------

class MysteryBoxResult {
  final String rewardType;
  final String rarity;
  final Map<String, dynamic> rewardData;

  const MysteryBoxResult({
    required this.rewardType,
    required this.rarity,
    required this.rewardData,
  });

  factory MysteryBoxResult.fromJson(Map<String, dynamic> json) =>
      MysteryBoxResult(
        rewardType: json['reward_type'] as String? ?? '',
        rarity: json['rarity'] as String? ?? 'common',
        rewardData:
            json['reward_data'] as Map<String, dynamic>? ?? {},
      );
}

// ---------------------------------------------------------------------------
// Pledge
// ---------------------------------------------------------------------------

class Pledge {
  final String uid;
  final int targetPuzzles;
  final int currentPuzzles;
  final int durationDays;
  final bool active;
  final String createdAt;
  final double goalGradient;

  const Pledge({
    required this.uid,
    required this.targetPuzzles,
    required this.currentPuzzles,
    required this.durationDays,
    required this.active,
    required this.createdAt,
    required this.goalGradient,
  });

  factory Pledge.fromJson(Map<String, dynamic> json) => Pledge(
        uid: json['uid'] as String? ?? '',
        targetPuzzles: json['target_puzzles'] as int? ?? 0,
        currentPuzzles: json['current_puzzles'] as int? ?? 0,
        durationDays: json['duration_days'] as int? ?? 7,
        active: json['active'] as bool? ?? false,
        createdAt: json['created_at'] as String? ?? '',
        goalGradient:
            (json['goal_gradient'] as num?)?.toDouble() ?? 0.0,
      );
}
