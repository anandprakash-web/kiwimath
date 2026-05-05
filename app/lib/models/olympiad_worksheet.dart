/// Models for Olympiad daily worksheets.
///
/// API:
///   GET /olympiad/worksheets?grade=N&day=D  → OlympiadWorksheet
///   GET /olympiad/worksheets/list?grade=N    → WorksheetListResponse

class OlympiadQuestion {
  final String id;
  final String stem;
  final String interactionMode; // mcq, integer, fill_up, drag_drop, match_column
  final String topic;
  final String difficultyTier; // warmup, practice, challenge
  final int questionNumber;

  // MCQ
  final List<String> choices;
  final int correctAnswer;

  // Integer
  final int? correctValue;

  // Fill-up
  final String? fillBlankAnswer;

  // Drag & drop
  final List<String>? dragItems;

  // Match column
  final List<String>? leftColumn;
  final List<String>? rightColumn;
  final Map<String, String>? correctMatches;

  // Visual
  final String? visualUrl;
  final String? visualAlt;
  final Map<String, dynamic>? visualRef;

  // Pedagogy
  final String approach;
  final Map<String, String> hintLadder;

  OlympiadQuestion({
    required this.id,
    required this.stem,
    required this.interactionMode,
    required this.topic,
    required this.difficultyTier,
    required this.questionNumber,
    this.choices = const [],
    this.correctAnswer = 0,
    this.correctValue,
    this.fillBlankAnswer,
    this.dragItems,
    this.leftColumn,
    this.rightColumn,
    this.correctMatches,
    this.visualUrl,
    this.visualAlt,
    this.visualRef,
    this.approach = '',
    this.hintLadder = const {},
  });

  factory OlympiadQuestion.fromJson(Map<String, dynamic> json) {
    final choicesRaw = json['choices'] as List<dynamic>? ?? [];
    final dragRaw = json['drag_items'] as List<dynamic>?;
    final leftRaw = json['left_column'] as List<dynamic>?;
    final rightRaw = json['right_column'] as List<dynamic>?;
    final matchRaw = json['correct_matches'] as Map<String, dynamic>?;
    final hintRaw = json['hint_ladder'] as Map<String, dynamic>? ?? {};

    return OlympiadQuestion(
      id: json['id'] as String,
      stem: json['stem'] as String,
      interactionMode: json['interaction_mode'] as String? ?? 'mcq',
      topic: json['topic'] as String? ?? '',
      difficultyTier: json['difficulty_tier'] as String? ?? 'practice',
      questionNumber: json['question_number'] as int? ?? 0,
      choices: choicesRaw.map((e) => e.toString()).toList(),
      correctAnswer: json['correct_answer'] is int ? json['correct_answer'] as int : 0,
      correctValue: json['correct_value'] is int ? json['correct_value'] as int : null,
      fillBlankAnswer: json['fill_blank_answer']?.toString(),
      dragItems: dragRaw?.map((e) => e.toString()).toList(),
      leftColumn: leftRaw?.map((e) => e.toString()).toList(),
      rightColumn: rightRaw?.map((e) => e.toString()).toList(),
      correctMatches: matchRaw?.map((k, v) => MapEntry(k, v.toString())),
      visualUrl: json['visual_url'] as String?,
      visualAlt: json['visual_alt'] as String?,
      visualRef: json['visual_ref'] as Map<String, dynamic>?,
      approach: json['approach'] as String? ?? '',
      hintLadder: hintRaw.map((k, v) => MapEntry(k, v.toString())),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'stem': stem,
        'interaction_mode': interactionMode,
        'topic': topic,
        'difficulty_tier': difficultyTier,
        'question_number': questionNumber,
        'choices': choices,
        'correct_answer': correctAnswer,
        'correct_value': correctValue,
        'fill_blank_answer': fillBlankAnswer,
        'drag_items': dragItems,
        'left_column': leftColumn,
        'right_column': rightColumn,
        'correct_matches': correctMatches,
        'visual_url': visualUrl,
        'visual_alt': visualAlt,
        'visual_ref': visualRef,
        'approach': approach,
        'hint_ladder': hintLadder,
      };

  /// Check if user answer is correct.
  bool checkAnswer({int? selectedIndex, int? integerAnswer, String? textAnswer,
      List<int>? dragOrder, Map<String, String>? matchPairs}) {
    switch (interactionMode) {
      case 'mcq':
        return selectedIndex == correctAnswer;
      case 'integer':
        return integerAnswer == correctValue;
      case 'fill_up':
        if (fillBlankAnswer == null) return false;
        final userTrimmed = (textAnswer ?? '').trim().toLowerCase();
        final correctTrimmed = fillBlankAnswer!.trim().toLowerCase();
        return userTrimmed == correctTrimmed;
      case 'drag_drop':
        if (dragOrder == null) return false;
        for (int i = 0; i < dragOrder.length; i++) {
          if (dragOrder[i] != i) return false;
        }
        return true;
      case 'match_column':
        if (matchPairs == null || correctMatches == null) return false;
        for (final entry in correctMatches!.entries) {
          if (matchPairs[entry.key] != entry.value) return false;
        }
        return true;
      default:
        return false;
    }
  }
}

class OlympiadWorksheet {
  final int grade;
  final int day;
  final String title;
  final String subtitle;
  final String dominantTopic;
  final List<OlympiadQuestion> questions;

  OlympiadWorksheet({
    required this.grade,
    required this.day,
    required this.title,
    this.subtitle = '',
    this.dominantTopic = 'mixed',
    required this.questions,
  });

  factory OlympiadWorksheet.fromJson(Map<String, dynamic> json) {
    final questionsRaw = json['questions'] as List<dynamic>? ?? [];
    return OlympiadWorksheet(
      grade: json['grade'] as int? ?? 1,
      day: json['day'] as int? ?? 1,
      title: json['title'] as String? ?? 'Day ${json['day']}',
      subtitle: json['subtitle'] as String? ?? '',
      dominantTopic: json['dominant_topic'] as String? ?? 'mixed',
      questions: questionsRaw
          .map((q) => OlympiadQuestion.fromJson(q as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'grade': grade,
        'day': day,
        'title': title,
        'subtitle': subtitle,
        'dominant_topic': dominantTopic,
        'questions': questions.map((q) => q.toJson()).toList(),
      };

  int get warmupCount => questions.where((q) => q.difficultyTier == 'warmup').length;
  int get practiceCount => questions.where((q) => q.difficultyTier == 'practice').length;
  int get challengeCount => questions.where((q) => q.difficultyTier == 'challenge').length;
}

/// Lightweight metadata for worksheet list display (no questions loaded).
class WorksheetMeta {
  final int day;
  final String title;
  final String subtitle;
  final String dominantTopic;
  final int questionCount;
  final Map<String, int> difficultyDistribution;

  WorksheetMeta({
    required this.day,
    required this.title,
    this.subtitle = '',
    this.dominantTopic = 'mixed',
    this.questionCount = 12,
    this.difficultyDistribution = const {},
  });

  factory WorksheetMeta.fromJson(Map<String, dynamic> json) {
    final distRaw = json['difficulty_distribution'] as Map<String, dynamic>? ?? {};
    return WorksheetMeta(
      day: json['day'] as int? ?? 1,
      title: json['title'] as String? ?? 'Day ${json['day']}',
      subtitle: json['subtitle'] as String? ?? '',
      dominantTopic: json['dominant_topic'] as String? ?? 'mixed',
      questionCount: json['question_count'] as int? ?? 12,
      difficultyDistribution: distRaw.map((k, v) => MapEntry(k, v as int? ?? 0)),
    );
  }

  int get warmupCount => difficultyDistribution['warmup'] ?? 0;
  int get practiceCount => difficultyDistribution['practice'] ?? 0;
  int get challengeCount => difficultyDistribution['challenge'] ?? 0;
}

class WorksheetDay {
  final int day;
  final bool isAvailable;

  WorksheetDay({required this.day, this.isAvailable = true});
}
