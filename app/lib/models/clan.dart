/// Kiwimath Clan data models — v1.0
///
/// Covers: Clan, ClanLevel, ClanCrest, ChallengeInfo, ChallengeProgress,
/// GuessEntry, LeaderboardEntry, DailySquadMember.

class ClanCrest {
  final String shape;
  final String color;
  const ClanCrest({required this.shape, required this.color});

  factory ClanCrest.fromJson(Map<String, dynamic> json) => ClanCrest(
        shape: json['shape'] as String? ?? 'bolt',
        color: json['color'] as String? ?? '#FF6D00',
      );
  Map<String, dynamic> toJson() => {'shape': shape, 'color': color};

  /// Emoji representation of the crest shape.
  String get emoji => const {
        'bolt': '⚡',
        'lion': '\U0001F981',
        'wave': '\U0001F30A',
        'rocket': '\U0001F680',
        'blossom': '\U0001F338',
        'dolphin': '\U0001F42C',
      }[shape] ??
      '⚡';
}

class ClanLevel {
  final int level;
  final String name;
  final String emoji;
  final int currentXp;
  final double progress;
  final int xpToNext;

  const ClanLevel({
    required this.level,
    required this.name,
    required this.emoji,
    required this.currentXp,
    required this.progress,
    required this.xpToNext,
  });

  factory ClanLevel.fromJson(Map<String, dynamic> json) => ClanLevel(
        level: json['level'] as int? ?? 1,
        name: json['name'] as String? ?? 'Seedling',
        emoji: json['emoji'] as String? ?? '\U0001F331',
        currentXp: json['current_xp'] as int? ?? 0,
        progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
        xpToNext: json['xp_to_next'] as int? ?? 5000,
      );
}

class Clan {
  final String clanId;
  final String name;
  final int grade;
  final ClanCrest crest;
  final String leaderUid;
  final int memberCount;
  final String status;
  final int lifetimeBrainPoints;
  final int lifetimeBrawnPoints;
  final int lifetimeQuizPoints;
  final ClanLevel clanLevel;
  final String? inviteCode;
  final String? inviteExpiresAt;
  final List<String> memberUids;
  final String createdAt;

  const Clan({
    required this.clanId,
    required this.name,
    required this.grade,
    required this.crest,
    required this.leaderUid,
    required this.memberCount,
    required this.status,
    required this.lifetimeBrainPoints,
    required this.lifetimeBrawnPoints,
    required this.lifetimeQuizPoints,
    required this.clanLevel,
    this.inviteCode,
    this.inviteExpiresAt,
    this.memberUids = const [],
    this.createdAt = '',
  });

  factory Clan.fromJson(Map<String, dynamic> json) => Clan(
        clanId: json['clan_id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        grade: json['grade'] as int? ?? 1,
        crest: ClanCrest.fromJson(json['crest'] as Map<String, dynamic>? ?? {}),
        leaderUid: json['leader_uid'] as String? ?? '',
        memberCount: json['member_count'] as int? ?? 0,
        status: json['status'] as String? ?? 'active',
        lifetimeBrainPoints: json['lifetime_brain_points'] as int? ?? 0,
        lifetimeBrawnPoints: json['lifetime_brawn_points'] as int? ?? 0,
        lifetimeQuizPoints: json['lifetime_quiz_points'] as int? ?? 0,
        clanLevel: ClanLevel.fromJson(
            json['clan_level'] as Map<String, dynamic>? ?? {}),
        inviteCode: json['invite_code'] as String?,
        inviteExpiresAt: json['invite_expires_at'] as String?,
        memberUids: (json['member_uids'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        createdAt: json['created_at'] as String? ?? '',
      );

  bool get isLeader => leaderUid.isNotEmpty;
  int get totalPoints =>
      lifetimeBrainPoints + lifetimeBrawnPoints + lifetimeQuizPoints;
}

// ---------------------------------------------------------------------------
// Challenge
// ---------------------------------------------------------------------------

class ChallengeInfo {
  final String challengeId;
  final String title;
  final String puzzleType;
  final String difficultyTier;
  final int gridRows;
  final int gridCols;
  final int durationDays;
  final String startDate;
  final String endDate;
  final String status;
  final int daysRemaining;

  const ChallengeInfo({
    required this.challengeId,
    required this.title,
    required this.puzzleType,
    required this.difficultyTier,
    required this.gridRows,
    required this.gridCols,
    required this.durationDays,
    required this.startDate,
    required this.endDate,
    required this.status,
    required this.daysRemaining,
  });

  factory ChallengeInfo.fromJson(Map<String, dynamic> json) => ChallengeInfo(
        challengeId: json['challenge_id'] as String? ?? '',
        title: json['title'] as String? ?? '',
        puzzleType: json['puzzle_type'] as String? ?? 'pattern_sequence',
        difficultyTier: json['difficulty_tier'] as String? ?? 'explorer',
        gridRows: json['grid_rows'] as int? ?? 20,
        gridCols: json['grid_cols'] as int? ?? 15,
        durationDays: json['duration_days'] as int? ?? 7,
        startDate: json['start_date'] as String? ?? '',
        endDate: json['end_date'] as String? ?? '',
        status: json['status'] as String? ?? 'none',
        daysRemaining: json['days_remaining'] as int? ?? 0,
      );

  int get totalBlocks => gridRows * gridCols;
}

class ChallengeProgress {
  final String clanId;
  final String challengeId;
  final int totalClanPoints;
  final int brainPoints;
  final int quizPoints;
  final int brawnPoints;
  final int blocksRevealed;
  final int totalBlocks;
  final double revealPercentage;
  final bool canSubmit;
  final String? currentAnswer;
  final int? answerDay;
  final int answerPointsToday;
  final List<int> blockOrder;

  const ChallengeProgress({
    required this.clanId,
    required this.challengeId,
    required this.totalClanPoints,
    required this.brainPoints,
    required this.quizPoints,
    required this.brawnPoints,
    required this.blocksRevealed,
    required this.totalBlocks,
    required this.revealPercentage,
    required this.canSubmit,
    this.currentAnswer,
    this.answerDay,
    required this.answerPointsToday,
    required this.blockOrder,
  });

  factory ChallengeProgress.fromJson(Map<String, dynamic> json) =>
      ChallengeProgress(
        clanId: json['clan_id'] as String? ?? '',
        challengeId: json['challenge_id'] as String? ?? '',
        totalClanPoints: json['total_clan_points'] as int? ?? 0,
        brainPoints: json['brain_points'] as int? ?? 0,
        quizPoints: json['quiz_points'] as int? ?? 0,
        brawnPoints: json['brawn_points'] as int? ?? 0,
        blocksRevealed: json['blocks_revealed'] as int? ?? 0,
        totalBlocks: json['total_blocks'] as int? ?? 300,
        revealPercentage:
            (json['reveal_percentage'] as num?)?.toDouble() ?? 0.0,
        canSubmit: json['can_submit'] as bool? ?? false,
        currentAnswer: json['current_answer'] as String?,
        answerDay: json['answer_day'] as int?,
        answerPointsToday: json['answer_points_today'] as int? ?? 0,
        blockOrder: (json['block_order'] as List<dynamic>?)
                ?.map((e) => e as int)
                .toList() ??
            [],
      );
}

// ---------------------------------------------------------------------------
// Guess Board
// ---------------------------------------------------------------------------

class GuessEntry {
  final String uid;
  final String initial;
  final String guessText;
  final int dayNumber;
  final String submittedAt;

  const GuessEntry({
    required this.uid,
    required this.initial,
    required this.guessText,
    required this.dayNumber,
    required this.submittedAt,
  });

  factory GuessEntry.fromJson(Map<String, dynamic> json) => GuessEntry(
        uid: json['uid'] as String? ?? '',
        initial: json['initial'] as String? ?? '?',
        guessText: json['guess_text'] as String? ?? '',
        dayNumber: json['day_number'] as int? ?? 1,
        submittedAt: json['submitted_at'] as String? ?? '',
      );
}

// ---------------------------------------------------------------------------
// Leaderboard
// ---------------------------------------------------------------------------

class LeaderboardEntry {
  final int rank;
  final String clanId;
  final String name;
  final ClanCrest crest;
  final int memberCount;
  final ClanLevel clanLevel;
  final int totalPoints;

  const LeaderboardEntry({
    required this.rank,
    required this.clanId,
    required this.name,
    required this.crest,
    required this.memberCount,
    required this.clanLevel,
    required this.totalPoints,
  });

  factory LeaderboardEntry.fromJson(Map<String, dynamic> json) =>
      LeaderboardEntry(
        rank: json['rank'] as int? ?? 0,
        clanId: json['clan_id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        crest: ClanCrest.fromJson(json['crest'] as Map<String, dynamic>? ?? {}),
        memberCount: json['member_count'] as int? ?? 0,
        clanLevel: ClanLevel.fromJson(
            json['clan_level'] as Map<String, dynamic>? ?? {}),
        totalPoints: json['total_points'] as int? ?? 0,
      );
}

// ---------------------------------------------------------------------------
// Daily Squad (for the activity bar)
// ---------------------------------------------------------------------------

class DailySquadMember {
  final String uid;
  final String initial;
  final String color;
  final bool practicedToday;
  final int sessionsToday;
  final int scoreToday;

  const DailySquadMember({
    required this.uid,
    required this.initial,
    required this.color,
    required this.practicedToday,
    this.sessionsToday = 0,
    this.scoreToday = 0,
  });
}
