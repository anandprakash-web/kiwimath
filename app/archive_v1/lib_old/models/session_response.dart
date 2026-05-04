/// Models for the session API responses.
/// Source of truth: backend/app/api/session.py
///
/// POST /session/start  → SessionResponse (first question)
/// POST /session/answer  → SessionResponse (feedback + next question)
/// GET  /session/concepts → List<ConceptInfo>

class SessionVisual {
  final String kind;
  final String? svg;
  final String? altText;

  SessionVisual({required this.kind, this.svg, this.altText});

  factory SessionVisual.fromJson(Map<String, dynamic> json) => SessionVisual(
        kind: json['kind'] as String,
        svg: json['svg'] as String?,
        altText: json['alt_text'] as String?,
      );
}

class SessionOption {
  final String text;
  final bool isCorrect;

  SessionOption({required this.text, this.isCorrect = false});

  factory SessionOption.fromJson(Map<String, dynamic> json) => SessionOption(
        text: json['text'] as String,
        isCorrect: json['is_correct'] as bool? ?? false,
      );
}

class SessionQuestion {
  final String questionId;
  final String stem;
  final List<SessionOption> options;
  final int correctIndex;
  final SessionVisual? visual;
  final Map<String, dynamic> paramsUsed;

  SessionQuestion({
    required this.questionId,
    required this.stem,
    required this.options,
    required this.correctIndex,
    this.visual,
    required this.paramsUsed,
  });

  factory SessionQuestion.fromJson(Map<String, dynamic> json) {
    final optionsJson = json['options'] as List<dynamic>;
    return SessionQuestion(
      questionId: json['question_id'] as String,
      stem: json['stem'] as String,
      options: optionsJson
          .map((o) => SessionOption.fromJson(o as Map<String, dynamic>))
          .toList(),
      correctIndex: json['correct_index'] as int,
      visual: json['visual'] == null
          ? null
          : SessionVisual.fromJson(json['visual'] as Map<String, dynamic>),
      paramsUsed:
          Map<String, dynamic>.from((json['params_used'] ?? {}) as Map),
    );
  }
}

class SessionResponse {
  final String sessionId;
  final SessionQuestion? question;
  final String? feedbackMessage;
  final String? misconceptionDiagnosis;
  final String mascotEmotion;
  final bool isStepDown;
  final bool sessionComplete;
  final bool conceptMastered;
  final String? suggestNextConcept;
  final Map<String, dynamic>? masterySnapshot;
  final Map<String, dynamic>? sessionStats;

  /// Multi-level scaffolding — when true, re-present the same question with a hint.
  final bool retrySameQuestion;

  /// Scaffold level: 0=none, 1=text hint, 2=visual/misconception hint, 3=step-down.
  final int scaffoldLevel;

  /// Gamification — populated when session completes.
  final Map<String, dynamic>? rewards;
  final Map<String, dynamic>? userProfile;

  SessionResponse({
    required this.sessionId,
    this.question,
    this.feedbackMessage,
    this.misconceptionDiagnosis,
    this.mascotEmotion = 'neutral',
    this.isStepDown = false,
    this.sessionComplete = false,
    this.conceptMastered = false,
    this.suggestNextConcept,
    this.masterySnapshot,
    this.sessionStats,
    this.retrySameQuestion = false,
    this.scaffoldLevel = 0,
    this.rewards,
    this.userProfile,
  });

  factory SessionResponse.fromJson(Map<String, dynamic> json) {
    return SessionResponse(
      sessionId: json['session_id'] as String,
      question: json['question'] == null
          ? null
          : SessionQuestion.fromJson(
              json['question'] as Map<String, dynamic>),
      feedbackMessage: json['feedback_message'] as String?,
      misconceptionDiagnosis: json['misconception_diagnosis'] as String?,
      mascotEmotion: (json['mascot_emotion'] as String?) ?? 'neutral',
      isStepDown: json['is_step_down'] as bool? ?? false,
      sessionComplete: json['session_complete'] as bool? ?? false,
      conceptMastered: json['concept_mastered'] as bool? ?? false,
      suggestNextConcept: json['suggest_next_concept'] as String?,
      retrySameQuestion: json['retry_same_question'] as bool? ?? false,
      scaffoldLevel: json['scaffold_level'] as int? ?? 0,
      masterySnapshot: json['mastery_snapshot'] != null
          ? Map<String, dynamic>.from(json['mastery_snapshot'] as Map)
          : null,
      sessionStats: json['session_stats'] != null
          ? Map<String, dynamic>.from(json['session_stats'] as Map)
          : null,
      rewards: json['rewards'] != null
          ? Map<String, dynamic>.from(json['rewards'] as Map)
          : null,
      userProfile: json['user_profile'] != null
          ? Map<String, dynamic>.from(json['user_profile'] as Map)
          : null,
    );
  }
}

class ConceptInfo {
  final String conceptId;
  final String displayName;
  final String? description;
  final String? worldRegion;
  final String? topicBranch;
  final int questionCount;

  ConceptInfo({
    required this.conceptId,
    required this.displayName,
    this.description,
    this.worldRegion,
    this.topicBranch,
    required this.questionCount,
  });

  factory ConceptInfo.fromJson(Map<String, dynamic> json) => ConceptInfo(
        conceptId: json['concept_id'] as String,
        displayName: json['display_name'] as String,
        description: json['description'] as String?,
        worldRegion: json['world_region'] as String?,
        topicBranch: json['topic_branch'] as String?,
        questionCount: json['question_count'] as int? ?? 0,
      );
}
