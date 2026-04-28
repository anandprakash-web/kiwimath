import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/session_response.dart';
import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/feedback_banner.dart';
import '../widgets/option_card.dart';
import '../widgets/svg_visual.dart';
import 'celebration_screen.dart';
import 'explanation_screen.dart';

/// v3 question screen — server-driven adaptive loop.
///
/// The server owns all adaptive logic (step-down routing, mastery, concept
/// switching). The client just:
///   1. Starts a session (POST /session/start)
///   2. Displays questions the server gives
///   3. Submits answers (POST /session/answer)
///   4. Shows the appropriate feedback and transitions
///
/// Flow:
///   start session → show question → check answer → feedback → next question
///   Server decides: parent vs step-down, mastery updates, session end.
class QuestionScreen extends StatefulWidget {
  final String conceptId;
  final String userId;
  final String locale;
  final VoidCallback? onBackToHome;

  const QuestionScreen({
    super.key,
    required this.conceptId,
    this.userId = 'demo-user',
    this.locale = 'global',
    this.onBackToHome,
  });

  @override
  State<QuestionScreen> createState() => _QuestionScreenState();
}

enum _Phase {
  loading,
  answering,        // question on screen, no selection
  selected,         // option tapped, waiting for "Check"
  submitting,       // answer submitted, waiting for server
  correct,          // correct answer bar showing
  wrong,            // wrong answer sheet showing
  sessionComplete,  // session done, showing stats
}

class _QuestionScreenState extends State<QuestionScreen> {
  final ApiClient _api = ApiClient();

  /// Infer grade from concept ID (e.g. "g1.counting" → 1).
  int get _grade {
    final match = RegExp(r'^g(\d)\.').firstMatch(widget.conceptId);
    return match != null ? int.parse(match.group(1)!) : 1;
  }

  KiwiTier get _tier => KiwiTier.forGrade(_grade);

  // Session state
  String? _sessionId;
  _Phase _phase = _Phase.loading;
  SessionQuestion? _question;
  bool _isStepDown = false;
  int? _selectedIndex;
  String? _error;

  // The server response from the last answer — contains the NEXT question
  // and feedback. We hold it here so we can show feedback first, then
  // transition to the next question.
  SessionResponse? _lastResponse;

  // Timing: how long the kid takes on each question
  final Stopwatch _questionTimer = Stopwatch();

  // Gamification — now powered by server rewards on session complete.
  int _streak = 0;
  int _gems = 0;
  int _xp = 0;
  int _questionsAnswered = 0;
  final int _dailyGoal = 5;

  // Server-provided rewards on session complete.
  Map<String, dynamic>? _sessionRewards;

  // Progress tracking
  int _questionNumber = 0;
  int _totalParentQuestions = 0;
  final int _questionsPerSession = 12; // server caps at 12 too

  // Mastery display
  Map<String, dynamic>? _masterySnapshot;

  @override
  void initState() {
    super.initState();
    _startSession();
  }

  // -------------------------------------------------------------------
  // Session lifecycle
  // -------------------------------------------------------------------

  Future<void> _startSession() async {
    setState(() {
      _phase = _Phase.loading;
      _question = null;
      _sessionId = null;
      _error = null;
      _questionNumber = 0;
      _totalParentQuestions = 0;
    });

    try {
      final response = await _api.startSession(
        userId: widget.userId,
        conceptId: widget.conceptId,
      );
      if (!mounted) return;

      _sessionId = response.sessionId;
      _masterySnapshot = response.masterySnapshot;
      _showQuestion(response.question, response.isStepDown);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  /// Display a question from a server response.
  void _showQuestion(SessionQuestion? question, bool isStepDown) {
    if (question == null) {
      // Shouldn't happen unless session is complete.
      setState(() => _phase = _Phase.sessionComplete);
      return;
    }

    _questionNumber++;
    if (!isStepDown) _totalParentQuestions++;

    setState(() {
      _question = question;
      _isStepDown = isStepDown;
      _selectedIndex = null;
      _lastResponse = null;
      _phase = _Phase.answering;
    });

    _questionTimer.reset();
    _questionTimer.start();
  }

  // -------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------

  void _onOptionTap(int index) {
    if (_phase != _Phase.answering && _phase != _Phase.selected) return;
    setState(() {
      _selectedIndex = index;
      _phase = _Phase.selected;
    });
  }

  Future<void> _onCheckAnswer() async {
    final q = _question;
    if (q == null || _selectedIndex == null || _sessionId == null) return;

    _questionTimer.stop();
    final isCorrect = _selectedIndex == q.correctIndex;

    // Show visual feedback immediately (we know correct/wrong from correctIndex).
    setState(() => _phase = _Phase.submitting);

    try {
      final response = await _api.submitAnswer(
        sessionId: _sessionId!,
        questionId: q.questionId,
        selectedOptionIndex: _selectedIndex!,
        timeTakenMs: _questionTimer.elapsedMilliseconds,
      );
      if (!mounted) return;

      _lastResponse = response;
      _masterySnapshot = response.masterySnapshot ?? _masterySnapshot;

      if (isCorrect) {
        _streak++;
        _questionsAnswered++;
        final xpGain = _isStepDown ? 5 : 15;
        final gemGain = _isStepDown ? 2 : 5;
        _xp += xpGain;
        _gems += gemGain;

        if (response.sessionComplete) {
          _sessionRewards = response.rewards;
          setState(() => _phase = _Phase.sessionComplete);
        } else {
          setState(() => _phase = _Phase.correct);
        }
      } else {
        _streak = 0;
        setState(() => _phase = _Phase.wrong);
      }
    } catch (e) {
      if (!mounted) return;
      // Network error during answer submission — show inline retry instead of
      // a full error screen so the kid doesn't lose their place.
      _showSubmitRetrySnackbar(q, isCorrect);
    }
  }

  /// Called after showing "Correct!" bar — advance to next question.
  void _onCorrectContinue() {
    final resp = _lastResponse;
    if (resp == null) return;

    if (resp.sessionComplete) {
      _showSessionComplete();
      return;
    }

    final xpEarned = _isStepDown ? 5 : 15;
    final gemsEarned = _isStepDown ? 2 : 5;

    // If this was a step-down correct and the next question is back to parent,
    // show the "You figured it out!" celebration.
    if (_isStepDown && !resp.isStepDown && resp.question != null) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => CelebrationScreen(
            xpEarned: 10,
            gemsEarned: 2,
            currentStreak: _streak,
            dailyRemaining: (_dailyGoal - _questionsAnswered).clamp(0, _dailyGoal),
            fromStepDown: true,
            onContinue: () {
              Navigator.of(context).pop();
              _showQuestion(resp.question, resp.isStepDown);
            },
          ),
        ),
      );
      return;
    }

    // For parent correct or continuing step-downs, show celebration then next.
    if (!_isStepDown) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => CelebrationScreen(
            xpEarned: xpEarned,
            gemsEarned: gemsEarned,
            currentStreak: _streak,
            dailyRemaining: (_dailyGoal - _questionsAnswered).clamp(0, _dailyGoal),
            fromStepDown: false,
            onContinue: () {
              Navigator.of(context).pop();
              _showQuestion(resp.question, resp.isStepDown);
            },
          ),
        ),
      );
    } else {
      // Step-down correct, more step-downs coming — just advance.
      _showQuestion(resp.question, resp.isStepDown);
    }
  }

  /// Called from wrong-answer sheet: "Help me learn" → explanation → next.
  void _onHelpMeLearn() {
    final resp = _lastResponse;
    final q = _question;
    if (resp == null || q == null || _selectedIndex == null) return;

    final wrongAnswer = q.options[_selectedIndex!].text;
    final correctAnswer = q.options[q.correctIndex].text;
    final feedback = resp.feedbackMessage ?? "Let's break this down step by step.";

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ExplanationScreen(
          feedbackMessage: feedback,
          questionStem: q.stem,
          correctAnswer: correctAnswer,
          wrongAnswer: wrongAnswer,
          onDone: () {
            Navigator.of(context).pop();
            // Show the next question from the server response.
            if (resp.sessionComplete) {
              _sessionRewards = resp.rewards;
              setState(() => _phase = _Phase.sessionComplete);
            } else {
              _showQuestion(resp.question, resp.isStepDown);
            }
          },
        ),
      ),
    );
  }

  /// Called from wrong-answer sheet "Try again" when [retrySameQuestion] is
  /// true. Re-presents the same question without advancing.
  void _onScaffoldRetry() {
    setState(() {
      _selectedIndex = null;
      _phase = _Phase.answering;
    });
    _questionTimer.reset();
    _questionTimer.start();
  }

  /// Called from wrong-answer sheet: "Try again" — re-show same question
  /// without re-submitting. The server has already recorded the wrong answer.
  void _onTryAgain() {
    setState(() {
      _selectedIndex = null;
      _phase = _Phase.answering;
    });
    _questionTimer.reset();
    _questionTimer.start();
  }

  /// Show a non-blocking snackbar on submit failure so the child can retry
  /// without losing their place (no full error screen).
  void _showSubmitRetrySnackbar(SessionQuestion q, bool isCorrect) {
    setState(() {
      // Roll back to the selected state so the Check button reappears.
      _phase = _Phase.selected;
    });
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

  void _showSessionComplete() {
    final resp = _lastResponse;
    final stats = resp?.sessionStats;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => CelebrationScreen(
          xpEarned: _xp,
          gemsEarned: _gems,
          currentStreak: _streak,
          dailyRemaining: (_dailyGoal - _questionsAnswered).clamp(0, _dailyGoal),
          fromStepDown: false,
          onContinue: () {
            Navigator.of(context).pop();
            // Go back to home screen.
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
  // Session goal helpers
  // -------------------------------------------------------------------

  /// Generate a friendly display name from the concept_id.
  /// e.g. "K-ADD-WITHIN10" → "Learn Addition within 10"
  String _friendlyConceptName(String conceptId) {
    final parts = conceptId.split('-');
    String topic = 'Practice';
    String qualifier = '';

    if (parts.length >= 2) {
      switch (parts[1].toUpperCase()) {
        case 'COUNT': topic = 'Counting'; break;
        case 'ARITH': topic = 'Arithmetic'; break;
        case 'ADD': topic = 'Addition'; break;
        case 'SUB': topic = 'Subtraction'; break;
        case 'MUL': topic = 'Multiplication'; break;
        case 'DIV': topic = 'Division'; break;
        case 'SHAPE': topic = 'Shapes'; break;
        case 'PATT': topic = 'Patterns'; break;
        case 'MEAS': topic = 'Measurement'; break;
        case 'SPATIAL': topic = 'Spatial Reasoning'; break;
        case 'LOGIC': topic = 'Logic'; break;
        default: topic = parts[1]; break;
      }
    }
    if (parts.length >= 3) {
      // Convert "WITHIN10" → "within 10", "TO20" → "to 20", etc.
      qualifier = parts.sublist(2).join(' ').replaceAllMapped(
        RegExp(r'(\D)(\d)'),
        (m) => '${m.group(1)} ${m.group(2)}',
      ).toLowerCase();
    }

    return qualifier.isNotEmpty ? 'Learn $topic $qualifier' : 'Learn $topic';
  }

  /// Small session-goal bar with concept name and mastery progress.
  Widget _buildSessionGoalBar() {
    if (_phase == _Phase.loading) return const SizedBox.shrink();

    final snapshot = _masterySnapshot;
    final shownScore = (snapshot?['shown_score'] as num?)?.toDouble() ?? 0;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 0),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: KiwiColors.kiwiGreenLight,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            const Icon(Icons.flag, size: 14, color: KiwiColors.kiwiGreenDark),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                _friendlyConceptName(widget.conceptId),
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.kiwiGreenDark,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 8),
            // Compact mastery progress indicator
            SizedBox(
              width: 60,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(
                  value: shownScore / 100.0,
                  minHeight: 4,
                  backgroundColor: const Color(0xFFC8E6C9),
                  valueColor: const AlwaysStoppedAnimation<Color>(KiwiColors.kiwiGreen),
                ),
              ),
            ),
            const SizedBox(width: 4),
            Text(
              '${shownScore.toInt()}%',
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: KiwiColors.kiwiGreenDark,
              ),
            ),
          ],
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
                  _buildSessionGoalBar(),
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
          // Progress bar
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                value: _questionsPerSession > 0
                    ? (_totalParentQuestions / _questionsPerSession).clamp(0.0, 1.0)
                    : 0,
                minHeight: _tier.isJunior ? 8 : 6,
                backgroundColor: _tier.colors.primary.withOpacity(0.12),
                valueColor: AlwaysStoppedAnimation<Color>(_tier.colors.primary),
              ),
            ),
          ),
          const SizedBox(width: 10),
          // Question counter
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: _tier.colors.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Q $_totalParentQuestions/$_questionsPerSession',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: _tier.colors.primaryDark,
              ),
            ),
          ),
          const SizedBox(width: 8),
          // XP badge
          _StatBadge(icon: Icons.bolt, value: '$_xp', color: KiwiColors.xpPurple),
          const SizedBox(width: 6),
          // Gem badge
          _StatBadge(icon: Icons.diamond, value: '$_gems', color: KiwiColors.gemBlue),
          // Step-down indicator
          if (_isStepDown && _phase != _Phase.loading)
            Padding(
              padding: const EdgeInsets.only(left: 8),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: KiwiColors.warmOrangeBg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Text(
                  'Step-down',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.warmOrangeDark,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_phase == _Phase.loading || _question == null) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_phase == _Phase.sessionComplete) {
      return _buildSessionComplete();
    }

    final q = _question!;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 4),

          // Step-down header
          if (_isStepDown) _buildStepDownHeader(),

          // Topic chip (for parent questions)
          if (!_isStepDown)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiGreenLight,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                _topicFromId(q.questionId),
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.kiwiGreenDark,
                ),
              ),
            ),

          if (!_isStepDown) const SizedBox(height: 10),

          // Visual
          if (q.visual != null) ...[
            Builder(builder: (context) {
              final visualWidget = KiwiVisualWidget(sessionVisual: q.visual);
              if (!visualWidget.hasContent) return const SizedBox.shrink();
              return Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: KiwiColors.visualYellowBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: KiwiColors.visualYellowBorder,
                      width: 1.5,
                    ),
                  ),
                  child: Center(child: visualWidget),
                ),
              );
            }),
          ],

          // Dev debug overlay — only in debug builds
          if (kDebugMode) _buildDebugOverlay(q),

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

          // Options
          ...List.generate(q.options.length, (i) {
            return OptionCard(
              text: q.options[i].text,
              index: i,
              state: _optionStateFor(i),
              onTap: () => _onOptionTap(i),
            );
          }),

          const SizedBox(height: 16),

          // Mastery indicator
          if (_masterySnapshot != null && !_isStepDown) _buildMasteryBar(),
        ],
      ),
    );
  }

  /// Dev-only debug overlay — shows question ID, generator, params, correct answer.
  /// Only visible in debug builds. Helps QA testers catch visual mismatches.
  Widget _buildDebugOverlay(SessionQuestion q) {
    final visual = q.visual;
    final genInfo = visual?.kind == 'svg_inline'
        ? 'SVG (server-rendered)'
        : visual?.kind ?? 'none';
    final altText = visual?.altText ?? '';
    final correctIdx = q.correctIndex;
    final correctText = correctIdx >= 0 && correctIdx < q.options.length
        ? q.options[correctIdx].text
        : '?';

    // Extract relevant params
    final paramsStr = q.paramsUsed.entries
        .where((e) => e.value is int || e.value is double)
        .map((e) => '${e.key}=${e.value}')
        .join(', ');

    return GestureDetector(
      onTap: () {
        // Tap to copy payload to clipboard for bug reports
        debugPrint('QA_DEBUG: ${q.questionId} | answer=$correctText | params={$paramsStr}');
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: const Color(0x15FF6600),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0x30FF6600)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'QA: ${q.questionId}',
              style: const TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w700,
                color: Color(0xFFCC5500),
                fontFamily: 'monospace',
              ),
            ),
            Text(
              'Visual: $genInfo | Answer: $correctText',
              style: const TextStyle(
                fontSize: 9,
                color: Color(0xFFCC5500),
                fontFamily: 'monospace',
              ),
            ),
            if (paramsStr.isNotEmpty)
              Text(
                'Params: $paramsStr',
                style: const TextStyle(
                  fontSize: 9,
                  color: Color(0xFFCC5500),
                  fontFamily: 'monospace',
                ),
              ),
            if (altText.isNotEmpty)
              Text(
                'Alt: $altText',
                style: const TextStyle(
                  fontSize: 8,
                  color: Color(0xAA996633),
                  fontFamily: 'monospace',
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepDownHeader() {
    final mascot = _lastResponse?.mascotEmotion ?? 'thinking';
    final emoji = _mascotEmoji(mascot);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [KiwiColors.visualYellowBg, KiwiColors.warmOrangeBg],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: KiwiColors.warmOrangeBorder),
      ),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 18)),
          const SizedBox(width: 8),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  "Let's break it down",
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.warmOrangeDark,
                    fontSize: 13,
                  ),
                ),
                SizedBox(height: 1),
                Text(
                  'Working through it step by step',
                  style: TextStyle(fontSize: 10, color: Color(0xFFBF360C)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMasteryBar() {
    final snapshot = _masterySnapshot;
    if (snapshot == null) return const SizedBox.shrink();

    // Look for the current concept's mastery in the snapshot.
    final shownScore = (snapshot['shown_score'] as num?)?.toInt() ?? 0;
    final label = (snapshot['mastery_label'] as String?) ?? 'new';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                'Mastery: ${_capitalize(label)}',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textMuted,
                ),
              ),
              const Spacer(),
              Text(
                '$shownScore%',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.kiwiGreenDark,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: shownScore / 100.0,
              minHeight: 5,
              backgroundColor: KiwiColors.kiwiGreenLight,
              valueColor: const AlwaysStoppedAnimation<Color>(KiwiColors.kiwiGreen),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionComplete() {
    final stats = _lastResponse?.sessionStats;
    final mastered = _lastResponse?.conceptMastered ?? false;
    final nextConcept = _lastResponse?.suggestNextConcept;
    final rewards = _sessionRewards;
    final xpEarned = rewards?['xp_earned'] as int? ?? _xp;
    final gemsEarned = rewards?['gems_earned'] as int? ?? 0;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              mastered ? Icons.emoji_events : Icons.star,
              size: 64,
              color: mastered ? KiwiColors.gemGold : KiwiColors.kiwiGreen,
            ),
            const SizedBox(height: 16),
            Text(
              mastered ? 'Concept Mastered!' : 'Session Complete!',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: KiwiColors.kiwiGreenDark,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              mastered
                  ? 'Amazing work! You\'ve mastered this concept.'
                  : 'Great practice session! Keep it up.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 14,
                color: Color(0xFF558B2F),
                height: 1.5,
              ),
            ),

            // Rewards row (XP + Gems earned).
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _rewardChip('\u26A1', '+$xpEarned XP', KiwiColors.xpPurple),
                const SizedBox(width: 12),
                _rewardChip('\u{1F48E}', '+$gemsEarned', KiwiColors.gemBlue),
              ],
            ),

            if (stats != null) ...[
              const SizedBox(height: 16),
              _buildStatsGrid(stats),
            ],
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  if (widget.onBackToHome != null) {
                    widget.onBackToHome!();
                  } else {
                    Navigator.of(context).maybePop();
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: KiwiColors.kiwiGreen,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: const Text(
                  'Back to home',
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _rewardChip(String icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(icon, style: const TextStyle(fontSize: 16)),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatsGrid(Map<String, dynamic> stats) {
    final items = <_StatItem>[];
    if (stats['total_questions'] != null) {
      items.add(_StatItem('Questions', '${stats['total_questions']}'));
    }
    if (stats['correct_count'] != null) {
      items.add(_StatItem('Correct', '${stats['correct_count']}'));
    }
    if (stats['accuracy_pct'] != null) {
      items.add(_StatItem('Accuracy', '${stats['accuracy_pct']}%'));
    }
    if (stats['step_downs_triggered'] != null) {
      items.add(_StatItem('Step-downs', '${stats['step_downs_triggered']}'));
    }

    if (items.isEmpty) return const SizedBox.shrink();

    return Wrap(
      spacing: 12,
      runSpacing: 8,
      alignment: WrapAlignment.center,
      children: items.map((item) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: KiwiColors.kiwiGreenLight,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Text(
                item.value,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.kiwiGreenDark,
                ),
              ),
              Text(
                item.label,
                style: const TextStyle(
                  fontSize: 11,
                  color: KiwiColors.textMuted,
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildBottomBar() {
    // Wrong answer sheet
    if (_phase == _Phase.wrong) {
      final resp = _lastResponse;
      final hint = resp?.feedbackMessage ?? 'Think about the problem again.';
      final hasStepDown = resp?.question != null && (resp?.isStepDown ?? false);
      final retrySame = resp?.retrySameQuestion ?? false;
      final scaffoldLvl = resp?.scaffoldLevel ?? 0;

      // At scaffold level 3+ with a step-down available, auto-route to the
      // step-down — no more "Try again" option (the child already tried 3×).
      final bool forceStepDown = hasStepDown && scaffoldLvl >= 3;

      return WrongAnswerSheet(
        hint: hint,
        retrySameQuestion: forceStepDown ? false : retrySame,
        scaffoldLevel: scaffoldLvl,
        showTryAgain: !forceStepDown,
        onTryAgain: forceStepDown
            ? _onHelpMeLearn
            : (retrySame ? _onScaffoldRetry : _onTryAgain),
        onHelpMeLearn: hasStepDown ? _onHelpMeLearn : () {
          // No step-downs available — just advance to next question.
          if (resp != null && !resp.sessionComplete && resp.question != null) {
            _showQuestion(resp.question, resp.isStepDown);
          } else if (resp != null && resp.sessionComplete) {
            setState(() => _phase = _Phase.sessionComplete);
          }
        },
      );
    }

    // Correct answer bar
    if (_phase == _Phase.correct) {
      return CorrectAnswerBar(
        xpEarned: _isStepDown ? 5 : 15,
        onContinue: _onCorrectContinue,
      );
    }

    // Check answer button
    if (_phase == _Phase.selected) {
      return _buildCheckButton(isStepDown: _isStepDown);
    }

    // Submitting — show spinner in check button
    if (_phase == _Phase.submitting) {
      return _buildCheckButton(disabled: true, isStepDown: _isStepDown, isLoading: true);
    }

    // Answering state — disabled check button
    if (_phase == _Phase.answering) {
      return _buildCheckButton(disabled: true, isStepDown: _isStepDown);
    }

    return const SizedBox.shrink();
  }

  Widget _buildCheckButton({
    bool disabled = false,
    bool isStepDown = false,
    bool isLoading = false,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFFF0F0F0))),
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: disabled ? null : _onCheckAnswer,
            style: ElevatedButton.styleFrom(
              backgroundColor: disabled
                  ? const Color(0xFFE0E0E0)
                  : isStepDown
                      ? KiwiColors.warmOrange
                      : _tier.colors.primary,
              foregroundColor: disabled ? const Color(0xFF999999) : Colors.white,
              disabledBackgroundColor: const Color(0xFFE0E0E0),
              disabledForegroundColor: const Color(0xFF999999),
              padding: EdgeInsets.symmetric(vertical: _tier.isJunior ? 16 : 13),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(_tier.shape.buttonRadius),
              ),
              elevation: disabled ? 0 : 2,
              shadowColor: disabled
                  ? Colors.transparent
                  : isStepDown
                      ? KiwiColors.warmOrange.withAlpha(77)
                      : _tier.colors.primary.withAlpha(77),
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
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF999999)),
                    ),
                  )
                : Text(isStepDown ? 'Check' : 'Check answer'),
          ),
        ),
      ),
    );
  }

  OptionState _optionStateFor(int idx) {
    if (_selectedIndex == null) return OptionState.idle;

    final correctIdx = _question!.correctIndex;

    // Before checking — just show "selected" highlight
    if (_phase == _Phase.selected || _phase == _Phase.answering) {
      return idx == _selectedIndex ? OptionState.selected : OptionState.idle;
    }

    // When the kid will retry (scaffold levels 1-2), do NOT reveal the
    // correct answer — only mark their wrong choice in red.
    final willRetry = _lastResponse?.retrySameQuestion ?? false;

    // After checking (submitting, correct, wrong) — show correct/wrong
    if (idx == _selectedIndex) {
      return idx == correctIdx
          ? OptionState.selectedCorrect
          : OptionState.selectedWrong;
    }
    // Only reveal the correct answer if the kid is NOT retrying.
    if (!willRetry && _selectedIndex != correctIdx && idx == correctIdx) {
      return OptionState.selectedCorrect;
    }
    return willRetry ? OptionState.idle : OptionState.disabled;
  }

  String _topicFromId(String id) {
    final parts = id.split('-');
    if (parts.length >= 2) {
      switch (parts[1]) {
        case 'COUNT': return 'Counting';
        case 'ARITH': return 'Arithmetic';
        case 'ADD': return 'Addition';
        case 'SUB': return 'Subtraction';
        case 'SHAPE': return 'Shapes';
        case 'PATT': return 'Patterns';
        case 'MEAS': return 'Measurement';
        case 'SPATIAL': return 'Spatial';
        case 'LOGIC': return 'Logic';
      }
    }
    return 'Practice';
  }

  String _mascotEmoji(String emotion) {
    switch (emotion) {
      case 'happy': return '\u{1F60A}';
      case 'celebrating': return '\u{1F389}';
      case 'thinking': return '\u{1F914}';
      case 'confused': return '\u{1F615}';
      case 'encouraging': return '\u{1F4AA}';
      case 'proud': return '\u{1F31F}';
      default: return '\u{1F95D}'; // kiwi
    }
  }

  String _capitalize(String s) =>
      s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);

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
              onPressed: _startSession,
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

class _StatItem {
  final String label;
  final String value;
  const _StatItem(this.label, this.value);
}
