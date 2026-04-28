import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/companion.dart';
import '../models/question_v2.dart';
import '../services/api_client.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';
import '../widgets/feedback_banner.dart';
import '../widgets/hint_ladder_bar.dart';
import '../widgets/option_card.dart';
import 'celebration_screen.dart';

/// v2 question screen — stateless adaptive practice.
///
/// Uses the v2 API which is simpler than the session-based v1:
///   1. Fetch next question (GET /v2/questions/next)
///   2. Display question with choices
///   3. Check answer (POST /v2/answer/check)
///   4. Adjust difficulty based on response
///   5. Repeat until 10 questions answered
class QuestionScreenV2 extends StatefulWidget {
  final String topicId;
  final String topicName;
  final String? userId;
  final int grade;
  final VoidCallback? onBackToHome;
  final CompanionService? companionService;

  const QuestionScreenV2({
    super.key,
    required this.topicId,
    required this.topicName,
    this.userId,
    this.grade = 1,
    this.onBackToHome,
    this.companionService,
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

  // Grade-adaptive tier for proper theming.
  KiwiTier get _tier => KiwiTier.forGrade(widget.grade);

  // Session state
  _PhaseV2 _phase = _PhaseV2.loading;
  QuestionV2? _question;
  AnswerCheckResponse? _lastResult;
  int? _selectedIndex;
  String? _error;

  // Difficulty tracking — start at easiest (1) and let adaptive engine ramp up
  int _currentDifficulty = 1;

  // Progress tracking
  int _questionsAnswered = 0;
  final int _totalQuestions = 10;
  int _correctCount = 0;
  int _xp = 0;
  int _coins = 0;
  int _gems = 0;
  int _streak = 0;

  // Exclude already-answered question IDs
  final List<String> _excludeIds = [];

  // Track hint usage per question for gamification
  int _maxHintLevel = -1;

  // Time tracking for adaptive engine
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
      final question = await _api.nextQuestionV2(
        topic: widget.topicId,
        difficulty: _currentDifficulty,
        window: 10,
        exclude: _excludeIds.isNotEmpty ? _excludeIds : null,
        userId: widget.userId,
        grade: widget.grade,
      );
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

    // Calculate time taken
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

      // Update counters from API response
      _xp += result.xpEarned;
      _coins += result.coinsEarned;
      _gems += result.gemsEarned;
      _currentDifficulty = (result.nextDifficulty).clamp(1, 100);

      if (result.correct) {
        _correctCount++;
        _streak++;
        setState(() => _phase = _PhaseV2.correct);
        // Trigger companion celebration bounce
        _companionKey.currentState?.playCelebration();
      } else {
        _streak = 0;
        setState(() => _phase = _PhaseV2.wrong);
      }

      // Show gamification events
      _showGamificationEvents(result);
    } catch (e) {
      if (!mounted) return;
      // Roll back to selected so the Check button reappears.
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
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          duration: const Duration(seconds: 4),
        ),
      );
    }
  }

  // -------------------------------------------------------------------
  // Gamification events
  // -------------------------------------------------------------------

  void _showGamificationEvents(AnswerCheckResponse result) {
    // XP toast
    if (result.xpEarned > 0) {
      _showXpToast(result.xpEarned);
    }

    // Micro celebration snackbar
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

    // Badge unlocks
    if (result.badgeUnlocks.isNotEmpty) {
      Future.delayed(const Duration(milliseconds: 800), () {
        if (!mounted) return;
        for (final badge in result.badgeUnlocks) {
          _showBadgeUnlockDialog(badge);
        }
      });
    }

    // Level up
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
        // Auto-dismiss after 3 seconds
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

  void _onTryAgain() {
    setState(() {
      _selectedIndex = null;
      _phase = _PhaseV2.answering;
    });
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
            Navigator.of(context).pop(); // pop celebration
            if (widget.onBackToHome != null) {
              widget.onBackToHome!();
            } else {
              Navigator.of(context).maybePop(); // pop question screen
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
                  _buildDifficultyBar(),
                  Expanded(child: _buildContent()),
                  _buildBottomBar(),
                ],
              ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          // Close / back button
          GestureDetector(
            onTap: widget.onBackToHome ?? () => Navigator.of(context).maybePop(),
            child: const Icon(Icons.close, size: 22, color: KiwiColors.textMuted),
          ),
          const SizedBox(width: 10),
          // Progress bar (question count) — thicker, rounded, gradient feel
          Expanded(
            child: Container(
              height: 10,
              decoration: BoxDecoration(
                color: _tier.colors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(5),
              ),
              child: FractionallySizedBox(
                alignment: Alignment.centerLeft,
                widthFactor: _totalQuestions > 0
                    ? (_questionsAnswered / _totalQuestions).clamp(0.0, 1.0)
                    : 0,
                child: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        _tier.colors.buttonGradientStart,
                        _tier.colors.buttonGradientEnd,
                      ],
                    ),
                    borderRadius: BorderRadius.circular(5),
                    boxShadow: [
                      BoxShadow(
                        color: _tier.colors.primary.withOpacity(0.3),
                        blurRadius: 4,
                        offset: const Offset(0, 1),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Question counter — show as "Q 3/10"
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: _tier.colors.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Q $_questionsAnswered/$_totalQuestions',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: _tier.colors.primaryDark,
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Coin badge
          _StatBadge(icon: Icons.monetization_on, value: '$_coins', color: KiwiColors.gemGold),
          const SizedBox(width: 5),
          // Gem badge
          _StatBadge(icon: Icons.diamond, value: '$_gems', color: KiwiColors.gemBlue),
          const SizedBox(width: 5),
          // XP badge
          _StatBadge(icon: Icons.bolt, value: '$_xp', color: KiwiColors.xpPurple),
          // Streak indicator (only when active)
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

  Widget _buildDifficultyBar() {
    if (_phase == _PhaseV2.loading) return const SizedBox.shrink();

    final tierLabel = _question?.difficultyTier ?? 'easy';
    final diffColor = _difficultyColor(tierLabel);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 0),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              diffColor.withOpacity(0.1),
              diffColor.withOpacity(0.05),
            ],
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: diffColor.withOpacity(0.2)),
        ),
        child: Row(
          children: [
            Icon(Icons.trending_up, size: 14, color: diffColor),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                widget.topicName,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: diffColor,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 8),
            // Difficulty progress bar (1-100) — gradient fill
            SizedBox(
              width: 60,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: _currentDifficulty / 100.0,
                  minHeight: 5,
                  backgroundColor: diffColor.withOpacity(0.12),
                  valueColor: AlwaysStoppedAnimation<Color>(diffColor),
                ),
              ),
            ),
            const SizedBox(width: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: diffColor.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: diffColor.withOpacity(0.3)),
              ),
              child: Text(
                tierLabel,
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w800,
                  color: diffColor,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _difficultyColor(String tier) {
    switch (tier.toLowerCase()) {
      case 'easy':
        return const Color(0xFF00C853);
      case 'medium':
        return const Color(0xFFFF6D00);
      case 'hard':
        return const Color(0xFFFF5252);
      default:
        return const Color(0xFF00C853);
    }
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
          const SizedBox(height: 8),

          // Companion — floats to the right of the topic chip
          if (companionSvc != null && companionSvc.isLoaded)
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: CompanionView(
                  key: _companionKey,
                  surface: _companionSurface,
                  config: companionSvc.config!,
                  size: 56,
                  picoAppearancesInLesson: companionSvc.picoAppearancesInLesson,
                ),
              ),
            ),

          // Topic chip — gradient pill
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  _tier.colors.primary.withOpacity(0.12),
                  _tier.colors.accent.withOpacity(0.08),
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: _tier.colors.primary.withOpacity(0.2),
              ),
            ),
            child: Text(
              q.topicName,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: _tier.colors.primaryDark,
              ),
            ),
          ),
          const SizedBox(height: 10),

          // SVG visual from URL
          if (q.visualSvgUrl != null) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    KiwiColors.visualYellowBg,
                    KiwiColors.visualBlueBg.withOpacity(0.3),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: KiwiColors.visualYellowBorder,
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: KiwiColors.visualYellowBorder.withOpacity(0.2),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Center(
                child: Semantics(
                  label: q.visualAlt ?? 'Question illustration',
                  image: true,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 120),
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
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 14),
          ],

          // Stem
          Text(
            q.stem,
            style: TextStyle(
              fontSize: _tier.isJunior ? 18 : 16,
              fontWeight: _tier.typography.headlineWeight,
              color: _tier.colors.textPrimary,
              height: 1.45,
            ),
          ),
          const SizedBox(height: 14),

          // Choices
          ...List.generate(q.choices.length, (i) {
            return OptionCard(
              text: q.choices[i],
              index: i,
              state: _optionStateFor(i),
              onTap: () => _onOptionTap(i),
            );
          }),

          // Hint ladder button (shown when available and not yet answered)
          if (q.hintLadder != null &&
              (_phase == _PhaseV2.answering || _phase == _PhaseV2.selected))
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Align(
                alignment: Alignment.centerLeft,
                child: HintButton(
                  hintLadder: q.hintLadder!,
                  onHintRevealed: (level) {
                    // Track hint usage for gamification
                    _maxHintLevel = level > _maxHintLevel ? level : _maxHintLevel;
                  },
                ),
              ),
            )
          // Fallback: simple hint text for questions without structured hints
          else if (q.hint != null &&
              (_phase == _PhaseV2.answering || _phase == _PhaseV2.selected))
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFFE3F2FD),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF90CAF9)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.lightbulb_outline,
                        size: 16, color: Color(0xFF1565C0)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        q.hint!,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF1976D2),
                          height: 1.3,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildBottomBar() {
    // Wrong answer sheet
    if (_phase == _PhaseV2.wrong) {
      final result = _lastResult;
      final feedback = result?.feedback ?? 'Think about the problem again.';
      final correctIdx = result?.correctAnswer ?? _question?.correctAnswer ?? 0;
      final correctChoice = _question != null && correctIdx < _question!.choices.length
          ? _question!.choices[correctIdx]
          : '';

      return _WrongAnswerSheetV2(
        feedback: feedback,
        correctAnswer: correctChoice,
        onTryAgain: _onTryAgain,
        onNext: _onWrongContinue,
      );
    }

    // Correct answer bar
    if (_phase == _PhaseV2.correct) {
      return CorrectAnswerBar(
        xpEarned: _lastResult?.xpEarned ?? 15,
        streak: _streak,
        onContinue: _onCorrectContinue,
      );
    }

    // Check answer button
    if (_phase == _PhaseV2.selected) {
      return _buildCheckButton();
    }

    // Submitting — show spinner
    if (_phase == _PhaseV2.submitting) {
      return _buildCheckButton(disabled: true, isLoading: true);
    }

    // Answering state — disabled check button
    if (_phase == _PhaseV2.answering) {
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
                    disabledBackgroundColor: const Color(0xFFE8E8E8),
                    disabledForegroundColor: const Color(0xFFAAAAAA),
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
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Color(0xFFAAAAAA)),
                          ),
                        )
                      : const Text('Check answer'),
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
                    child: const Text('Check answer'),
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

/// Animated "+XP" toast that floats up near the top-right XP badge.
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
    // Position near the top-right where the XP badge sits
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

/// v2-specific wrong answer sheet — shows correct answer and diagnostic feedback.
class _WrongAnswerSheetV2 extends StatelessWidget {
  final String feedback;
  final String correctAnswer;
  final VoidCallback onTryAgain;
  final VoidCallback onNext;

  const _WrongAnswerSheetV2({
    required this.feedback,
    required this.correctAnswer,
    required this.onTryAgain,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: KiwiColors.warmOrangeBg,
        border: Border(top: BorderSide(color: KiwiColors.warmOrange, width: 2)),
      ),
      padding: const EdgeInsets.all(14),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Title row
            Row(
              children: [
                const Text('\u{1F914}', style: TextStyle(fontSize: 22)),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Not quite!',
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.warmOrangeDark,
                      fontSize: 15,
                    ),
                  ),
                ),
                // Show correct answer badge
                if (correctAnswer.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: KiwiColors.kiwiGreenLight,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: KiwiColors.kiwiGreen),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.check, size: 14, color: KiwiColors.kiwiGreenDark),
                        const SizedBox(width: 4),
                        ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 120),
                          child: Text(
                            correctAnswer,
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: KiwiColors.kiwiGreenDark,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            // Diagnostic feedback
            Text(
              feedback,
              style: const TextStyle(
                fontSize: 12,
                color: Color(0xFFBF360C),
                height: 1.3,
              ),
            ),
            const SizedBox(height: 10),
            // Action buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onTryAgain,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: KiwiColors.warmOrangeDark,
                      side: const BorderSide(color: Color(0xFFFFB74D), width: 2),
                      padding: const EdgeInsets.symmetric(vertical: 11),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      textStyle: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Try again'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: onNext,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: KiwiColors.warmOrange,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 11),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      elevation: 2,
                      shadowColor: KiwiColors.warmOrange.withAlpha(77),
                      textStyle: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Next question \u2192'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
