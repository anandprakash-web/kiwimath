import 'package:flutter/material.dart';
import '../models/question_v2.dart';

/// Khan Academy-style inline stepped hint widget.
///
/// Renders progressive solution steps inline between the question stem and
/// answer options. Each step is revealed one at a time with a colored left
/// border and slide+fade animation.
class InlineHintSteps extends StatefulWidget {
  /// Primary input: each string is one step of the worked solution.
  final List<String> solutionSteps;

  /// Fallback: legacy hint ladder format (converted to steps internally).
  final HintLadder? hintLadder;

  /// Fires when a new step is revealed, with the step index (0-based).
  final ValueChanged<int>? onStepRevealed;

  /// How many steps to show initially. Use -1 for none revealed yet.
  final int initialStepRevealed;

  const InlineHintSteps({
    super.key,
    this.solutionSteps = const [],
    this.hintLadder,
    this.onStepRevealed,
    this.initialStepRevealed = -1,
  });

  @override
  State<InlineHintSteps> createState() => _InlineHintStepsState();
}

class _InlineHintStepsState extends State<InlineHintSteps>
    with TickerProviderStateMixin {
  late List<String> _steps;
  late int _revealedCount; // number of steps currently visible
  final List<AnimationController> _controllers = [];
  final List<Animation<double>> _slideAnimations = [];
  final List<Animation<double>> _fadeAnimations = [];

  // Step color palette — cycles if more than 4 steps.
  static const _stepColors = [
    _StepColorScheme(
      background: Color(0xFFE1F5FE),
      border: Color(0xFF81D4FA),
      text: Color(0xFF0277BD),
    ),
    _StepColorScheme(
      background: Color(0xFFFFF3E0),
      border: Color(0xFFFFB74D),
      text: Color(0xFFE65100),
    ),
    _StepColorScheme(
      background: Color(0xFFF3E5F5),
      border: Color(0xFFCE93D8),
      text: Color(0xFF6A1B9A),
    ),
    _StepColorScheme(
      background: Color(0xFFE8F5E9),
      border: Color(0xFF81C784),
      text: Color(0xFF2E7D32),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _steps = _resolveSteps();
    _revealedCount = (widget.initialStepRevealed + 1).clamp(0, _steps.length);

    // Create animation controllers for already-revealed steps (no animation).
    for (var i = 0; i < _revealedCount; i++) {
      _addController(animate: false);
    }
  }

  @override
  void didUpdateWidget(InlineHintSteps oldWidget) {
    super.didUpdateWidget(oldWidget);
    final newSteps = _resolveSteps();
    if (newSteps.length != _steps.length ||
        !_listsEqual(newSteps, _steps)) {
      setState(() {
        _steps = newSteps;
        _revealedCount = _revealedCount.clamp(0, _steps.length);
      });
    }
  }

  @override
  void dispose() {
    for (final controller in _controllers) {
      controller.dispose();
    }
    super.dispose();
  }

  /// Resolves the effective list of steps, handling backward compatibility.
  List<String> _resolveSteps() {
    if (widget.solutionSteps.isNotEmpty) {
      return widget.solutionSteps;
    }
    if (widget.hintLadder == null) return [];

    final ladder = widget.hintLadder!;
    // 6-level ladder: use level2, level3, level4 (teaching parts).
    final sixLevel = [ladder.level2, ladder.level3, ladder.level4]
        .where((s) => s.isNotEmpty)
        .toList();
    if (sixLevel.isNotEmpty) return sixLevel;

    // 3-level ladder fallback: use all non-empty levels.
    return [ladder.level0, ladder.level1, ladder.level2]
        .where((s) => s.isNotEmpty)
        .toList();
  }

  void _addController({required bool animate}) {
    final controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 350),
    );
    final curved = CurvedAnimation(
      parent: controller,
      curve: Curves.easeOutCubic,
    );
    _controllers.add(controller);
    _slideAnimations.add(
      Tween<double>(begin: 20.0, end: 0.0).animate(curved),
    );
    _fadeAnimations.add(
      Tween<double>(begin: 0.0, end: 1.0).animate(curved),
    );

    if (animate) {
      controller.forward();
    } else {
      controller.value = 1.0;
    }
  }

  void _revealNextStep() {
    if (_revealedCount >= _steps.length) return;

    setState(() {
      _addController(animate: true);
      _revealedCount++;
    });

    widget.onStepRevealed?.call(_revealedCount - 1);
  }

  static bool _listsEqual(List<String> a, List<String> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  _StepColorScheme _colorForStep(int index) {
    return _stepColors[index % _stepColors.length];
  }

  @override
  Widget build(BuildContext context) {
    if (_steps.isEmpty) return const SizedBox.shrink();

    // Not yet started — show the "Need help?" button.
    if (_revealedCount == 0) {
      return _buildNeedHelpButton();
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Revealed steps.
        for (var i = 0; i < _revealedCount; i++) _buildStepCard(i),

        // "Show next step" button if more remain.
        if (_revealedCount < _steps.length)
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: _buildShowNextButton(),
          ),
      ],
    );
  }

  Widget _buildNeedHelpButton() {
    return Align(
      alignment: Alignment.centerRight,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: _revealNextStep,
          borderRadius: BorderRadius.circular(20),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF42A5F5), Color(0xFF1976D2)],
              ),
              borderRadius: BorderRadius.circular(20),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF1976D2).withOpacity(0.3),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.lightbulb_outline, color: Colors.white, size: 16),
                SizedBox(width: 6),
                Text(
                  'Need help?',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepCard(int index) {
    final colors = _colorForStep(index);

    return AnimatedBuilder(
      animation: _controllers[index],
      builder: (context, child) {
        return Transform.translate(
          offset: Offset(0, _slideAnimations[index].value),
          child: Opacity(
            opacity: _fadeAnimations[index].value,
            child: child,
          ),
        );
      },
      child: Padding(
        padding: const EdgeInsets.only(bottom: 8.0),
        child: Container(
          decoration: BoxDecoration(
            color: colors.background,
            borderRadius: BorderRadius.circular(8),
            border: Border(
              left: BorderSide(color: colors.border, width: 3),
            ),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Step ${index + 1}',
                style: TextStyle(
                  color: colors.text,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.3,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _steps[index],
                style: TextStyle(
                  color: Colors.grey.shade900,
                  fontSize: 14,
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildShowNextButton() {
    final remaining = _steps.length - _revealedCount;

    return Align(
      alignment: Alignment.centerLeft,
      child: TextButton.icon(
        onPressed: _revealNextStep,
        icon: const Icon(Icons.arrow_downward, size: 16),
        label: Text('Show next step ($remaining remaining)'),
        style: TextButton.styleFrom(
          foregroundColor: const Color(0xFF1976D2),
          textStyle: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        ),
      ),
    );
  }
}

/// Internal color scheme for a single step.
class _StepColorScheme {
  final Color background;
  final Color border;
  final Color text;

  const _StepColorScheme({
    required this.background,
    required this.border,
    required this.text,
  });
}
