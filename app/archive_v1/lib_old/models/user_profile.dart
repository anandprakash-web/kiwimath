/// User profile model — v2 Meritocratic Achievement Economy.
///
/// Dual currency: Kiwi Coins (effort) + Mastery Gems (skill).
/// Learner persona classification for identity-based motivation.
/// Loaded on app start, updated after each session completes.

class UserProfile {
  final String userId;
  final String displayName;
  final String avatar;
  final int streakCurrent;
  final int streakLongest;
  final int xpTotal;
  final int kiwiCoins;       // Effort currency — "A Kiwi Coin is always a Kiwi Coin"
  final int masteryGems;     // Skill currency — harder to earn
  final int dailyGoal;
  final int dailyProgress;
  final String? dailyDate;
  final String? onboardedAt;   // ISO timestamp — null means never onboarded
  final int? grade;            // Selected grade (1-6)
  final String? curriculum;    // Selected curriculum: ncert, icse, igcse, olympiad
  final String learnerPersona;  // steady_learner, power_learner, mastery_learner, comeback_learner
  final String? personaName;    // "The Guardian of the Streak" etc.
  final String? personaEmoji;
  final int topicsMastered;     // Topics at 70%+ accuracy

  const UserProfile({
    required this.userId,
    this.displayName = 'Kiwi Learner',
    this.avatar = 'kiwi_default',
    this.streakCurrent = 0,
    this.streakLongest = 0,
    this.xpTotal = 0,
    this.kiwiCoins = 0,
    this.masteryGems = 5,
    this.dailyGoal = 5,
    this.dailyProgress = 0,
    this.dailyDate,
    this.onboardedAt,
    this.grade,
    this.curriculum,
    this.learnerPersona = 'steady_learner',
    this.personaName,
    this.personaEmoji,
    this.topicsMastered = 0,
  });

  /// Whether this user has completed onboarding (benchmark test).
  bool get hasOnboarded => onboardedAt != null;

  /// Backward-compatible factory: reads both old (gems) and new (kiwi_coins) fields.
  factory UserProfile.fromJson(Map<String, dynamic> json) {
    final personaInfo = json['persona_info'] as Map<String, dynamic>?;
    return UserProfile(
      userId: json['user_id'] as String? ?? '',
      displayName: json['display_name'] as String? ?? 'Kiwi Learner',
      avatar: json['avatar'] as String? ?? 'kiwi_default',
      streakCurrent: json['streak_current'] as int? ?? 0,
      streakLongest: json['streak_longest'] as int? ?? 0,
      xpTotal: json['xp_total'] as int? ?? 0,
      kiwiCoins: json['kiwi_coins'] as int? ?? 0,
      masteryGems: json['gems'] as int? ?? json['mastery_gems'] as int? ?? 5,
      dailyGoal: json['daily_goal'] as int? ?? 5,
      dailyProgress: json['daily_progress'] as int? ?? 0,
      dailyDate: json['daily_date'] as String?,
      onboardedAt: json['onboarded_at'] as String?,
      grade: json['grade'] as int?,
      curriculum: json['curriculum'] as String?,
      learnerPersona: json['learner_persona'] as String? ?? 'steady_learner',
      personaName: personaInfo?['name'] as String? ?? json['persona_name'] as String?,
      personaEmoji: personaInfo?['emoji'] as String?,
      topicsMastered: json['topics_mastered'] as int? ?? 0,
    );
  }

  static const empty = UserProfile(userId: '');

  /// Whether this user follows a curriculum (NCERT/ICSE/IGCSE) vs Olympiad.
  bool get hasCurriculum =>
      curriculum != null &&
      curriculum!.isNotEmpty &&
      curriculum != 'olympiad';

  UserProfile copyWith({
    int? streakCurrent,
    int? xpTotal,
    int? kiwiCoins,
    int? masteryGems,
    int? dailyProgress,
    String? learnerPersona,
    int? topicsMastered,
    String? curriculum,
  }) {
    return UserProfile(
      userId: userId,
      displayName: displayName,
      avatar: avatar,
      streakCurrent: streakCurrent ?? this.streakCurrent,
      streakLongest: streakLongest,
      xpTotal: xpTotal ?? this.xpTotal,
      kiwiCoins: kiwiCoins ?? this.kiwiCoins,
      masteryGems: masteryGems ?? this.masteryGems,
      dailyGoal: dailyGoal,
      dailyProgress: dailyProgress ?? this.dailyProgress,
      dailyDate: dailyDate,
      onboardedAt: onboardedAt,
      grade: grade,
      curriculum: curriculum ?? this.curriculum,
      learnerPersona: learnerPersona ?? this.learnerPersona,
      personaName: personaName,
      personaEmoji: personaEmoji,
      topicsMastered: topicsMastered ?? this.topicsMastered,
    );
  }
}

/// Mastery state for a single concept.
class ConceptMastery {
  final String conceptId;
  final double internalScore;
  final int shownScore;
  final String masteryLabel;
  final int totalAttempts;
  final int streakCurrent;
  final String? lastPractised;

  const ConceptMastery({
    required this.conceptId,
    this.internalScore = 0.0,
    this.shownScore = 0,
    this.masteryLabel = 'new',
    this.totalAttempts = 0,
    this.streakCurrent = 0,
    this.lastPractised,
  });

  factory ConceptMastery.fromJson(Map<String, dynamic> json) => ConceptMastery(
        conceptId: json['concept_id'] as String? ?? '',
        internalScore: (json['internal_score'] as num?)?.toDouble() ?? 0.0,
        shownScore: json['shown_score'] as int? ?? 0,
        masteryLabel: json['mastery_label'] as String? ?? 'new',
        totalAttempts: json['total_attempts'] as int? ?? 0,
        streakCurrent: json['streak_current'] as int? ?? 0,
        lastPractised: json['last_practised'] as String?,
      );

  double get progress => shownScore / 100.0;
}

/// Rewards earned from a session — v2 with Hero's Formula breakdown.
class SessionRewards {
  final int xpEarned;
  final int coinsEarned;
  final int gemsEarned;
  final int? comebackBonus;
  final int? improvementBonus;
  final String? persona;

  const SessionRewards({
    this.xpEarned = 0,
    this.coinsEarned = 0,
    this.gemsEarned = 0,
    this.comebackBonus,
    this.improvementBonus,
    this.persona,
  });

  factory SessionRewards.fromJson(Map<String, dynamic> json) {
    // Parse session_coins breakdown if present
    final sessionCoins = json['session_coins'] as Map<String, dynamic>?;
    final breakdown = sessionCoins?['breakdown'] as Map<String, dynamic>?;

    return SessionRewards(
      xpEarned: json['xp_earned'] as int? ?? 0,
      coinsEarned: sessionCoins?['coins_earned'] as int? ?? json['coins_earned'] as int? ?? 0,
      gemsEarned: (json['session_gems'] as Map<String, dynamic>?)?['gems_earned'] as int?
          ?? json['gems_earned'] as int? ?? 0,
      comebackBonus: breakdown?['comeback_bonus'] as int?,
      improvementBonus: breakdown?['improvement_bonus'] as int?,
      persona: json['persona'] as String?,
    );
  }

  bool get hasComeback => comebackBonus != null && comebackBonus! > 0;
  bool get hasImprovement => improvementBonus != null && improvementBonus! > 0;
}
