/// Data models that mirror the backend's QuestionOut response.
/// Source of truth is backend/app/api/questions.py::QuestionOut.
/// If that shape changes, change this file.

class KiwiVisual {
  final String kind; // 'svg_inline' or 'static_asset'
  final String? svg;
  final String? path;
  final String? altText;

  KiwiVisual({required this.kind, this.svg, this.path, this.altText});

  factory KiwiVisual.fromJson(Map<String, dynamic> json) => KiwiVisual(
        kind: json['kind'] as String,
        svg: json['svg'] as String?,
        path: json['path'] as String?,
        altText: json['alt_text'] as String?,
      );
}

class KiwiOption {
  final String text;
  KiwiOption({required this.text});

  factory KiwiOption.fromJson(Map<String, dynamic> json) =>
      KiwiOption(text: json['text'] as String);
}

class KiwiQuestion {
  final String questionId;
  final String stem;
  final List<KiwiOption> options;
  final int correctIndex;
  final KiwiVisual? visual;
  final int? estTimeSeconds;

  /// Concrete param values the server used to render this question.
  /// Pass these back when requesting a step-down so it inherits consistently.
  final Map<String, dynamic> paramsUsed;

  /// index -> misconception diagnosis (snake_case label)
  final Map<int, String> wrongOptionDiagnosis;

  /// index -> ordered list of step-down question ids
  final Map<int, List<String>> wrongOptionStepDownPath;

  /// index -> warm kid-facing message (from misconception.feedback_child)
  final Map<int, String> wrongOptionFeedback;

  KiwiQuestion({
    required this.questionId,
    required this.stem,
    required this.options,
    required this.correctIndex,
    this.visual,
    this.estTimeSeconds,
    required this.paramsUsed,
    required this.wrongOptionDiagnosis,
    required this.wrongOptionStepDownPath,
    required this.wrongOptionFeedback,
  });

  bool get hasStepDownFor => wrongOptionStepDownPath.isNotEmpty;

  factory KiwiQuestion.fromJson(Map<String, dynamic> json) {
    final optionsJson = json['options'] as List<dynamic>;
    final diagJson = (json['wrong_option_diagnosis'] ?? {}) as Map<String, dynamic>;
    final pathJson = (json['wrong_option_step_down_path'] ?? {}) as Map<String, dynamic>;
    final fbJson = (json['wrong_option_feedback'] ?? {}) as Map<String, dynamic>;
    final paramsJson = (json['params_used'] ?? {}) as Map<String, dynamic>;

    return KiwiQuestion(
      questionId: json['question_id'] as String,
      stem: json['stem'] as String,
      options:
          optionsJson.map((o) => KiwiOption.fromJson(o as Map<String, dynamic>)).toList(),
      correctIndex: json['correct_index'] as int,
      visual: json['visual'] == null
          ? null
          : KiwiVisual.fromJson(json['visual'] as Map<String, dynamic>),
      estTimeSeconds: json['est_time_seconds'] as int?,
      paramsUsed: Map<String, dynamic>.from(paramsJson),
      wrongOptionDiagnosis:
          diagJson.map((k, v) => MapEntry(int.parse(k), v as String)),
      wrongOptionStepDownPath: pathJson.map(
        (k, v) => MapEntry(
          int.parse(k),
          (v as List<dynamic>).map((e) => e as String).toList(),
        ),
      ),
      wrongOptionFeedback:
          fbJson.map((k, v) => MapEntry(int.parse(k), v as String)),
    );
  }
}
