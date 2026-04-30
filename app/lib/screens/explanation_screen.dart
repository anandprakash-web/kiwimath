import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// Interactive explanation screen — Brilliant-inspired step-through learning.
///
/// Instead of passively showing the answer, this lets kids interact:
/// - Step 1: "Let's think about this" — shows the question + what went wrong
/// - Step 2: Interactive counting/tapping to discover the answer
/// - Step 3: Reinforcement — correct answer highlighted with encouragement
class ExplanationScreen extends StatefulWidget {
  final String feedbackMessage;
  final String questionStem;
  final String correctAnswer;
  final String wrongAnswer;
  final VoidCallback onDone;

  const ExplanationScreen({
    super.key,
    required this.feedbackMessage,
    required this.questionStem,
    required this.correctAnswer,
    required this.wrongAnswer,
    required this.onDone,
  });

  @override
  State<ExplanationScreen> createState() => _ExplanationScreenState();
}

class _ExplanationScreenState extends State<ExplanationScreen>
    with SingleTickerProviderStateMixin {
  int _currentStep = 0;
  static const _totalSteps = 3;

  // Interactive counting state (for step 2).
  int _tapCount = 0;
  bool _countingComplete = false;

  // Parse numeric answer for interactive counting.
  int? get _numericAnswer => int.tryParse(widget.correctAnswer.trim());

  // Animation for the celebration sparkle on step 3.
  late AnimationController _sparkleController;
  late Animation<double> _sparkleAnim;

  @override
  void initState() {
    super.initState();
    _sparkleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _sparkleAnim = CurvedAnimation(
      parent: _sparkleController,
      curve: Curves.elasticOut,
    );
  }

  @override
  void dispose() {
    _sparkleController.dispose();
    super.dispose();
  }

  void _nextStep() {
    if (_currentStep < _totalSteps - 1) {
      setState(() {
        _currentStep++;
        if (_currentStep == 2) {
          _sparkleController.forward();
        }
      });
    } else {
      widget.onDone();
    }
  }

  void _prevStep() {
    if (_currentStep > 0) {
      setState(() => _currentStep--);
    }
  }

  void _onItemTapped() {
    final target = _numericAnswer;
    if (target == null || _countingComplete) return;
    setState(() {
      _tapCount++;
      if (_tapCount >= target) {
        _countingComplete = true;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildProgressDots(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: _buildStepContent(),
              ),
            ),
            _buildBottomNav(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: const BoxDecoration(
        color: KiwiColors.visualYellowBg,
        border: Border(
          bottom: BorderSide(color: KiwiColors.visualYellowBorder, width: 1),
        ),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: const SizedBox(
              width: 28,
              child: Text(
                '✕',
                style: TextStyle(fontSize: 16, color: Color(0xFFBF360C)),
              ),
            ),
          ),
          const Expanded(
            child: Text(
              'Understanding the answer',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: Color(0xFFE65100),
              ),
            ),
          ),
          const SizedBox(width: 28),
        ],
      ),
    );
  }

  Widget _buildProgressDots() {
    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(_totalSteps, (i) {
          final isActive = i == _currentStep;
          final isDone = i < _currentStep;
          return Padding(
            padding: EdgeInsets.only(left: i == 0 ? 0 : 5),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeInOut,
              width: isActive ? 20 : 7,
              height: 7,
              decoration: BoxDecoration(
                color: isDone
                    ? KiwiColors.kiwiGreen
                    : isActive
                        ? KiwiColors.warmOrange
                        : KiwiColors.warmOrangeBorder,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildStepContent() {
    switch (_currentStep) {
      case 0:
        return _buildStep1ThinkAboutIt();
      case 1:
        return _buildStep2Interactive();
      case 2:
        return _buildStep3Reinforcement();
      default:
        return const SizedBox.shrink();
    }
  }

  // ─── Step 1: "Let's think about this" ─────────────────────────────
  Widget _buildStep1ThinkAboutIt() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Let’s think about this',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        const SizedBox(height: 14),
        // Question in a light-yellow card
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: KiwiColors.visualYellowBg,
            border: Border.all(
              color: KiwiColors.visualYellowBorder,
              width: 1.5,
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Column(
            children: [
              Text(
                widget.questionStem,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textDark,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'The question you were working on',
                style: TextStyle(
                  fontSize: 10,
                  color: const Color(0xFFF57F17),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        // What went wrong — feedback from the engine
        Text(
          widget.feedbackMessage,
          style: const TextStyle(
            fontSize: 14,
            color: KiwiColors.textDark,
            height: 1.55,
          ),
        ),
        const SizedBox(height: 12),
        // Your pick vs correct (compact)
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _buildAnswerChip(
              widget.wrongAnswer,
              Icons.close,
              const Color(0xFFEF5350),
              const Color(0xFFFFEBEE),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: Icon(Icons.arrow_forward, color: KiwiColors.textMuted, size: 18),
            ),
            _buildAnswerChip(
              widget.correctAnswer,
              Icons.check,
              KiwiColors.kiwiGreenDark,
              KiwiColors.kiwiGreenLight,
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildAnswerChip(String text, IconData icon, Color color, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.4), width: 1.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 5),
          Text(
            text,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  // ─── Step 2: Interactive discovery ─────────────────────────────────
  Widget _buildStep2Interactive() {
    final target = _numericAnswer;
    // If the answer is numeric and small (1-20), show an interactive counting grid.
    if (target != null && target >= 1 && target <= 20) {
      return _buildCountingInteraction(target);
    }
    // Fallback: guided text walkthrough for non-numeric answers.
    return _buildGuidedWalkthrough();
  }

  /// Interactive counting grid — kid taps each item, counter increments.
  Widget _buildCountingInteraction(int target) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Try it yourself!',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Tap each item to count. How many are there?',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: KiwiColors.textMuted,
          ),
        ),
        const SizedBox(height: 16),
        // Counting grid
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFFF3F1EC),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFE0DDD6), width: 1.5),
          ),
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            alignment: WrapAlignment.center,
            children: List.generate(target, (i) {
              final isTapped = i < _tapCount;
              return GestureDetector(
                onTap: () {
                  if (_tapCount == i) {
                    _onItemTapped();
                  }
                },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: isTapped
                        ? KiwiColors.kiwiGreenLight
                        : Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isTapped
                          ? KiwiColors.kiwiGreen
                          : const Color(0xFFE0E0E0),
                      width: isTapped ? 2 : 1.5,
                    ),
                    boxShadow: isTapped
                        ? [
                            BoxShadow(
                              color: KiwiColors.kiwiGreen.withOpacity(0.15),
                              blurRadius: 6,
                              offset: const Offset(0, 2),
                            ),
                          ]
                        : [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.04),
                              blurRadius: 4,
                              offset: const Offset(0, 2),
                            ),
                          ],
                  ),
                  child: Center(
                    child: isTapped
                        ? Text(
                            '${i + 1}',
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w800,
                              color: KiwiColors.kiwiGreenDark,
                            ),
                          )
                        : Text(
                            _getCountingEmoji(i),
                            style: const TextStyle(fontSize: 22),
                          ),
                  ),
                ),
              );
            }),
          ),
        ),
        const SizedBox(height: 16),
        // Live counter
        Center(
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              color: _countingComplete
                  ? KiwiColors.kiwiGreenLight
                  : const Color(0xFFF5F5F5),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _countingComplete
                    ? KiwiColors.kiwiGreen
                    : const Color(0xFFE0E0E0),
                width: 1.5,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _countingComplete ? '✅' : '\u{1F449}',
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(width: 8),
                Text(
                  _countingComplete
                      ? 'You counted $_tapCount — that’s right!'
                      : 'Count: $_tapCount / $target',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: _countingComplete
                        ? KiwiColors.kiwiGreenDark
                        : KiwiColors.textDark,
                  ),
                ),
              ],
            ),
          ),
        ),
        if (_countingComplete) ...[
          const SizedBox(height: 14),
          Center(
            child: Text(
              'Great job counting! The answer is $target.',
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: KiwiColors.kiwiGreenDark,
              ),
            ),
          ),
        ],
      ],
    );
  }

  /// Fallback guided walkthrough for non-countable answers.
  Widget _buildGuidedWalkthrough() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Let’s work through it',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Follow the steps below:',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: KiwiColors.textMuted,
          ),
        ),
        const SizedBox(height: 16),
        // Step-by-step breakdown
        _buildWalkthroughStep(
          1,
          'Read the question again',
          widget.questionStem,
          true,
        ),
        const SizedBox(height: 10),
        _buildWalkthroughStep(
          2,
          'Think about the key information',
          widget.feedbackMessage,
          true,
        ),
        const SizedBox(height: 10),
        _buildWalkthroughStep(
          3,
          'The correct answer',
          'The answer is ${widget.correctAnswer}.',
          true,
        ),
      ],
    );
  }

  Widget _buildWalkthroughStep(int num, String title, String content, bool revealed) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: revealed ? Colors.white : const Color(0xFFF5F5F5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: revealed
              ? KiwiColors.kiwiGreen.withOpacity(0.3)
              : const Color(0xFFE0E0E0),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiGreen,
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    '$num',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.textDark,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.only(left: 32),
            child: Text(
              content,
              style: const TextStyle(
                fontSize: 13,
                color: KiwiColors.textDark,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─── Step 3: Reinforcement ─────────────────────────────────────────
  Widget _buildStep3Reinforcement() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const SizedBox(height: 12),
        // Celebration icon
        ScaleTransition(
          scale: _sparkleAnim,
          child: Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF66BB6A), Color(0xFF43A047)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: KiwiColors.kiwiGreen.withOpacity(0.3),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const Center(
              child: Text('\u{1F4A1}', style: TextStyle(fontSize: 36)),
            ),
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Now you know!',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'The correct answer is ${widget.correctAnswer}.',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
            color: KiwiColors.textDark,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 20),
        // Correct answer card — large and proud
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: KiwiColors.kiwiGreenLight,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFA5D6A7), width: 2),
          ),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.check_circle, color: KiwiColors.kiwiGreenDark, size: 28),
                  const SizedBox(width: 10),
                  Text(
                    widget.correctAnswer,
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.kiwiGreenDark,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              const Text(
                'You’ll get it next time!',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF558B2F),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        // Key takeaway from feedback
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFFFFF8E1),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFFFE082), width: 1),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('\u{1F4DD}', style: TextStyle(fontSize: 16)),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  widget.feedbackMessage,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF795548),
                    height: 1.45,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  // ─── Bottom nav ────────────────────────────────────────────────────
  Widget _buildBottomNav() {
    final isLastStep = _currentStep == _totalSteps - 1;
    // For counting step, require completion before allowing Next.
    final canProceed = _currentStep != 1 ||
        _numericAnswer == null ||
        _countingComplete ||
        _numericAnswer! > 20;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFFF0F0F0), width: 1)),
      ),
      child: Row(
        children: [
          if (_currentStep > 0) ...[
            GestureDetector(
              onTap: _prevStep,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: const Color(0xFFE0E0E0), width: 2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  '← Back',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
          ],
          Expanded(
            child: GestureDetector(
              onTap: canProceed ? _nextStep : null,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: !canProceed
                      ? Colors.grey.shade300
                      : isLastStep
                          ? KiwiColors.kiwiGreen
                          : KiwiColors.warmOrange,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isLastStep
                      ? 'Now try it yourself →'
                      : _currentStep == 1 && !canProceed
                          ? 'Tap all items to continue'
                          : 'Next →',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: canProceed ? Colors.white : Colors.grey.shade500,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ─── Helpers ───────────────────────────────────────────────────────

  /// Cycle through fun counting emojis.
  String _getCountingEmoji(int index) {
    const emojis = [
      '\u{1F34E}', // apple
      '\u{1F34A}', // orange
      '\u{1F353}', // strawberry
      '\u{1F352}', // cherry
      '\u{1F347}', // grapes
      '\u{1F34B}', // lemon
      '\u{1F349}', // watermelon
      '\u{1F350}', // pear
      '\u{1F351}', // peach
      '\u{1F95D}', // kiwi
    ];
    return emojis[index % emojis.length];
  }
}
