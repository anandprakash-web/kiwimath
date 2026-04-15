import 'question.dart';

/// High-level phase of the question screen.
enum ScreenPhase {
  /// A parent question is on screen, waiting for a tap.
  parentQuestion,

  /// Kid just tapped wrong — showing the warm feedback message + "Let's try it step by step" CTA.
  wrongFeedback,

  /// A step-down question is on screen, mid-scaffolding.
  stepDownQuestion,

  /// Kid got the step-down wrong — show correct answer briefly, auto-advance.
  stepDownWrongFeedback,

  /// Kid completed the full step-down path — show "You got it!" success, then next parent.
  stepDownComplete,

  /// Kid got the parent right first try — show a cheer, then next parent.
  parentCorrect,
}

/// The state of an in-progress step-down session. Created when the kid taps a
/// wrong option on a parent question. Discarded when they finish the path or
/// bail out.
class StepDownSession {
  /// The parent question we're scaffolding away from.
  final KiwiQuestion parent;

  /// The diagnosis label (e.g. "added_instead_of_subtracted").
  final String diagnosis;

  /// The ordered list of step-down IDs we'll walk through.
  final List<String> path;

  /// Which step in `path` we're currently on (0-indexed).
  int currentStep;

  /// The warm feedback message shown BEFORE the step-downs start.
  final String openingFeedback;

  StepDownSession({
    required this.parent,
    required this.diagnosis,
    required this.path,
    required this.openingFeedback,
    this.currentStep = 0,
  });

  bool get isComplete => currentStep >= path.length;
  String? get currentStepId => isComplete ? null : path[currentStep];

  /// Params to inherit into the next step-down — everything the parent used,
  /// minus anything that doesn't inherit cleanly.
  Map<String, dynamic> inheritedParams() {
    final out = <String, dynamic>{};
    parent.paramsUsed.forEach((key, value) {
      if (value is String || value is num || value is bool) {
        out[key] = value;
      }
    });
    return out;
  }

  void advance() {
    currentStep++;
  }
}
