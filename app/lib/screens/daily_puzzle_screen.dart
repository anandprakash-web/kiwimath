import 'dart:async';

import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';
import '../models/engagement.dart';

/// Daily puzzle solving experience — story narrative, MCQ, timer, hints, results.
///
/// Designed to feel like opening a gift every day: exciting, rewarding, and
/// full of character.
class DailyPuzzleScreen extends StatefulWidget {
  final DailyPuzzle puzzle;
  final int currentStreak;
  final int gemsBalance;

  /// Submits the answer to the server and returns the graded result.
  /// The server's [PuzzleSubmissionResult.correct] is authoritative —
  /// the client never knows the right answer up front.
  final Future<PuzzleSubmissionResult?> Function(
      int selectedIndex, int timeTakenSeconds)? onSubmit;
  final VoidCallback? onShareResult;
  final VoidCallback? onClose;

  const DailyPuzzleScreen({
    super.key,
    required this.puzzle,
    this.currentStreak = 0,
    this.gemsBalance = 0,
    this.onSubmit,
    this.onShareResult,
    this.onClose,
  });

  @override
  State<DailyPuzzleScreen> createState() => _DailyPuzzleScreenState();
}

class _DailyPuzzleScreenState extends State<DailyPuzzleScreen>
    with TickerProviderStateMixin {
  int? _selectedIndex;
  bool _submitted = false;
  bool _checking = false;
  bool _isCorrect = false;
  int? _correctIndex; // Only known when the server says our pick was right.
  bool _hint1Used = false;
  bool _hint2Used = false;
  int _elapsedSeconds = 0;
  Timer? _timer;
  int _pointsEarned = 0;

  late final AnimationController _resultController;
  late final Animation<double> _resultScaleAnimation;
  late final Animation<double> _resultFadeAnimation;

  late final AnimationController _optionFeedbackController;

  @override
  void initState() {
    super.initState();
    _startTimer();

    _resultController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _resultScaleAnimation = Tween<double>(begin: 0.5, end: 1.0).animate(
      CurvedAnimation(parent: _resultController, curve: Curves.elasticOut),
    );
    _resultFadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _resultController, curve: Curves.easeIn),
    );

    _optionFeedbackController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _resultController.dispose();
    _optionFeedbackController.dispose();
    super.dispose();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!_submitted) {
        setState(() => _elapsedSeconds++);
      }
    });
  }

  String _formatTime(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  void _selectOption(int index) {
    if (_submitted) return;
    setState(() => _selectedIndex = index);
  }

  Future<void> _submit() async {
    if (_selectedIndex == null || _submitted || _checking) return;

    // The correct answer lives server-side only: submit, and let the
    // server's grading drive the UI (no client-side answer key).
    setState(() => _checking = true);
    _timer?.cancel();

    PuzzleSubmissionResult? result;
    var submissionFailed = false;
    try {
      result = await widget.onSubmit?.call(_selectedIndex!, _elapsedSeconds);
    } catch (_) {
      submissionFailed = true;
    }
    if (!mounted) return;

    if (submissionFailed || (widget.onSubmit != null && result == null)) {
      // Couldn't reach the server — let the child try submitting again.
      setState(() => _checking = false);
      _startTimer();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not submit your answer. Check your connection and try again!'),
        ),
      );
      return;
    }

    final correct = result?.correct ?? false;
    setState(() {
      _checking = false;
      _submitted = true;
      _isCorrect = correct;
      // We only learn the correct index when our pick was right; on a wrong
      // answer the server does not reveal it (clan-mates still get to solve).
      _correctIndex = correct ? _selectedIndex : null;
      _pointsEarned = result?.pointsEarned ?? 0;
    });

    _optionFeedbackController.forward();
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) _resultController.forward();
    });
  }

  void _useHint1() {
    if (_hint1Used || _submitted) return;
    setState(() => _hint1Used = true);
  }

  void _useHint2() {
    if (_hint2Used || _submitted || widget.gemsBalance < 10) return;
    setState(() => _hint2Used = true);
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: Stack(
        children: [
          // Main content
          SafeArea(
            child: Column(
              children: [
                _buildTopBar(),
                Expanded(
                  child: SingleChildScrollView(
                    padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.xl),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(height: KiwiSpacing.lg),
                        _buildStorySection(),
                        SizedBox(height: KiwiSpacing.xl),
                        _buildQuestionSection(),
                        SizedBox(height: KiwiSpacing.xl),
                        _buildOptions(),
                        SizedBox(height: KiwiSpacing.xl),
                        if (!_submitted) ...[
                          _buildHintButtons(),
                          SizedBox(height: KiwiSpacing.xl),
                          _buildSubmitButton(),
                        ],
                        SizedBox(height: KiwiSpacing.xxl + KiwiSpacing.sm),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Result overlay
          if (_submitted) _buildResultOverlay(),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Top bar: close, timer, streak
  // ---------------------------------------------------------------------------

  Widget _buildTopBar() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.sm + 2),
      child: Row(
        children: [
          // Close button
          GestureDetector(
            onTap: widget.onClose,
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: KiwiColors.cardBg,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 8,
                  ),
                ],
              ),
              child: const Icon(
                Icons.close_rounded,
                color: KiwiColors.textMid,
                size: 22,
              ),
            ),
          ),
          const Spacer(),

          // Timer
          Container(
            padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.md + 2, vertical: KiwiSpacing.xs + 2),
            decoration: BoxDecoration(
              color: KiwiColors.cardBg,
              borderRadius: BorderRadius.circular(KiwiSpacing.xl),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 8,
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.timer_rounded,
                  size: 18,
                  color: _elapsedSeconds > 120
                      ? KiwiColors.coral
                      : KiwiColors.textMid,
                ),
                SizedBox(width: KiwiSpacing.xs + 2),
                Text(
                  _formatTime(_elapsedSeconds),
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    fontFeatures: const [FontFeature.tabularFigures()],
                    color: _elapsedSeconds > 120
                        ? KiwiColors.coral
                        : KiwiColors.textDark,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(width: KiwiSpacing.sm + 2),

          // Streak badge
          if (widget.currentStreak > 0)
            Container(
              padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.md, vertical: KiwiSpacing.xs + 2),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [KiwiColors.streakWarm, KiwiColors.kiwiPrimaryDark],
                ),
                borderRadius: BorderRadius.circular(KiwiSpacing.xl),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('\u{1F525}', style: TextStyle(fontSize: 14)),
                  const SizedBox(width: 4),
                  Text(
                    '${widget.currentStreak}',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Story section — Captain Kiwi character + story text
  // ---------------------------------------------------------------------------

  Widget _buildStorySection() {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(KiwiSpacing.lg + 2),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [KiwiColors.visualYellowBg, KiwiColors.kiwiPrimaryLight],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(KiwiSpacing.lg + 2),
        border: Border.all(
          color: KiwiColors.amber.withOpacity(0.3),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Captain Kiwi placeholder
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimary.withOpacity(0.15),
              borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
              border: Border.all(
                color: KiwiColors.kiwiPrimary.withOpacity(0.3),
              ),
            ),
            alignment: Alignment.center,
            child: const Text(
              '\u{1F95D}',
              style: TextStyle(fontSize: 32),
            ),
          ),
          SizedBox(width: KiwiSpacing.md + 2),

          // Story text
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.puzzle.title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.textDark,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  widget.puzzle.storyNarrative,
                  style: const TextStyle(
                    fontSize: 14,
                    color: KiwiColors.textMid,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Question section
  // ---------------------------------------------------------------------------

  Widget _buildQuestionSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Question',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: KiwiColors.xpPurple,
            letterSpacing: 0.5,
          ),
        ),
        SizedBox(height: KiwiSpacing.sm),
        Text(
          widget.puzzle.questionText,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // MCQ Options
  // ---------------------------------------------------------------------------

  Widget _buildOptions() {
    final options = widget.puzzle.options;
    return Column(
      children: [
        for (int i = 0; i < options.length && i < 4; i++) ...[
          if (i > 0) SizedBox(height: KiwiSpacing.sm + 2),
          _buildOptionButton(i, options[i]),
        ],
      ],
    );
  }

  Widget _buildOptionButton(int index, String text) {
    final isSelected = _selectedIndex == index;
    // Known only after a correct server-graded submission; on a wrong answer
    // no option is highlighted green (the server keeps the answer secret).
    final isCorrectAnswer = _correctIndex != null && index == _correctIndex;

    Color bgColor;
    Color borderColor;
    Color textColor;

    if (_submitted) {
      if (isCorrectAnswer) {
        bgColor = KiwiColors.correctBg;
        borderColor = KiwiColors.correct;
        textColor = KiwiColors.kiwiGreenDark;
      } else if (isSelected && !isCorrectAnswer) {
        bgColor = KiwiColors.wrongBg;
        borderColor = KiwiColors.wrong;
        textColor = KiwiColors.kiwiPrimaryDark;
      } else {
        bgColor = KiwiColors.cardBg;
        borderColor = KiwiColors.pathLocked;
        textColor = KiwiColors.textMuted;
      }
    } else if (isSelected) {
      bgColor = KiwiColors.kiwiPrimaryLight;
      borderColor = KiwiColors.kiwiPrimary;
      textColor = KiwiColors.kiwiPrimaryDark;
    } else {
      bgColor = KiwiColors.cardBg;
      borderColor = KiwiColors.pathLocked;
      textColor = KiwiColors.textDark;
    }

    final labels = ['A', 'B', 'C', 'D'];

    return GestureDetector(
      onTap: () => _selectOption(index),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
        width: double.infinity,
        padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.lg),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
          border: Border.all(color: borderColor, width: isSelected ? 2.5 : 1.5),
          boxShadow: isSelected && !_submitted
              ? [
                  BoxShadow(
                    color: KiwiColors.kiwiPrimary.withOpacity(0.15),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.03),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ],
        ),
        child: Row(
          children: [
            // Letter badge
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected && !_submitted
                    ? KiwiColors.kiwiPrimary
                    : borderColor.withOpacity(0.2),
              ),
              alignment: Alignment.center,
              child: Text(
                labels[index],
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  color: isSelected && !_submitted
                      ? Colors.white
                      : textColor,
                ),
              ),
            ),
            SizedBox(width: KiwiSpacing.md + 2),
            Expanded(
              child: Text(
                text,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: textColor,
                ),
              ),
            ),
            if (_submitted && isCorrectAnswer)
              const Icon(Icons.check_circle_rounded,
                  color: KiwiColors.correct, size: 24),
            if (_submitted && isSelected && !isCorrectAnswer)
              const Icon(Icons.cancel_rounded,
                  color: KiwiColors.wrong, size: 24),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Hint buttons
  // ---------------------------------------------------------------------------

  Widget _buildHintButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Hint 1 (free)
        if (!_hint1Used)
          GestureDetector(
            onTap: _useHint1,
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.md),
              decoration: BoxDecoration(
                color: KiwiColors.visualYellowBg,
                borderRadius: BorderRadius.circular(KiwiSpacing.md),
                border: Border.all(color: KiwiColors.visualYellowBorder),
              ),
              child: Row(
                children: [
                  const Text('\u{1F4A1}', style: TextStyle(fontSize: 20)),
                  SizedBox(width: KiwiSpacing.sm + 2),
                  const Expanded(
                    child: Text(
                      'Hint 1 (Free)',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.textDark,
                      ),
                    ),
                  ),
                  const Icon(
                    Icons.touch_app_rounded,
                    size: 20,
                    color: KiwiColors.amber,
                  ),
                ],
              ),
            ),
          )
        else
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(KiwiSpacing.md + 2),
            decoration: BoxDecoration(
              color: KiwiColors.visualYellowBg,
              borderRadius: BorderRadius.circular(KiwiSpacing.md),
              border: Border.all(color: KiwiColors.visualYellowBorder),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('\u{1F4A1}', style: TextStyle(fontSize: 18)),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    widget.puzzle.hint1,
                    style: const TextStyle(
                      fontSize: 14,
                      color: KiwiColors.textMid,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
        SizedBox(height: KiwiSpacing.sm + 2),

        // Hint 2 (costs gems)
        if (!_hint2Used)
          GestureDetector(
            onTap: _useHint2,
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.md),
              decoration: BoxDecoration(
                color: KiwiColors.visualBlueBg,
                borderRadius: BorderRadius.circular(KiwiSpacing.md),
                border: Border.all(color: KiwiColors.visualBlueBorder),
              ),
              child: Row(
                children: [
                  const Text('\u{1F48E}', style: TextStyle(fontSize: 20)),
                  SizedBox(width: KiwiSpacing.sm + 2),
                  Expanded(
                    child: Text(
                      'Hint 2 (10 gems)',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: widget.gemsBalance >= 10
                            ? KiwiColors.textDark
                            : KiwiColors.textMuted,
                      ),
                    ),
                  ),
                  if (widget.gemsBalance < 10)
                    const Text(
                      'Not enough gems',
                      style: TextStyle(
                        fontSize: 11,
                        color: KiwiColors.textMuted,
                      ),
                    ),
                ],
              ),
            ),
          )
        else
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(KiwiSpacing.md + 2),
            decoration: BoxDecoration(
              color: KiwiColors.visualBlueBg,
              borderRadius: BorderRadius.circular(KiwiSpacing.md),
              border: Border.all(color: KiwiColors.visualBlueBorder),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('\u{1F48E}', style: TextStyle(fontSize: 18)),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    widget.puzzle.hint2,
                    style: const TextStyle(
                      fontSize: 14,
                      color: KiwiColors.textMid,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Submit button
  // ---------------------------------------------------------------------------

  Widget _buildSubmitButton() {
    final canSubmit = _selectedIndex != null && !_submitted && !_checking;

    return SizedBox(
      width: double.infinity,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        decoration: BoxDecoration(
          gradient: canSubmit
              ? const LinearGradient(
                  colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
                )
              : null,
          color: canSubmit ? null : KiwiColors.pathLocked,
          borderRadius: BorderRadius.circular(KiwiSpacing.lg),
          boxShadow: canSubmit
              ? [
                  BoxShadow(
                    color: KiwiColors.kiwiPrimary.withOpacity(0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ]
              : [],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            borderRadius: BorderRadius.circular(KiwiSpacing.lg),
            onTap: canSubmit ? _submit : null,
            child: Padding(
              padding: EdgeInsets.symmetric(vertical: KiwiSpacing.lg + 2),
              child: Center(
                child: _checking
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: KiwiColors.textMuted,
                        ),
                      )
                    : Text(
                        'Submit Answer',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: canSubmit ? Colors.white : KiwiColors.textMuted,
                        ),
                      ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Result overlay
  // ---------------------------------------------------------------------------

  Widget _buildResultOverlay() {
    return AnimatedBuilder(
      animation: _resultController,
      builder: (context, child) {
        return Opacity(
          opacity: _resultFadeAnimation.value,
          child: Container(
            color: Colors.black.withOpacity(0.5 * _resultFadeAnimation.value),
            child: Center(
              child: Transform.scale(
                scale: _resultScaleAnimation.value,
                child: _buildResultCard(),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildResultCard() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: KiwiSpacing.xxl),
      padding: EdgeInsets.all(KiwiSpacing.xxl - 4),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(KiwiSpacing.xl),
        boxShadow: [
          BoxShadow(
            color: (_isCorrect ? KiwiColors.correct : KiwiColors.coral)
                .withOpacity(0.25),
            blurRadius: 30,
            spreadRadius: 4,
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Big emoji
          Text(
            _isCorrect ? '\u{1F389}\u{1F31F}' : '\u{1F914}',
            style: const TextStyle(fontSize: 56),
          ),
          SizedBox(height: KiwiSpacing.lg),

          // Title
          Text(
            _isCorrect ? 'Brilliant!' : 'Not quite...',
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w900,
              color: _isCorrect ? KiwiColors.kiwiGreenDark : KiwiColors.coral,
            ),
          ),
          SizedBox(height: KiwiSpacing.sm),

          Text(
            _isCorrect
                ? 'You nailed it! Great thinking!'
                : 'Keep practicing, you\'ll get it next time!',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 14,
              color: KiwiColors.textMid,
              height: 1.4,
            ),
          ),
          SizedBox(height: KiwiSpacing.xl),

          // Points earned
          Container(
            padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.xl, vertical: KiwiSpacing.md),
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('\u{2B50}', style: TextStyle(fontSize: 22)),
                SizedBox(width: KiwiSpacing.sm + 2),
                Text(
                  '+$_pointsEarned IPS',
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                    color: KiwiColors.kiwiPrimaryDark,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: KiwiSpacing.md),

          // Streak update
          if (widget.currentStreak > 0 || _isCorrect)
            Container(
              padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.sm),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [KiwiColors.streakWarm, KiwiColors.kiwiPrimaryDark],
                ),
                borderRadius: BorderRadius.circular(KiwiSpacing.md),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('\u{1F525}', style: TextStyle(fontSize: 18)),
                  SizedBox(width: KiwiSpacing.xs + 2),
                  Text(
                    _isCorrect
                        ? 'Streak: ${widget.currentStreak + 1} days!'
                        : 'Streak: ${widget.currentStreak} days',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
          SizedBox(height: KiwiSpacing.lg),

          // Time taken
          Text(
            'Time: ${_formatTime(_elapsedSeconds)}',
            style: const TextStyle(
              fontSize: 13,
              color: KiwiColors.textMuted,
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: KiwiSpacing.xl),

          // Action buttons
          Row(
            children: [
              // Share button
              Expanded(
                child: GestureDetector(
                  onTap: widget.onShareResult,
                  child: Container(
                    padding: EdgeInsets.symmetric(vertical: KiwiSpacing.md + 2),
                    decoration: BoxDecoration(
                      color: KiwiColors.creamDark,
                      borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
                    ),
                    child: const Center(
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.share_rounded,
                              size: 18, color: KiwiColors.textMid),
                          SizedBox(width: 6),
                          Text(
                            'Share',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: KiwiColors.textMid,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              SizedBox(width: KiwiSpacing.sm + 2),
              // Done button
              Expanded(
                child: GestureDetector(
                  onTap: widget.onClose,
                  child: Container(
                    padding: EdgeInsets.symmetric(vertical: KiwiSpacing.md + 2),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [
                          KiwiColors.kiwiPrimary,
                          KiwiColors.kiwiPrimaryDark,
                        ],
                      ),
                      borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
                    ),
                    child: const Center(
                      child: Text(
                        'Done',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
