/// Progress model for the 4-Pillar Olympiad system.
///
/// Tracks per-pillar mastery, current level, and question stats.
/// Synced with Firestore collection: pillar_progress/{userId}

class PillarProgress {
  final String pillar; // algebra, number_theory, combinatorics, geometry
  final int currentLevel; // 1–5
  final int questionsAttempted;
  final int questionsCorrect;
  final double masteryPercent; // 0.0–100.0
  final Map<int, LevelProgress> levelProgress; // level → stats

  PillarProgress({
    required this.pillar,
    this.currentLevel = 1,
    this.questionsAttempted = 0,
    this.questionsCorrect = 0,
    this.masteryPercent = 0.0,
    this.levelProgress = const {},
  });

  double get accuracy =>
      questionsAttempted > 0 ? questionsCorrect / questionsAttempted * 100 : 0;

  bool get canAdvance => masteryPercent >= 60.0;

  factory PillarProgress.fromJson(Map<String, dynamic> json) {
    final levelRaw = json['level_progress'] as Map<String, dynamic>? ?? {};
    return PillarProgress(
      pillar: json['pillar'] as String? ?? '',
      currentLevel: json['current_level'] as int? ?? 1,
      questionsAttempted: json['questions_attempted'] as int? ?? 0,
      questionsCorrect: json['questions_correct'] as int? ?? 0,
      masteryPercent: (json['mastery_percent'] as num?)?.toDouble() ?? 0.0,
      levelProgress: levelRaw.map(
        (k, v) => MapEntry(
          int.parse(k),
          LevelProgress.fromJson(v as Map<String, dynamic>),
        ),
      ),
    );
  }

  Map<String, dynamic> toJson() => {
        'pillar': pillar,
        'current_level': currentLevel,
        'questions_attempted': questionsAttempted,
        'questions_correct': questionsCorrect,
        'mastery_percent': masteryPercent,
        'level_progress': levelProgress.map(
          (k, v) => MapEntry(k.toString(), v.toJson()),
        ),
      };
}

class LevelProgress {
  final int level;
  final int attempted;
  final int correct;
  final double mastery;
  final List<String> completedTopics;
  final DateTime? lastPracticed;

  LevelProgress({
    required this.level,
    this.attempted = 0,
    this.correct = 0,
    this.mastery = 0.0,
    this.completedTopics = const [],
    this.lastPracticed,
  });

  factory LevelProgress.fromJson(Map<String, dynamic> json) {
    final topicsRaw = json['completed_topics'] as List<dynamic>? ?? [];
    return LevelProgress(
      level: json['level'] as int? ?? 1,
      attempted: json['attempted'] as int? ?? 0,
      correct: json['correct'] as int? ?? 0,
      mastery: (json['mastery'] as num?)?.toDouble() ?? 0.0,
      completedTopics: topicsRaw.map((e) => e.toString()).toList(),
      lastPracticed: json['last_practiced'] != null
          ? DateTime.tryParse(json['last_practiced'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'level': level,
        'attempted': attempted,
        'correct': correct,
        'mastery': mastery,
        'completed_topics': completedTopics,
        if (lastPracticed != null)
          'last_practiced': lastPracticed!.toIso8601String(),
      };
}

/// Summary of all 4 pillars for the home screen.
class PillarSummary {
  final Map<String, PillarProgress> pillars;
  final int totalQuestions;
  final int totalCorrect;
  final int streak;
  final String? dailyChallengeId;

  PillarSummary({
    required this.pillars,
    this.totalQuestions = 0,
    this.totalCorrect = 0,
    this.streak = 0,
    this.dailyChallengeId,
  });

  PillarProgress get algebra =>
      pillars['algebra'] ?? PillarProgress(pillar: 'algebra');
  PillarProgress get numberTheory =>
      pillars['number_theory'] ?? PillarProgress(pillar: 'number_theory');
  PillarProgress get combinatorics =>
      pillars['combinatorics'] ?? PillarProgress(pillar: 'combinatorics');
  PillarProgress get geometry =>
      pillars['geometry'] ?? PillarProgress(pillar: 'geometry');

  factory PillarSummary.fromJson(Map<String, dynamic> json) {
    final pillarsRaw = json['pillars'] as Map<String, dynamic>? ?? {};
    return PillarSummary(
      pillars: pillarsRaw.map(
        (k, v) => MapEntry(k, PillarProgress.fromJson(v as Map<String, dynamic>)),
      ),
      totalQuestions: json['total_questions'] as int? ?? 0,
      totalCorrect: json['total_correct'] as int? ?? 0,
      streak: json['streak'] as int? ?? 0,
      dailyChallengeId: json['daily_challenge_id'] as String?,
    );
  }
}

/// Pillar metadata (static info — name, emoji, color, tagline).
class PillarMeta {
  final String id;
  final String name;
  final String emoji;
  final String tagline;
  final String colorHex; // Primary brand color for this pillar

  const PillarMeta({
    required this.id,
    required this.name,
    required this.emoji,
    required this.tagline,
    required this.colorHex,
  });

  static const List<PillarMeta> all = [
    PillarMeta(
      id: 'algebra',
      name: 'Algebra',
      emoji: '\u{1F9EE}', // 🧮
      tagline: 'Patterns, equations & elegant proofs',
      colorHex: 'FF6D00',
    ),
    PillarMeta(
      id: 'number_theory',
      name: 'Number Theory',
      emoji: '\u{1F522}', // 🔢
      tagline: 'Primes, divisibility & hidden structure',
      colorHex: '2E7D32',
    ),
    PillarMeta(
      id: 'combinatorics',
      name: 'Combinatorics',
      emoji: '\u{1F3B2}', // 🎲
      tagline: 'Counting, probability & clever arguments',
      colorHex: '1565C0',
    ),
    PillarMeta(
      id: 'geometry',
      name: 'Geometry',
      emoji: '\u{1F4D0}', // 📐
      tagline: 'Shapes, symmetry & spatial reasoning',
      colorHex: '7B1FA2',
    ),
  ];

  static PillarMeta byId(String id) =>
      all.firstWhere((p) => p.id == id, orElse: () => all.first);
}
