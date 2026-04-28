/// Data models for the v2 API endpoints.
/// Source of truth: backend v2 API.
///
/// GET  /v2/topics             → List<TopicV2>
/// GET  /v2/questions/next     → QuestionV2
/// GET  /v2/questions/{id}     → QuestionV2
/// POST /v2/answer/check       → AnswerCheckResponse
/// GET  /v2/questions/{id}/visual → SVG content

/// Socratic 6-level hint ladder.
class HintLadder {
  final String level0; // Pause prompt
  final String level1; // Attention direction
  final String level2; // Thinking question
  final String level3; // Scaffolded step
  final String level4; // Guided reveal
  final String level5; // Teach + retry

  HintLadder({
    required this.level0,
    required this.level1,
    required this.level2,
    required this.level3,
    required this.level4,
    required this.level5,
  });

  factory HintLadder.fromJson(Map<String, dynamic> json) {
    return HintLadder(
      level0: json['level_0'] as String? ?? '',
      level1: json['level_1'] as String? ?? '',
      level2: json['level_2'] as String? ?? '',
      level3: json['level_3'] as String? ?? '',
      level4: json['level_4'] as String? ?? '',
      level5: json['level_5'] as String? ?? '',
    );
  }

  /// Get hint text for a given level (0-5).
  String forLevel(int level) {
    switch (level) {
      case 0: return level0;
      case 1: return level1;
      case 2: return level2;
      case 3: return level3;
      case 4: return level4;
      case 5: return level5;
      default: return level0;
    }
  }
}

class TopicV2 {
  final String topicId;
  final String topicName;
  final int totalQuestions;
  final Map<String, int> difficultyDistribution;

  TopicV2({
    required this.topicId,
    required this.topicName,
    required this.totalQuestions,
    required this.difficultyDistribution,
  });

  factory TopicV2.fromJson(Map<String, dynamic> json) {
    final distJson = (json['difficulty_distribution'] ?? {}) as Map<String, dynamic>;
    return TopicV2(
      topicId: json['topic_id'] as String,
      topicName: json['topic_name'] as String,
      totalQuestions: json['total_questions'] as int? ?? 0,
      difficultyDistribution:
          distJson.map((k, v) => MapEntry(k, (v as num).toInt())),
    );
  }
}

class QuestionV2 {
  final String questionId;
  final String stem;
  final List<String> choices;
  final int difficultyScore;
  final String difficultyTier;
  final String? visualSvgUrl;
  final String? visualAlt;
  final String topic;
  final String topicName;
  final List<String> tags;
  final int correctAnswer;
  final String? hint;
  final HintLadder? hintLadder;

  QuestionV2({
    required this.questionId,
    required this.stem,
    required this.choices,
    required this.difficultyScore,
    required this.difficultyTier,
    this.visualSvgUrl,
    this.visualAlt,
    required this.topic,
    required this.topicName,
    required this.tags,
    required this.correctAnswer,
    this.hint,
    this.hintLadder,
  });

  factory QuestionV2.fromJson(Map<String, dynamic> json) {
    final choicesJson = json['choices'] as List<dynamic>;
    final tagsJson = (json['tags'] as List<dynamic>?) ?? [];
    final ladderJson = json['hint_ladder'] as Map<String, dynamic>?;
    return QuestionV2(
      questionId: json['question_id'] as String,
      stem: json['stem'] as String,
      choices: choicesJson.map((e) => e as String).toList(),
      difficultyScore: json['difficulty_score'] as int? ?? 0,
      difficultyTier: json['difficulty_tier'] as String? ?? 'easy',
      visualSvgUrl: json['visual_svg'] as String?,
      visualAlt: json['visual_alt'] as String?,
      topic: json['topic'] as String,
      topicName: json['topic_name'] as String,
      tags: tagsJson.map((e) => e as String).toList(),
      correctAnswer: json['correct_answer'] as int,
      hint: json['hint'] as String?,
      hintLadder: ladderJson != null ? HintLadder.fromJson(ladderJson) : null,
    );
  }
}

class AnswerCheckResponse {
  final bool correct;
  final int correctAnswer;
  final String feedback;
  final int difficultyScore;
  final int nextDifficulty;
  // ELO/IRT adaptive fields
  final double pExpected;     // model's predicted P(correct)
  final int abilityScore;     // student's current ability (1-100)
  final int streak;           // current streak (+correct, -wrong)
  final String confidence;    // low/medium/high
  final double accuracy;      // overall accuracy %
  // Behavioral matrix fields (PoP model)
  final String behavioralState;    // mastery/guessing/struggle_win/frustrated
  final double rewardMultiplier;   // XP multiplier based on behavioral state
  final double pAbandon;           // probability of quitting (0-1)
  final String intervention;       // none/visual_scaffold/cooldown/airdrop/boss_battle
  final String latencyClass;       // fast/slow/unknown
  // Gamification event fields
  final int xpEarned;
  final int coinsEarned;
  final int gemsEarned;
  final Map<String, dynamic>? levelUp;
  final String? microCelebration;
  final List<Map<String, dynamic>> badgeUnlocks;
  final List<Map<String, dynamic>> titleUnlocks;
  // Kiwi Brain engine fields
  final String childState;              // flowing/struggling/guessing/fatigued/confident/bored/new_user
  final Map<String, dynamic>? nextAction; // {action, message} from next action engine
  final Map<String, dynamic>? rewardBreakdown; // per-question coin breakdown

  AnswerCheckResponse({
    required this.correct,
    required this.correctAnswer,
    required this.feedback,
    required this.difficultyScore,
    required this.nextDifficulty,
    this.pExpected = 0.5,
    this.abilityScore = 50,
    this.streak = 0,
    this.confidence = 'low',
    this.accuracy = 0.0,
    this.behavioralState = '',
    this.rewardMultiplier = 1.0,
    this.pAbandon = 0.0,
    this.intervention = 'none',
    this.latencyClass = 'normal',
    this.xpEarned = 0,
    this.coinsEarned = 0,
    this.gemsEarned = 0,
    this.levelUp,
    this.microCelebration,
    this.badgeUnlocks = const [],
    this.titleUnlocks = const [],
    this.childState = '',
    this.nextAction,
    this.rewardBreakdown,
  });

  factory AnswerCheckResponse.fromJson(Map<String, dynamic> json) {
    return AnswerCheckResponse(
      correct: json['correct'] as bool,
      correctAnswer: json['correct_answer'] as int,
      feedback: json['feedback'] as String? ?? '',
      difficultyScore: json['difficulty_score'] as int? ?? 0,
      nextDifficulty: json['next_difficulty'] as int? ?? 0,
      pExpected: (json['p_expected'] as num?)?.toDouble() ?? 0.5,
      abilityScore: json['ability_score'] as int? ?? 50,
      streak: json['streak'] as int? ?? 0,
      confidence: json['confidence'] as String? ?? 'low',
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0.0,
      behavioralState: json['behavioral_state'] as String? ?? '',
      rewardMultiplier: (json['reward_multiplier'] as num?)?.toDouble() ?? 1.0,
      pAbandon: (json['p_abandon'] as num?)?.toDouble() ?? 0.0,
      intervention: json['intervention'] as String? ?? 'none',
      latencyClass: json['latency_class'] as String? ?? 'normal',
      xpEarned: json['xp_earned'] as int? ?? 0,
      coinsEarned: json['coins_earned'] as int? ?? 0,
      gemsEarned: json['gems_earned'] as int? ?? 0,
      levelUp: json['level_up'] as Map<String, dynamic>?,
      microCelebration: json['micro_celebration'] as String?,
      badgeUnlocks: (json['badge_unlocks'] as List<dynamic>?)
              ?.map((e) => Map<String, dynamic>.from(e as Map))
              .toList() ??
          const [],
      titleUnlocks: (json['title_unlocks'] as List<dynamic>?)
              ?.map((e) => Map<String, dynamic>.from(e as Map))
              .toList() ??
          const [],
      childState: json['child_state'] as String? ?? '',
      nextAction: json['next_action'] as Map<String, dynamic>?,
      rewardBreakdown: json['reward_breakdown'] as Map<String, dynamic>?,
    );
  }
}
