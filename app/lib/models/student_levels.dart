/// Student micro-level progression models.
///
/// Maps to GET /v2/student/levels response.
/// 10 levels per topic per grade, with status (locked/current/completed)
/// and 0-3 star ratings based on accuracy.

class LevelInfo {
  final int level;
  final String name;
  /// "locked" | "current" | "completed"
  final String status;
  final int difficultyMin;
  final int difficultyMax;
  final int questionsDone;
  final int questionsTotal;
  /// 0-3 stars based on accuracy
  final int stars;
  final double accuracy;

  LevelInfo({
    required this.level,
    required this.name,
    required this.status,
    required this.difficultyMin,
    required this.difficultyMax,
    this.questionsDone = 0,
    this.questionsTotal = 0,
    this.stars = 0,
    this.accuracy = 0.0,
  });

  factory LevelInfo.fromJson(Map<String, dynamic> json) {
    return LevelInfo(
      level: json['level'] as int,
      name: json['name'] as String,
      status: json['status'] as String,
      difficultyMin: json['difficulty_min'] as int,
      difficultyMax: json['difficulty_max'] as int,
      questionsDone: json['questions_done'] as int? ?? 0,
      questionsTotal: json['questions_total'] as int? ?? 0,
      stars: json['stars'] as int? ?? 0,
      accuracy: (json['accuracy'] as num?)?.toDouble() ?? 0.0,
    );
  }

  bool get isLocked => status == 'locked';
  bool get isCurrent => status == 'current';
  bool get isCompleted => status == 'completed';
}

class TopicLevels {
  final String topicId;
  final String topicName;
  final int grade;
  final int currentLevel;
  final List<LevelInfo> levels;
  final bool allMastered;
  final bool gradeUpgradeAvailable;

  TopicLevels({
    required this.topicId,
    required this.topicName,
    required this.grade,
    required this.currentLevel,
    required this.levels,
    this.allMastered = false,
    this.gradeUpgradeAvailable = false,
  });

  factory TopicLevels.fromJson(Map<String, dynamic> json) {
    return TopicLevels(
      topicId: json['topic_id'] as String,
      topicName: json['topic_name'] as String,
      grade: json['grade'] as int,
      currentLevel: json['current_level'] as int? ?? 1,
      levels: (json['levels'] as List<dynamic>)
          .map((e) => LevelInfo.fromJson(e as Map<String, dynamic>))
          .toList(),
      allMastered: json['all_mastered'] as bool? ?? false,
      gradeUpgradeAvailable: json['grade_upgrade_available'] as bool? ?? false,
    );
  }

  /// Current level name (e.g. "Explorer", "Trailblazer").
  String get currentLevelName {
    if (currentLevel >= 1 && currentLevel <= levels.length) {
      return levels[currentLevel - 1].name;
    }
    return 'Starter';
  }

  /// Fraction of levels completed (0.0 to 1.0).
  double get progressFraction {
    if (levels.isEmpty) return 0.0;
    final completed = levels.where((l) => l.isCompleted).length;
    return completed / levels.length;
  }
}

class StudentLevels {
  final String userId;
  final int grade;
  final List<TopicLevels> topics;
  final double overallLevel;

  StudentLevels({
    required this.userId,
    required this.grade,
    required this.topics,
    this.overallLevel = 0.0,
  });

  factory StudentLevels.fromJson(Map<String, dynamic> json) {
    return StudentLevels(
      userId: json['user_id'] as String,
      grade: json['grade'] as int,
      topics: (json['topics'] as List<dynamic>)
          .map((e) => TopicLevels.fromJson(e as Map<String, dynamic>))
          .toList(),
      overallLevel: (json['overall_level'] as num?)?.toDouble() ?? 0.0,
    );
  }

  /// Find topic levels by topic ID.
  TopicLevels? forTopic(String topicId) {
    try {
      return topics.firstWhere((t) => t.topicId == topicId);
    } catch (_) {
      return null;
    }
  }

  /// The topic the student should continue with (highest current level that isn't mastered).
  TopicLevels? get continueWithTopic {
    final active = topics.where((t) => !t.allMastered).toList();
    if (active.isEmpty) return topics.isNotEmpty ? topics.first : null;
    // Pick the one they've been progressing most in
    active.sort((a, b) => b.currentLevel.compareTo(a.currentLevel));
    return active.first;
  }
}
