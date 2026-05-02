import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/companion.dart';
import '../models/question_v2.dart';
import '../services/api_client.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';
import '../widgets/drag_drop_tiles.dart';
import '../widgets/inline_hint_steps.dart';
import '../widgets/integer_input.dart';
import '../widgets/option_card.dart';
import 'celebration_screen.dart';

/// v3 question screen — clean, competitor-informed redesign.
///
/// Key changes from v2:
///   - Segmented progress dots instead of gradient bar
///   - 2x2 grid options instead of vertical list
///   - Minimal wrong-answer feedback with "Why?" button
///   - In-place correct answer celebration
///   - Cleaner header (back + dots + one stat)
class QuestionScreenV2 extends StatefulWidget {
  final String topicId;
  final String topicName;
  final String? userId;
  final int grade;
  final VoidCallback? onBackToHome;
  final CompanionService? companionService;

  /// If provided, uses these as the question queue (smart session mode)
  /// instead of calling /v2/questions/next one at a time.
  final List<Map<String, dynamic>>? sessionPlan;

  /// Curriculum chapter name for IRT-powered chapter practice.
  /// When set, the backend uses get_curriculum_questions() for the candidate pool.
  final String? chapter;

  /// Curriculum identifier (ncert, icse, igcse) for chapter-based IRT.
  final String? curriculum;

  const QuestionScreenV2({
    super.key,
    required this.topicId,
    required this.topicName,
    this.userId,
    this.grade = 1,
    this.onBackToHome,
    this.companionService,
    this.sessionPlan,
    this.chapter,
    this.curriculum,
  });

  @override
  State<QuestionScreenV2> createState() => _QuestionScreenV2State();
}

enum _PhaseV2 {
  loading,
  answering,
  selected,
  submitting,
  correct,
  wrong,
}

class _QuestionScreenV2State extends State<QuestionScreenV2> {
  final ApiClient _api = ApiClient();

  KiwiTier get _tier => KiwiTier.forGrade(widget.grade);

  // Session state
  _PhaseV2 _phase = _PhaseV2.loading;
  QuestionV2? _question;
  AnswerCheckResponse? _lastResult;
  int? _selectedIndex;
  String? _error;

  // Difficulty tracking
  int _currentDifficulty = 1;

  // Progress tracking
  int _questionsAnswered = 0;
  late final int _totalQuestions;
  int _correctCount = 0;

  // Smart session mode — index into sessionPlan
  int _planIndex = 0;
  int _xp = 0;
  int _coins = 0;
  int _gems = 0;
  int _streak = 0;

  // Exclude already-answered question IDs
  final List<String> _excludeIds = [];

  // Track hint usage per question
  int _maxHintLevel = -1;

  // Time tracking
  DateTime? _questionStartTime;

  // Companion state
  final GlobalKey<CompanionViewState> _companionKey = GlobalKey();

  CompanionSurface get _companionSurface {
    switch (_phase) {
      case _PhaseV2.loading:
        return CompanionSurface.lessonFraming;
      case _PhaseV2.answering:
      case _PhaseV2.selected:
      case _PhaseV2.submitting:
        if (_maxHintLevel == 0) return CompanionSurface.lessonHint1;
        if (_maxHintLevel >= 1) return CompanionSurface.lessonHint2;
        return CompanionSurface.lessonFraming;
      case _PhaseV2.correct:
        return CompanionSurface.lessonMastery;
      case _PhaseV2.wrong:
        return CompanionSurface.lessonWrong;
    }
  }

  @override
  void initState() {
    super.initState();
    _totalQuestions = widget.sessionPlan?.length ?? 10;
    widget.companionService?.startNewLesson();
    widget.companionService?.startDeepThinkMonitor();
    _fetchNextQuestion();
  }

  // -------------------------------------------------------------------
  // Data fetching
  // -------------------------------------------------------------------

  Future<void> _fetchNextQuestion() async {
    setState(() {
      _phase = _PhaseV2.loading;
      _question = null;
      _selectedIndex = null;
      _lastResult = null;
      _error = null;
      _maxHintLevel = -1;
    });

    try {
      QuestionV2 question;

      if (widget.sessionPlan != null) {
        // Smart session mode — load questions by ID from the plan
        if (_planIndex >= widget.sessionPlan!.length) {
          // Plan exhausted — show session complete
          _showSessionComplete();
          return;
        }
        final planItem = widget.sessionPlan![_planIndex];
        final questionId = planItem['question_id'] as String;
        question = await _api.getQuestionV2(questionId);
        _planIndex++;
      } else {
        // Default topic-locked mode (with IRT for chapters when curriculum is set)
        question = await _api.nextQuestionV2(
          topic: widget.topicId,
          difficulty: _currentDifficulty,
          window: 10,
          exclude: _excludeIds.isNotEmpty ? _excludeIds : null,
          userId: widget.userId,
          grade: widget.grade,
          chapter: widget.chapter,
          curriculum: widget.curriculum,
        );
      }

      if (!mounted) return;

      setState(() {
        _question = question;
        _phase = _PhaseV2.answering;
        _questionStartTime = DateTime.now();
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  // -------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------

  void _onOptionTap(int index) {
    if (_phase != _PhaseV2.answering && _phase != _PhaseV2.selected) return;
    widget.companionService?.recordKidAction();
    setState(() {
      _selectedIndex = index;
      _phase = _PhaseV2.selected;
    });
  }

  Future<void> _onCheckAnswer() async {
    final q = _question;
    if (q == null || _selectedIndex == null) return;

    setState(() => _phase = _PhaseV2.submitting);

    final timeTakenMs = _questionStartTime != null
        ? DateTime.now().difference(_questionStartTime!).inMilliseconds
        : 0;

    try {
      final result = await _api.checkAnswerV2(
        questionId: q.questionId,
        selectedAnswer: _selectedIndex!,
        userId: widget.userId,
        timeTakenMs: timeTakenMs,
        hintsUsed: _maxHintLevel >= 0 ? _maxHintLevel : 0,
      );
      if (!mounted) return;

      _lastResult = result;
      _questionsAnswered++;
      _excludeIds.add(q.questionId);

      _xp += result.xpEarned;
      _coins += result.coinsEarned;
      _gems += result.gemsEarned;
      _currentDifficulty = (result.nextDifficulty).clamp(1, 100);

      if (result.correct) {
        _correctCount++;
        _streak++;
        setState(() => _phase = _PhaseV2.correct);
        _companionKey.currentState?.playCelebration();
      } else {
        _streak = 0;
        setState(() => _phase = _PhaseV2.wrong);
      }

      _showGamificationEvents(result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _phase = _PhaseV2.selected);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text(
            'Oops! Could not reach the server. Tap Check to try again.',
            style: TextStyle(fontSize: 13),
          ),
          backgroundColor: const Color(0xFFE65100),
          behavior: SnackBarBehavior.floating,
          margin: const EdgeInsets.fromLTRB(16, 0, 16, 80),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  Future<void> _onIntegerSubmit(int value) async {
    final q = _question;
    if (q == null) return;

    setState(() => _phase = _PhaseV2.submitting);

    final timeTakenMs = _questionStartTime != null
        ? DateTime.now().difference(_questionStartTime!).inMilliseconds
        : 0;

    try {
      final result = await _api.checkAnswerV2(
        questionId: q.questionId,
        selectedAnswer: 0,
        integerAnswer: value,
        userId: widget.userId,
        timeTakenMs: timeTakenMs,
        hintsUsed: _maxHintLevel >= 0 ? _maxHintLevel : 0,
      );
      if (!mounted) return;
      _handleResult(q, result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _phase = _PhaseV2.answering);
      _showNetworkError();
    }
  }

  Future<void> _onDragDropSubmit(List<int> order) async {
    final q = _question;
    if (q == null) return;

    setState(() => _phase = _PhaseV2.submitting);

    final timeTakenMs = _questionStartTime != null
        ? DateTime.now().difference(_questionStartTime!).inMilliseconds
        : 0;

    try {
      final result = await _api.checkAnswerV2(
        questionId: q.questionId,
        selectedAnswer: 0,
        dragOrder: order,
        userId: widget.userId,
        timeTakenMs: timeTakenMs,
        hintsUsed: _maxHintLevel >= 0 ? _maxHintLevel : 0,
      );
      if (!mounted) return;
      _handleResult(q, result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _phase = _PhaseV2.answering);
      _showNetworkError();
    }
  }

  void _handleResult(QuestionV2 q, AnswerCheckResponse result) {
    _lastResult = result;
    _questionsAnswered++;
    _excludeIds.add(q.questionId);

    _xp += result.xpEarned;
    _coins += result.coinsEarned;
    _gems += result.gemsEarned;
    _currentDifficulty = (result.nextDifficulty).clamp(1, 100);

    if (result.correct) {
      _correctCount++;
      _streak++;
      setState(() => _phase = _PhaseV2.correct);
      _companionKey.currentState?.playCelebration();
    } else {
      _streak = 0;
      setState(() => _phase = _PhaseV2.wrong);
    }

    _showGamificationEvents(result);
  }

  void _showNetworkError() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          'Oops! Could not reach the server. Please try again.',
          style: TextStyle(fontSize: 13),
        ),
        backgroundColor: const Color(0xFFE65100),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.fromLTRB(16, 0, 16, 80),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 4),
      ),
    );
  }

  // -------------------------------------------------------------------
  // Gamification events
  // -------------------------------------------------------------------

  void _showGamificationEvents(AnswerCheckResponse result) {
    if (result.xpEarned > 0) {
      _showXpToast(result.xpEarned);
    }

    if (result.microCelebration != null) {
      Future.delayed(const Duration(milliseconds: 400), () {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              result.microCelebration!,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            backgroundColor: KiwiColors.kiwiGreen,
            behavior: SnackBarBehavior.floating,
            margin: const EdgeInsets.fromLTRB(40, 0, 40, 100),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            duration: const Duration(seconds: 2),
          ),
        );
      });
    }

    if (result.badgeUnlocks.isNotEmpty) {
      Future.delayed(const Duration(milliseconds: 800), () {
        if (!mounted) return;
        for (final badge in result.badgeUnlocks) {
          _showBadgeUnlockDialog(badge);
        }
      });
    }

    if (result.levelUp != null) {
      Future.delayed(
        Duration(milliseconds: result.badgeUnlocks.isNotEmpty ? 1600 : 800),
        () {
          if (!mounted) return;
          _showLevelUpDialog(result.levelUp!);
        },
      );
    }
  }

  void _showXpToast(int xp) {
    final overlay = Overlay.of(context);
    late OverlayEntry entry;
    entry = OverlayEntry(
      builder: (context) => _XpToastAnimation(
        xp: xp,
        onDone: () => entry.remove(),
      ),
    );
    overlay.insert(entry);
  }

  void _showBadgeUnlockDialog(Map<String, dynamic> badge) {
    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Badge Unlock',
      barrierColor: Colors.black38,
      transitionDuration: const Duration(milliseconds: 300),
      transitionBuilder: (ctx, anim, _, child) {
        return ScaleTransition(
          scale: CurvedAnimation(parent: anim, curve: Curves.elasticOut),
          child: child,
        );
      },
      pageBuilder: (ctx, _, __) {
        Future.delayed(const Duration(seconds: 3), () {
          if (Navigator.of(ctx, rootNavigator: true).canPop()) {
            Navigator.of(ctx, rootNavigator: true).pop();
          }
        });

        final emoji = badge['emoji'] as String? ?? '';
        final name = badge['badge_name'] as String? ?? 'Badge';
        final tier = badge['tier'] as String? ?? '';
        final tierDisplay = tier.isNotEmpty
            ? '${tier[0].toUpperCase()}${tier.substring(1)}'
            : '';
        final gems = badge['gems_awarded'] as int? ?? 0;

        return Center(
          child: Material(
            color: Colors.transparent,
            child: Container(
              width: 280,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: KiwiColors.xpPurple.withOpacity(0.2),
                    blurRadius: 24,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(emoji, style: const TextStyle(fontSize: 48)),
                  const SizedBox(height: 12),
                  const Text(
                    'Badge Unlocked!',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.xpPurple,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    tierDisplay.isNotEmpty ? '$emoji $name — $tierDisplay' : '$emoji $name',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: KiwiColors.textDark,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  if (gems > 0) ...[
                    const SizedBox(height: 6),
                    Text(
                      '+$gems gems',
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.gemBlue,
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: KiwiColors.xpPurple,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      child: const Text(
                        'Awesome!',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  void _showLevelUpDialog(Map<String, dynamic> levelUp) {
    final emoji = levelUp['emoji'] as String? ?? '';
    final name = levelUp['name'] as String? ?? 'New Level';

    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'Level Up',
      barrierColor: Colors.black38,
      transitionDuration: const Duration(milliseconds: 300),
      transitionBuilder: (ctx, anim, _, child) {
        return ScaleTransition(
          scale: CurvedAnimation(parent: anim, curve: Curves.elasticOut),
          child: child,
        );
      },
      pageBuilder: (ctx, _, __) {
        return Center(
          child: Material(
            color: Colors.transparent,
            child: Container(
              width: 280,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
                boxShadow: [
                  BoxShadow(
                    color: KiwiColors.kiwiGreen.withOpacity(0.25),
                    blurRadius: 24,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(emoji, style: const TextStyle(fontSize: 56)),
                  const SizedBox(height: 12),
                  const Text(
                    'Level Up!',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.kiwiGreenDark,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "You're now a $name! $emoji",
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: KiwiColors.textDark,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: KiwiColors.kiwiGreen,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                      child: const Text(
                        "Let's go!",
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  void _onCorrectContinue() {
    if (_questionsAnswered >= _totalQuestions) {
      _showSessionComplete();
    } else {
      _fetchNextQuestion();
    }
  }

  void _onWrongContinue() {
    if (_questionsAnswered >= _totalQuestions) {
      _showSessionComplete();
    } else {
      _fetchNextQuestion();
    }
  }

  void _onWhyPressed() {
    final q = _question;
    final result = _lastResult;
    if (q == null) return;

    final correctIdx = result?.correctAnswer ?? q.correctAnswer;
    final selectedIdx = _selectedIndex ?? 0;

    final correctAnswer = correctIdx < q.choices.length
        ? q.choices[correctIdx]
        : 'Answer ${correctIdx + 1}';
    final wrongAnswer = selectedIdx < q.choices.length
        ? q.choices[selectedIdx]
        : 'Your pick';
    final feedback = result?.feedback ?? 'Let\'s understand this better.';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _WhyBottomSheet(
        feedbackMessage: feedback,
        questionStem: q.stem,
        correctAnswer: correctAnswer,
        wrongAnswer: wrongAnswer,
        onDone: () {
          Navigator.of(ctx).pop(); // close sheet
          _onWrongContinue();
        },
      ),
    );
  }

  void _showSessionComplete() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => CelebrationScreen(
          xpEarned: _xp,
          coinsEarned: _coins,
          gemsEarned: _gems,
          currentStreak: _streak,
          dailyRemaining: 0,
          fromStepDown: false,
          correctCount: _correctCount,
          totalQuestions: _totalQuestions,
          companionService: widget.companionService,
          onContinue: () {
            Navigator.of(context).pop();
            if (widget.onBackToHome != null) {
              widget.onBackToHome!();
            } else {
              Navigator.of(context).maybePop();
            }
          },
        ),
      ),
    );
  }

  // -------------------------------------------------------------------
  // Build
  // -------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _tier.colors.background,
      body: SafeArea(
        child: _error != null
            ? _buildError()
            : Column(
                children: [
                  _buildTopBar(),
                  Expanded(child: _buildContent()),
                  _buildBottomBar(),
                ],
              ),
      ),
    );
  }

  /// v3 top bar: back arrow + segmented dots + report flag + XP badge
  Widget _buildTopBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          // Close / back button
          GestureDetector(
            onTap: widget.onBackToHome ?? () => Navigator.of(context).maybePop(),
            child: Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: _tier.colors.primary.withOpacity(0.08),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.close, size: 18, color: _tier.colors.textSecondary),
            ),
          ),
          const SizedBox(width: 12),
          // Segmented progress dots — one per question
          Expanded(child: _buildProgressDots()),
          const SizedBox(width: 8),
          // Report / flag — only shown when a question is loaded
          if (_question != null) ...[
            GestureDetector(
              onTap: _onReportPressed,
              child: Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: _tier.colors.primary.withOpacity(0.08),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.flag_outlined,
                  size: 18,
                  color: _tier.colors.textSecondary,
                ),
              ),
            ),
            const SizedBox(width: 8),
          ],
          // Single stat: XP
          _StatBadge(icon: Icons.bolt, value: '$_xp', color: KiwiColors.xpPurple),
          // Streak fire (only when hot)
          if (_streak >= 2) ...[
            const SizedBox(width: 6),
            _StatBadge(
              icon: Icons.local_fire_department,
              value: '$_streak',
              color: KiwiColors.streakOrange,
            ),
          ],
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Report / flag question (Task #194)
  // -------------------------------------------------------------------

  void _onReportPressed() {
    final q = _question;
    if (q == null) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _ReportQuestionSheet(
        questionId: q.questionId,
        userId: widget.userId,
        api: _api,
      ),
    );
  }

  /// Segmented progress dots: filled = answered, current = pulse, empty = upcoming
  Widget _buildProgressDots() {
    return Row(
      children: List.generate(_totalQuestions, (i) {
        final isAnswered = i < _questionsAnswered;
        final isCurrent = i == _questionsAnswered && _phase != _PhaseV2.loading;

        Color dotColor;
        if (isAnswered) {
          dotColor = _tier.colors.primary;
        } else if (isCurrent) {
          dotColor = _tier.colors.primary.withOpacity(0.4);
        } else {
          dotColor = _tier.colors.primary.withOpacity(0.12);
        }

        return Expanded(
          child: Container(
            height: isCurrent ? 6 : 4,
            margin: EdgeInsets.only(right: i < _totalQuestions - 1 ? 3 : 0),
            decoration: BoxDecoration(
              color: dotColor,
              borderRadius: BorderRadius.circular(3),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildContent() {
    if (_phase == _PhaseV2.loading || _question == null) {
      return const Center(child: CircularProgressIndicator());
    }

    final q = _question!;
    final companionSvc = widget.companionService;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 4),

          // Companion — floats to the right
          if (companionSvc != null && companionSvc.isLoaded)
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: CompanionView(
                  key: _companionKey,
                  surface: _companionSurface,
                  config: companionSvc.config!,
                  size: 48,
                  picoAppearancesInLesson: companionSvc.picoAppearancesInLesson,
                ),
              ),
            ),

          // SVG visual — full width, light-gray bg (Brilliant-style separation)
          if (q.visualSvgUrl != null) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFF3F1EC),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: const Color(0xFFE0DDD6),
                  width: 1.5,
                ),
              ),
              child: Center(
                child: Semantics(
                  label: q.visualAlt ?? 'Question illustration',
                  image: true,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 140),
                    child: SvgPicture.network(
                      _api.visualUrlV2(q.questionId),
                      fit: BoxFit.contain,
                      semanticsLabel: q.visualAlt ?? 'Question illustration',
                      placeholderBuilder: (_) => const SizedBox(
                        height: 60,
                        child: Center(
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                      errorBuilder: (context, error, stackTrace) {
                        final alt = q.visualAlt;
                        if (alt != null && alt.isNotEmpty) {
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.image_outlined,
                                    size: 18, color: Colors.grey.shade400),
                                const SizedBox(width: 8),
                                Flexible(
                                  child: Text(
                                    alt,
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade600,
                                      fontStyle: FontStyle.italic,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),
          ],

          // Stem — clean, large, bold
          Text(
            q.stem,
            style: TextStyle(
              fontSize: _tier.isJunior ? 18 : 16,
              fontWeight: _tier.typography.headlineWeight,
              color: _tier.colors.textPrimary,
              height: 1.45,
            ),
          ),

          // Inline hint steps — Khan Academy style (between stem and options)
          if ((q.solutionSteps.isNotEmpty || q.hintLadder != null) &&
              (_phase == _PhaseV2.answering || _phase == _PhaseV2.selected))
            Padding(
              padding: const EdgeInsets.only(top: 10, bottom: 12),
              child: InlineHintSteps(
                solutionSteps: q.solutionSteps,
                hintLadder: q.hintLadder,
                onStepRevealed: (step) {
                  _maxHintLevel = step > _maxHintLevel ? step : _maxHintLevel;
                },
              ),
            )
          else
            const SizedBox(height: 16),

          // Interaction-mode-specific input
          _buildInteractionWidget(q),

          const SizedBox(height: 16),
        ],
      ),
    );
  }

  /// Dispatch to the correct interaction widget based on question mode.
  Widget _buildInteractionWidget(QuestionV2 q) {
    switch (q.interactionMode) {
      case 'integer':
        return IntegerInput(
          allowNegative: widget.grade >= 4,
          onSubmit: _onIntegerSubmit,
        );
      case 'drag_drop':
        if (q.dragItems != null && q.dragItems!.isNotEmpty) {
          return DragDropTiles(
            items: q.dragItems!,
            onSubmit: _onDragDropSubmit,
          );
        }
        return _buildOptionsGrid(q);
      default:
        return _buildOptionsGrid(q);
    }
  }

  /// 2x2 grid of answer options
  Widget _buildOptionsGrid(QuestionV2 q) {
    final count = q.choices.length;
    // For 2 choices, use a single row. For 3-4, use 2x2 grid.
    if (count <= 2) {
      return Row(
        children: List.generate(count, (i) {
          return Expanded(
            child: Padding(
              padding: EdgeInsets.only(right: i < count - 1 ? 8 : 0),
              child: OptionCard(
                text: q.choices[i],
                index: i,
                state: _optionStateFor(i),
                onTap: () => _onOptionTap(i),
              ),
            ),
          );
        }),
      );
    }

    // 2x2 grid for 3-4 choices
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: OptionCard(
                text: q.choices[0],
                index: 0,
                state: _optionStateFor(0),
                onTap: () => _onOptionTap(0),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OptionCard(
                text: q.choices[1],
                index: 1,
                state: _optionStateFor(1),
                onTap: () => _onOptionTap(1),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OptionCard(
                text: q.choices[2],
                index: 2,
                state: _optionStateFor(2),
                onTap: () => _onOptionTap(2),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: count > 3
                  ? OptionCard(
                      text: q.choices[3],
                      index: 3,
                      state: _optionStateFor(3),
                      onTap: () => _onOptionTap(3),
                    )
                  : const SizedBox.shrink(),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildBottomBar() {
    // Wrong answer — minimal feedback with "Why?" button + encouragement
    if (_phase == _PhaseV2.wrong) {
      return _WrongAnswerSheetV3(
        onWhy: _onWhyPressed,
        onContinue: _onWrongContinue,
        encouragement: _lastResult?.nextAction?['message'] as String?,
      );
    }

    // Correct answer — celebration bar
    if (_phase == _PhaseV2.correct) {
      return _CorrectAnswerBarV3(
        xpEarned: _lastResult?.xpEarned ?? 15,
        coinsEarned: _lastResult?.coinsEarned ?? 0,
        streak: _streak,
        encouragement: _lastResult?.nextAction?['message'] as String?,
        onContinue: _onCorrectContinue,
      );
    }

    // For integer and drag_drop modes, the check button is inside the widget.
    final isNonMcq = _question?.interactionMode == 'integer' ||
        _question?.interactionMode == 'drag_drop';

    // Check answer button (MCQ only)
    if (_phase == _PhaseV2.selected && !isNonMcq) {
      return _buildCheckButton();
    }

    // Submitting
    if (_phase == _PhaseV2.submitting && !isNonMcq) {
      return _buildCheckButton(disabled: true, isLoading: true);
    }

    // Answering — disabled check (MCQ only)
    if (_phase == _PhaseV2.answering && !isNonMcq) {
      return _buildCheckButton(disabled: true);
    }

    return const SizedBox.shrink();
  }

  Widget _buildCheckButton({
    bool disabled = false,
    bool isLoading = false,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: SafeArea(
        top: false,
        child: SizedBox(
          width: double.infinity,
          child: disabled
              ? ElevatedButton(
                  onPressed: null,
                  style: ElevatedButton.styleFrom(
                    disabledBackgroundColor: _tier.colors.primary.withOpacity(0.08),
                    disabledForegroundColor: _tier.colors.primary.withOpacity(0.35),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(_tier.shape.buttonRadius),
                    ),
                    textStyle: TextStyle(
                      fontSize: _tier.typography.buttonSize,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: isLoading
                      ? SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                                _tier.colors.primary.withOpacity(0.4)),
                          ),
                        )
                      : const Text('Pick an answer'),
                )
              : DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        _tier.colors.buttonGradientStart,
                        _tier.colors.buttonGradientEnd,
                      ],
                    ),
                    borderRadius: BorderRadius.circular(_tier.shape.buttonRadius),
                    boxShadow: [
                      BoxShadow(
                        color: _tier.colors.primary.withOpacity(0.35),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: ElevatedButton(
                    onPressed: _onCheckAnswer,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      foregroundColor: Colors.white,
                      shadowColor: Colors.transparent,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(_tier.shape.buttonRadius),
                      ),
                      textStyle: TextStyle(
                        fontSize: _tier.typography.buttonSize,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Check'),
                  ),
                ),
        ),
      ),
    );
  }

  OptionState _optionStateFor(int idx) {
    if (_selectedIndex == null) return OptionState.idle;

    final q = _question;
    if (q == null) return OptionState.idle;

    final correctIdx = _lastResult?.correctAnswer ?? q.correctAnswer;

    // Before checking — just show "selected" highlight
    if (_phase == _PhaseV2.selected || _phase == _PhaseV2.answering) {
      return idx == _selectedIndex ? OptionState.selected : OptionState.idle;
    }

    // After checking — show correct/wrong
    if (idx == _selectedIndex) {
      return idx == correctIdx
          ? OptionState.selectedCorrect
          : OptionState.selectedWrong;
    }
    if (_selectedIndex != correctIdx && idx == correctIdx) {
      return OptionState.selectedCorrect;
    }
    return OptionState.disabled;
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_off, size: 48, color: Colors.grey),
            const SizedBox(height: 16),
            const Text(
              "Can't reach Kiwimath backend",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              _error ?? '',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _fetchNextQuestion,
              child: const Text('Try again'),
            ),
          ],
        ),
      ),
    );
  }
}

// ==========================================================================
// Supporting widgets
// ==========================================================================

class _StatBadge extends StatelessWidget {
  final IconData icon;
  final String value;
  final Color color;

  const _StatBadge({
    required this.icon,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withAlpha(25),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: color),
          const SizedBox(width: 3),
          Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

/// Animated "+XP" toast that floats up near the XP badge.
class _XpToastAnimation extends StatefulWidget {
  final int xp;
  final VoidCallback onDone;

  const _XpToastAnimation({required this.xp, required this.onDone});

  @override
  State<_XpToastAnimation> createState() => _XpToastAnimationState();
}

class _XpToastAnimationState extends State<_XpToastAnimation>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _opacity;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _opacity = TweenSequence<double>([
      TweenSequenceItem(tween: Tween(begin: 0.0, end: 1.0), weight: 20),
      TweenSequenceItem(tween: ConstantTween(1.0), weight: 50),
      TweenSequenceItem(tween: Tween(begin: 1.0, end: 0.0), weight: 30),
    ]).animate(_ctrl);
    _slide = Tween<Offset>(
      begin: const Offset(0, 0),
      end: const Offset(0, -1.5),
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));

    _ctrl.forward().then((_) => widget.onDone());
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    return Positioned(
      top: mq.padding.top + 6,
      right: 60,
      child: SlideTransition(
        position: _slide,
        child: FadeTransition(
          opacity: _opacity,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFAA00FF), Color(0xFF7C4DFF)],
              ),
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFAA00FF).withOpacity(0.5),
                  blurRadius: 12,
                  offset: const Offset(0, 3),
                ),
              ],
            ),
            child: Text(
              '+${widget.xp} XP',
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w800,
                color: Colors.white,
                decoration: TextDecoration.none,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// v3 wrong answer — minimal, with "Why?" button.
///
/// Competitor-inspired: brief text, two clear actions.
/// "Why?" opens the explanation screen for deeper learning.
class _WrongAnswerSheetV3 extends StatelessWidget {
  final VoidCallback onWhy;
  final VoidCallback onContinue;
  final String? encouragement;

  const _WrongAnswerSheetV3({
    required this.onWhy,
    required this.onContinue,
    this.encouragement,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFFF8F0),
        border: const Border(
          top: BorderSide(color: Color(0xFFFFCC80), width: 1.5),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            // Status indicator
            Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: Color(0xFFFFEBEE),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.close, size: 20, color: Color(0xFFEF5350)),
            ),
            const SizedBox(width: 12),
            // Text + encouragement
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Not quite right.',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFBF360C),
                    ),
                  ),
                  if (encouragement != null && encouragement!.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        encouragement!,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFFBF360C),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
              ),
            ),
            // Why? button — the key innovation
            GestureDetector(
              onTap: onWhy,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFFFCC80), width: 1.5),
                ),
                child: const Text(
                  'Why?',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFFE65100),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            // Continue button
            GestureDetector(
              onTap: onContinue,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFF9800), Color(0xFFE65100)],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Got it',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// v3 correct answer — celebration bar with streak emphasis.
class _CorrectAnswerBarV3 extends StatelessWidget {
  final int xpEarned;
  final int coinsEarned;
  final int streak;
  final String? encouragement;
  final VoidCallback onContinue;

  const _CorrectAnswerBarV3({
    required this.xpEarned,
    this.coinsEarned = 0,
    required this.streak,
    this.encouragement,
    required this.onContinue,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF0FFF0),
        border: const Border(
          top: BorderSide(color: Color(0xFF66BB6A), width: 1.5),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            // Green checkmark
            Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: Color(0xFFE8F5E9),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.check, size: 22, color: Color(0xFF00C853)),
            ),
            const SizedBox(width: 12),
            // "Correct!" text with streak + encouragement + rewards
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text(
                        'Correct!',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF2E7D32),
                        ),
                      ),
                      if (streak >= 2) ...[
                        const SizedBox(width: 6),
                        Text(
                          '\u{1F525} $streak in a row!',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFFFF8F00),
                          ),
                        ),
                      ],
                    ],
                  ),
                  // Show encouragement message from Kiwi Brain
                  if (encouragement != null && encouragement!.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        encouragement!,
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: Color(0xFF388E3C),
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  // Coins earned
                  if (coinsEarned > 0)
                    Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text(
                        '+$coinsEarned \u{1FA99}${xpEarned > 0 ? "  +$xpEarned XP" : ""}',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF66BB6A),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            // Continue button
            GestureDetector(
              onTap: onContinue,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF66BB6A), Color(0xFF2E7D32)],
                  ),
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF2E7D32).withOpacity(0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: const Text(
                  'Continue',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ===========================================================================
// Report / Flag Question bottom sheet (Task #194)
// ===========================================================================

class _ReportQuestionSheet extends StatefulWidget {
  final String questionId;
  final String? userId;
  final ApiClient api;

  const _ReportQuestionSheet({
    required this.questionId,
    required this.userId,
    required this.api,
  });

  @override
  State<_ReportQuestionSheet> createState() => _ReportQuestionSheetState();
}

class _ReportQuestionSheetState extends State<_ReportQuestionSheet> {
  String? _selectedType;
  final TextEditingController _commentController = TextEditingController();
  bool _submitting = false;
  bool _submitted = false;

  // Display label, internal flag_type code, emoji
  static const List<List<String>> _options = [
    ['Wrong answer', 'answer_error', '⚠️'],
    ['Hint not helpful', 'hint_not_good', '💡'],
    ['Visual missing', 'visual_missing', '🖼️'],
    ["Visual doesn't match", 'visual_mismatch', '🔀'],
    ['Question has an error', 'question_error', '❓'],
    ['Something else', 'other', '💬'],
  ];

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final type = _selectedType;
    if (type == null) return;
    setState(() => _submitting = true);
    try {
      // Submit to the new flag/submit endpoint for quality tracking.
      await widget.api.flagQuestion(
        questionId: widget.questionId,
        studentId: widget.userId ?? 'anonymous',
        flagType: type,
        comment: _commentController.text,
      );
      if (!mounted) return;
      setState(() {
        _submitting = false;
        _submitted = true;
      });
      // Show a friendly snackbar and auto-dismiss.
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text(
            'Thanks! We\'ll look into it \u{1F64F}',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            textAlign: TextAlign.center,
          ),
          backgroundColor: KiwiColors.kiwiGreen,
          behavior: SnackBarBehavior.floating,
          margin: const EdgeInsets.fromLTRB(40, 0, 40, 100),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          duration: const Duration(seconds: 2),
        ),
      );
      Future.delayed(const Duration(milliseconds: 1100), () {
        if (mounted) Navigator.of(context).maybePop();
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Couldn't send report \u{2014} please try again."),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        child: SafeArea(
          top: false,
          child: _submitted
              ? const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle, size: 48, color: KiwiColors.kiwiGreen),
                      SizedBox(height: 10),
                      Text(
                        'Thanks! We\'ll look into it \u{1F64F}',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: KiwiColors.textDark,
                        ),
                      ),
                    ],
                  ),
                )
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 36,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.grey.shade300,
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text(
                      "What's wrong with this question?",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: KiwiColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ..._options.map((opt) {
                      final label = opt[0];
                      final code = opt[1];
                      final emoji = opt[2];
                      final isSelected = _selectedType == code;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: GestureDetector(
                          onTap: () => setState(() => _selectedType = code),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 14, vertical: 12),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? KiwiColors.kiwiGreenLight
                                  : Colors.grey.shade100,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: isSelected
                                    ? KiwiColors.kiwiGreen
                                    : Colors.transparent,
                                width: 1.5,
                              ),
                            ),
                            child: Row(
                              children: [
                                Text(emoji, style: const TextStyle(fontSize: 18)),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    label,
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w600,
                                      color: isSelected
                                          ? KiwiColors.kiwiGreenDark
                                          : KiwiColors.textDark,
                                    ),
                                  ),
                                ),
                                if (isSelected)
                                  const Icon(Icons.check_circle,
                                      size: 18, color: KiwiColors.kiwiGreen),
                              ],
                            ),
                          ),
                        ),
                      );
                    }),
                    const SizedBox(height: 6),
                    TextField(
                      controller: _commentController,
                      maxLines: 2,
                      maxLength: 200,
                      decoration: InputDecoration(
                        hintText: 'Add a note (optional)',
                        hintStyle: TextStyle(
                          fontSize: 13,
                          color: Colors.grey.shade500,
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10),
                          borderSide: BorderSide(color: Colors.grey.shade300),
                        ),
                        counterText: '',
                      ),
                      style: const TextStyle(fontSize: 13),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed:
                            _selectedType == null || _submitting ? null : _submit,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: KiwiColors.kiwiGreen,
                          foregroundColor: Colors.white,
                          disabledBackgroundColor: Colors.grey.shade300,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          textStyle: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        child: _submitting
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                      Colors.white),
                                ),
                              )
                            : const Text('Send report'),
                      ),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}

/// "Why?" bottom sheet — slides up from the bottom on the same screen.
///
/// Shows the explanation inline instead of navigating to a new page.
/// The kid stays in context and can dismiss by swiping down or tapping "Got it".
class _WhyBottomSheet extends StatelessWidget {
  final String feedbackMessage;
  final String questionStem;
  final String correctAnswer;
  final String wrongAnswer;
  final VoidCallback onDone;

  const _WhyBottomSheet({
    required this.feedbackMessage,
    required this.questionStem,
    required this.correctAnswer,
    required this.wrongAnswer,
    required this.onDone,
  });

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.55,
      minChildSize: 0.3,
      maxChildSize: 0.85,
      builder: (context, scrollController) {
        return Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [
              BoxShadow(
                color: Color(0x1A000000),
                blurRadius: 20,
                offset: Offset(0, -4),
              ),
            ],
          ),
          child: Column(
            children: [
              // Drag handle
              Padding(
                padding: const EdgeInsets.only(top: 12, bottom: 4),
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: const Color(0xFFE0E0E0),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              // Header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Row(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: const BoxDecoration(
                        color: Color(0xFFFFF3E0),
                        shape: BoxShape.circle,
                      ),
                      child: const Center(
                        child: Text('\u{1F4A1}', style: TextStyle(fontSize: 16)),
                      ),
                    ),
                    const SizedBox(width: 10),
                    const Text(
                      'Understanding the answer',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFFE65100),
                      ),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1, color: Color(0xFFF5F5F5)),
              // Content
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(20),
                  children: [
                    // Your answer vs correct answer
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        _buildAnswerChip(wrongAnswer, false),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 10),
                          child: Icon(Icons.arrow_forward,
                              color: Color(0xFFBDBDBD), size: 18),
                        ),
                        _buildAnswerChip(correctAnswer, true),
                      ],
                    ),
                    const SizedBox(height: 18),
                    // Explanation
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFFDE7),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                            color: const Color(0xFFFFF9C4), width: 1.5),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Here\'s why:',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFFF57F17),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            feedbackMessage,
                            style: const TextStyle(
                              fontSize: 14,
                              color: Color(0xFF424242),
                              height: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Question reminder (collapsed)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF5F5F5),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        questionStem,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF757575),
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              // Bottom button
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: SafeArea(
                  top: false,
                  child: SizedBox(
                    width: double.infinity,
                    child: GestureDetector(
                      onTap: onDone,
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFFFF9800), Color(0xFFE65100)],
                          ),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Text(
                          'Got it, next question \u{2192}',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAnswerChip(String text, bool isCorrect) {
    final color =
        isCorrect ? const Color(0xFF2E7D32) : const Color(0xFFEF5350);
    final bg =
        isCorrect ? const Color(0xFFE8F5E9) : const Color(0xFFFFEBEE);
    final icon = isCorrect ? Icons.check : Icons.close;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3), width: 1.5),
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
}
