/// Kiwimath Growth Journey data models — v1.0
///
/// Covers: GrowthJourney, GrowthLevel, GrowthEngagement, TopicGrowth,
/// GrowthMilestone.

// ---------------------------------------------------------------------------
// Growth Journey — aggregate view from /growth/journey
// ---------------------------------------------------------------------------

class GrowthJourney {
  final GrowthLevel current;
  final GrowthLevel? baseline;
  final int deltaLevels;
  final int deltaScale;
  final GrowthEngagement engagement;
  final int milestonesCount;
  final int daysSinceDiagnostic;
  final bool suggestedRetake;

  const GrowthJourney({
    required this.current,
    this.baseline,
    required this.deltaLevels,
    required this.deltaScale,
    required this.engagement,
    required this.milestonesCount,
    required this.daysSinceDiagnostic,
    required this.suggestedRetake,
  });

  factory GrowthJourney.fromJson(Map<String, dynamic> json) => GrowthJourney(
        current:
            GrowthLevel.fromJson(json['current'] as Map<String, dynamic>),
        baseline: json['baseline'] != null &&
                (json['baseline'] as Map<String, dynamic>).isNotEmpty
            ? GrowthLevel.fromJson(json['baseline'] as Map<String, dynamic>)
            : null,
        deltaLevels: json['delta_levels'] as int? ?? 0,
        deltaScale: json['delta_scale'] as int? ?? 0,
        engagement: GrowthEngagement.fromJson(
            json['engagement'] as Map<String, dynamic>? ?? {}),
        milestonesCount: json['milestones_count'] as int? ?? 0,
        daysSinceDiagnostic: json['days_since_diagnostic'] as int? ?? 0,
        suggestedRetake: json['suggested_retake'] as bool? ?? false,
      );
}

// ---------------------------------------------------------------------------
// Growth Level — single point-in-time proficiency snapshot
// ---------------------------------------------------------------------------

class GrowthLevel {
  final int level; // 1-6
  final String name; // Explorer, Builder, etc.
  final double theta;
  final int scaleScore;
  final String? takenAt;

  const GrowthLevel({
    required this.level,
    required this.name,
    required this.theta,
    required this.scaleScore,
    this.takenAt,
  });

  factory GrowthLevel.fromJson(Map<String, dynamic> json) => GrowthLevel(
        level: json['level'] as int? ?? 1,
        name: json['name'] as String? ?? 'Explorer',
        theta: (json['theta'] as num?)?.toDouble() ?? 0.0,
        scaleScore: json['scale_score'] as int? ?? 0,
        takenAt: json['taken_at'] as String?,
      );
}

// ---------------------------------------------------------------------------
// Growth Engagement — aggregated ecosystem stats
// ---------------------------------------------------------------------------

class GrowthEngagement {
  final int totalGems;
  final int totalXp;
  final int currentStreak;
  final int longestStreak;
  final int badgesEarned;
  final int stickersCollected;
  final double stickerAlbumPct;
  final int worksheetsCompleted;
  final int dailyPuzzlesSolved;
  final int clanWarsWon;
  final int practiceSessions;
  final int totalQuestionsAnswered;
  final int daysActive;

  const GrowthEngagement({
    required this.totalGems,
    required this.totalXp,
    required this.currentStreak,
    required this.longestStreak,
    required this.badgesEarned,
    required this.stickersCollected,
    required this.stickerAlbumPct,
    required this.worksheetsCompleted,
    required this.dailyPuzzlesSolved,
    required this.clanWarsWon,
    required this.practiceSessions,
    required this.totalQuestionsAnswered,
    required this.daysActive,
  });

  factory GrowthEngagement.fromJson(Map<String, dynamic> json) =>
      GrowthEngagement(
        totalGems: json['total_gems'] as int? ?? 0,
        totalXp: json['total_xp'] as int? ?? 0,
        currentStreak: json['current_streak'] as int? ?? 0,
        longestStreak: json['longest_streak'] as int? ?? 0,
        badgesEarned: json['badges_earned'] as int? ?? 0,
        stickersCollected: json['stickers_collected'] as int? ?? 0,
        stickerAlbumPct:
            (json['sticker_album_pct'] as num?)?.toDouble() ?? 0.0,
        worksheetsCompleted: json['worksheets_completed'] as int? ?? 0,
        dailyPuzzlesSolved: json['daily_puzzles_solved'] as int? ?? 0,
        clanWarsWon: json['clan_wars_won'] as int? ?? 0,
        practiceSessions: json['practice_sessions'] as int? ?? 0,
        totalQuestionsAnswered:
            json['total_questions_answered'] as int? ?? 0,
        daysActive: json['days_active'] as int? ?? 0,
      );
}

// ---------------------------------------------------------------------------
// Topic Growth — per-topic delta from baseline
// ---------------------------------------------------------------------------

class TopicGrowth {
  final String topicId;
  final String name;
  final int currentLevel;
  final double currentTheta;
  final int baselineLevel;
  final double baselineTheta;
  final double delta;
  final String trend; // up, down, flat
  final int questionsSince;
  final double accuracy;
  final bool isSuperpower;
  final bool needsLevelup;

  const TopicGrowth({
    required this.topicId,
    required this.name,
    required this.currentLevel,
    required this.currentTheta,
    required this.baselineLevel,
    required this.baselineTheta,
    required this.delta,
    required this.trend,
    required this.questionsSince,
    required this.accuracy,
    required this.isSuperpower,
    required this.needsLevelup,
  });

  factory TopicGrowth.fromJson(Map<String, dynamic> json) => TopicGrowth(
        topicId: json['topic_id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        currentLevel: json['current_level'] as int? ?? 1,
        currentTheta:
            (json['current_theta'] as num?)?.toDouble() ?? 0.0,
        baselineLevel: json['baseline_level'] as int? ?? 1,
        baselineTheta:
            (json['baseline_theta'] as num?)?.toDouble() ?? 0.0,
        delta: (json['delta'] as num?)?.toDouble() ?? 0.0,
        trend: json['trend'] as String? ?? 'flat',
        questionsSince: json['questions_since'] as int? ?? 0,
        accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0.0,
        isSuperpower: json['is_superpower'] as bool? ?? false,
        needsLevelup: json['needs_levelup'] as bool? ?? false,
      );
}

// ---------------------------------------------------------------------------
// Growth Milestone — timeline event
// ---------------------------------------------------------------------------

class GrowthMilestone {
  final String type; // diagnostic, level_up, topic_breakthrough, streak, gems, badge, worksheet, clan_war
  final String description;
  final String date;
  final String icon;
  final String? topicId;
  final int? fromLevel;
  final int? toLevel;
  final int? value;

  const GrowthMilestone({
    required this.type,
    required this.description,
    required this.date,
    required this.icon,
    this.topicId,
    this.fromLevel,
    this.toLevel,
    this.value,
  });

  factory GrowthMilestone.fromJson(Map<String, dynamic> json) =>
      GrowthMilestone(
        type: json['type'] as String? ?? '',
        description: json['description'] as String? ?? '',
        date: json['date'] as String? ?? '',
        icon: json['icon'] as String? ?? '',
        topicId: json['topic_id'] as String?,
        fromLevel: json['from_level'] as int?,
        toLevel: json['to_level'] as int?,
        value: json['value'] as int?,
      );
}
