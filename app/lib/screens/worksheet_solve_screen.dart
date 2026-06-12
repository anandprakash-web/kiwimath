import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/olympiad_worksheet.dart';
import '../services/api_client.dart';
import '../services/worksheet_cache.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/authed_svg.dart';
import '../widgets/drag_drop_tiles.dart';
import '../widgets/fill_up_input.dart';
import '../widgets/integer_input.dart';
import '../widgets/match_column_widget.dart';
import '../widgets/option_card.dart';

/// Worksheet solve screen — one question at a time.
///
/// Supports all 5 interaction modes: mcq, integer, fill_up, drag_drop, match_column.
/// Shows SVG visuals, approach/explanation after answering, progress bar at top.
class WorksheetSolveScreen extends StatefulWidget {
  final int grade;
  final int day;
  final void Function(WorksheetResult result)? onComplete;

  /// Optional pre-loaded worksheet (for v2 pillar flow).
  /// When provided, skips the API fetch and uses this directly.
  final OlympiadWorksheet? worksheet;

  /// Optional user ID for progress tracking (v2 pillar flow).
  final String? userId;

  const WorksheetSolveScreen({
    super.key,
    required this.grade,
    this.day = 0,
    this.onComplete,
    this.worksheet,
    this.userId,
  });

  @override
  State<WorksheetSolveScreen> createState() => _WorksheetSolveScreenState();
}

enum _Phase { loading, answering, correct, wrong, complete }

class _WorksheetSolveScreenState extends State<WorksheetSolveScreen>
    with SingleTickerProviderStateMixin {
  final _api = ApiClient();
  final _cache = WorksheetCache.instance;
  KiwiTier get _tier => KiwiTier.forGrade(widget.grade);

  OlympiadWorksheet? _worksheet;
  _Phase _phase = _Phase.loading;
  String? _error;

  int _currentIndex = 0;
  int _correctCount = 0;
  bool _showApproach = false;
  final Stopwatch _stopwatch = Stopwatch();

  // Animation
  late AnimationController _slideController;
  late Animation<Offset> _slideAnimation;

  OlympiadQuestion? get _currentQuestion =>
      _worksheet != null && _currentIndex < _worksheet!.questions.length
          ? _worksheet!.questions[_currentIndex]
          : null;

  int get _totalQuestions => _worksheet?.questions.length ?? 12;

  @override
  void initState() {
    super.initState();
    _slideController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(1, 0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _slideController,
      curve: Curves.easeOut,
    ));
    _loadWorksheet();
  }

  @override
  void dispose() {
    _slideController.dispose();
    _stopwatch.stop();
    super.dispose();
  }

  Future<void> _loadWorksheet() async {
    try {
      // v2 pillar flow — use pre-loaded worksheet
      if (widget.worksheet != null) {
        if (mounted) {
          setState(() {
            _worksheet = widget.worksheet;
            _phase = _Phase.answering;
            _stopwatch.start();
          });
        }
        return;
      }
      final ws = await _cache.getWorksheet(widget.grade, widget.day);
      if (mounted) {
        setState(() {
          _worksheet = ws;
          _phase = _Phase.answering;
        });
        _stopwatch.start();
        _slideController.forward(from: 0);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _phase = _Phase.loading;
        });
      }
    }
  }

  void _onAnswer(bool correct) {
    HapticFeedback.mediumImpact();
    if (correct) _correctCount++;
    setState(() {
      _phase = correct ? _Phase.correct : _Phase.wrong;
      _showApproach = false;
    });
  }

  void _nextQuestion() {
    if (_currentIndex + 1 >= _totalQuestions) {
      _onComplete();
      return;
    }
    setState(() {
      _currentIndex++;
      _phase = _Phase.answering;
      _showApproach = false;
    });
    _slideController.forward(from: 0);
  }

  void _onComplete() {
    _stopwatch.stop();
    final stars = _correctCount >= 11
        ? 3
        : _correctCount >= 8
            ? 2
            : _correctCount >= 5
                ? 1
                : 0;
    final result = WorksheetResult(
      correctCount: _correctCount,
      totalCount: _totalQuestions,
      timeSeconds: _stopwatch.elapsed.inSeconds,
      completedAt: DateTime.now(),
      stars: stars,
    );
    _cache.saveResult(widget.grade, widget.day, result);
    widget.onComplete?.call(result);
    setState(() => _phase = _Phase.complete);
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.grade);
    final colors = tier.colors;
    final typo = tier.typography;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: _buildContent(colors, typo),
      ),
    );
  }

  Widget _buildContent(KiwiTierColors colors, KiwiTierTypography typo) {
    if (_phase == _Phase.loading) {
      if (_error != null) {
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: KiwiColors.coral),
              const SizedBox(height: 12),
              Text('Failed to load worksheet',
                  style: TextStyle(fontSize: typo.bodySize, color: colors.textPrimary)),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: _loadWorksheet,
                child: const Text('Retry'),
              ),
            ],
          ),
        );
      }
      return const Center(child: CircularProgressIndicator());
    }

    if (_phase == _Phase.complete) {
      return _buildCompleteScreen(colors, typo);
    }

    return Column(
      children: [
        // ── Header ─────────────────────────────────────────────
        _buildHeader(colors, typo),

        // ── Question content ───────────────────────────────────
        Expanded(
          child: SlideTransition(
            position: _slideAnimation,
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 12),

                  // Difficulty tier badge
                  _buildTierBadge(colors, typo),
                  const SizedBox(height: 12),

                  // Question stem
                  _buildStem(colors, typo),
                  const SizedBox(height: 12),

                  // Visual (SVG)
                  if (_currentQuestion?.visualUrl != null ||
                      _currentQuestion?.visualRef != null)
                    _buildVisual(colors),

                  // Interaction widget
                  if (_phase == _Phase.answering)
                    _buildInteraction(colors, typo),

                  // Feedback + approach
                  if (_phase == _Phase.correct || _phase == _Phase.wrong)
                    _buildFeedback(colors, typo),

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ── Header with progress ────────────────────────────────────────────────

  Widget _buildHeader(KiwiTierColors colors, KiwiTierTypography typo) {
    return Container(
      padding: const EdgeInsets.fromLTRB(KiwiSpacing.sm, KiwiSpacing.sm, KiwiSpacing.lg, KiwiSpacing.sm),
      child: Row(
        children: [
          // Back button
          IconButton(
            onPressed: () => _showExitDialog(colors),
            icon: Icon(Icons.close_rounded, color: colors.textPrimary),
          ),
          const SizedBox(width: 4),

          // Day label
          Text(
            'Day ${widget.day}',
            style: TextStyle(
              fontSize: typo.topicNameSize,
              fontWeight: FontWeight.w700,
              color: colors.textPrimary,
              fontFamily: typo.fontFamily,
            ),
          ),
          const SizedBox(width: 12),

          // Progress bar
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(KiwiSpacing.sm - 2),
              child: LinearProgressIndicator(
                value: (_currentIndex + 1) / _totalQuestions,
                minHeight: 8,
                backgroundColor: KiwiColors.pathLocked,
                valueColor: AlwaysStoppedAnimation(colors.primary),
              ),
            ),
          ),
          const SizedBox(width: 8),

          // Progress text
          Text(
            '${_currentIndex + 1}/$_totalQuestions',
            style: TextStyle(
              fontSize: typo.topicNameSize,
              fontWeight: FontWeight.w700,
              color: colors.textMuted,
              fontFamily: typo.fontFamily,
            ),
          ),
        ],
      ),
    );
  }

  // ── Tier badge ──────────────────────────────────────────────────────────

  Widget _buildTierBadge(KiwiTierColors colors, KiwiTierTypography typo) {
    final q = _currentQuestion!;
    final tierLabel = q.difficultyTier;
    Color tierColor;
    String emoji;
    switch (tierLabel) {
      case 'warmup':
        tierColor = KiwiColors.kiwiGreen;
        emoji = '\u{1F33F}'; // 🌿
        break;
      case 'challenge':
        tierColor = KiwiColors.coral;
        emoji = '\u{1F525}'; // 🔥
        break;
      default:
        tierColor = KiwiColors.amber;
        emoji = '\u{1F4AA}'; // 💪
    }

    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.sm + 2, vertical: KiwiSpacing.xs),
          decoration: BoxDecoration(
            color: tierColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(KiwiSpacing.sm),
            border: Border.all(color: tierColor.withOpacity(0.3)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(emoji, style: TextStyle(fontSize: typo.chipSize)),
              const SizedBox(width: KiwiSpacing.xs),
              Text(
                tierLabel.toUpperCase(),
                style: TextStyle(
                  fontSize: typo.chipSize - 1,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1,
                  color: tierColor,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ],
          ),
        ),
        const Spacer(),
        // Mode indicator
        _modeChip(q.interactionMode, colors, typo),
      ],
    );
  }

  Widget _modeChip(String mode, KiwiTierColors colors, KiwiTierTypography typo) {
    IconData icon;
    String label;
    switch (mode) {
      case 'mcq':
        icon = Icons.radio_button_checked;
        label = 'MCQ';
        break;
      case 'integer':
        icon = Icons.pin;
        label = 'Number';
        break;
      case 'fill_up':
        icon = Icons.edit_note;
        label = 'Fill Up';
        break;
      case 'drag_drop':
        icon = Icons.swap_vert;
        label = 'Order';
        break;
      case 'match_column':
        icon = Icons.compare_arrows;
        label = 'Match';
        break;
      default:
        icon = Icons.quiz;
        label = mode;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: 3),
      decoration: BoxDecoration(
        color: colors.primary.withOpacity(0.08),
        borderRadius: BorderRadius.circular(KiwiSpacing.sm),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: colors.primary),
          const SizedBox(width: KiwiSpacing.xs),
          Text(
            label,
            style: TextStyle(
              fontSize: typo.chipSize - 1,
              fontWeight: FontWeight.w700,
              color: colors.primary,
              fontFamily: typo.fontFamily,
            ),
          ),
        ],
      ),
    );
  }

  // ── Question stem ───────────────────────────────────────────────────────

  Widget _buildStem(KiwiTierColors colors, KiwiTierTypography typo) {
    return Text(
      _currentQuestion!.stem,
      style: TextStyle(
        fontSize: typo.bodySize + 3,
        fontWeight: FontWeight.w600,
        color: colors.textPrimary,
        fontFamily: typo.fontFamily,
        height: 1.4,
      ),
    );
  }

  // ── Visual (SVG) ────────────────────────────────────────────────────────

  Widget _buildVisual(KiwiTierColors colors) {
    final q = _currentQuestion!;
    final url = _api.olympiadVisualUrl(q.id);

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(KiwiSpacing.md),
      decoration: BoxDecoration(
        color: KiwiColors.visualYellowBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: KiwiColors.visualYellowBorder, width: 1.5),
      ),
      child: Center(
        child: SizedBox(
          height: 140,
          child: AuthedSvg(
            url: url,
            placeholderBuilder: (_) => const SizedBox(
              height: 80,
              child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
            ),
          ),
        ),
      ),
    );
  }

  // ── Interaction widgets ─────────────────────────────────────────────────

  Widget _buildInteraction(KiwiTierColors colors, KiwiTierTypography typo) {
    final q = _currentQuestion!;
    switch (q.interactionMode) {
      case 'mcq':
        return _buildMcq(q, colors, typo);
      case 'integer':
        return IntegerInput(
          allowNegative: widget.grade >= 4,
          onSubmit: (value) {
            final correct = q.checkAnswer(integerAnswer: value);
            _onAnswer(correct);
          },
        );
      case 'fill_up':
        final isSymbol = q.fillBlankAnswer == '<' ||
            q.fillBlankAnswer == '>' ||
            q.fillBlankAnswer == '=';
        return FillUpInput(
          showSymbolButtons: isSymbol,
          hintText: isSymbol ? 'Pick the symbol' : 'Type your answer',
          onSubmit: (answer) {
            final correct = q.checkAnswer(textAnswer: answer);
            _onAnswer(correct);
          },
        );
      case 'drag_drop':
        return DragDropTiles(
          items: q.dragItems ?? [],
          onSubmit: (order) {
            final correct = q.checkAnswer(dragOrder: order);
            _onAnswer(correct);
          },
        );
      case 'match_column':
        return MatchColumnWidget(
          leftItems: q.leftColumn ?? [],
          rightItems: q.rightColumn ?? [],
          onSubmit: (matches) {
            final correct = q.checkAnswer(matchPairs: matches);
            _onAnswer(correct);
          },
        );
      default:
        return Text('Unknown mode: ${q.interactionMode}');
    }
  }

  Widget _buildMcq(OlympiadQuestion q, KiwiTierColors colors, KiwiTierTypography typo) {
    return Column(
      children: List.generate(q.choices.length, (i) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: OptionCard(
            text: q.choices[i],
            index: i,
            state: OptionState.idle,
            onTap: () {
              final correct = q.checkAnswer(selectedIndex: i);
              _onAnswer(correct);
            },
          ),
        );
      }),
    );
  }

  // ── Feedback after answering ────────────────────────────────────────────

  Widget _buildFeedback(KiwiTierColors colors, KiwiTierTypography typo) {
    final isCorrect = _phase == _Phase.correct;
    final q = _currentQuestion!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 8),

        // Correct/wrong banner
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
          decoration: BoxDecoration(
            color: isCorrect ? KiwiColors.correctBg : KiwiColors.wrongBg,
            borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
            border: Border.all(
              color: isCorrect ? KiwiColors.correct : KiwiColors.wrong,
              width: 1.5,
            ),
          ),
          child: Row(
            children: [
              Icon(
                isCorrect ? Icons.check_circle : Icons.cancel,
                color: isCorrect ? KiwiColors.kiwiGreenDark : KiwiColors.kiwiPrimaryDark,
                size: 28,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isCorrect ? 'Correct!' : 'Not quite!',
                      style: TextStyle(
                        fontSize: typo.headlineSize,
                        fontWeight: FontWeight.w800,
                        color: isCorrect
                            ? KiwiColors.kiwiGreenDark
                            : KiwiColors.kiwiPrimaryDark,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    if (!isCorrect) ...[
                      const SizedBox(height: 2),
                      Text(
                        _getCorrectAnswerText(q),
                        style: TextStyle(
                          fontSize: typo.topicNameSize,
                          color: KiwiColors.kiwiPrimaryDark,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 12),

        // "Why?" toggle
        GestureDetector(
          onTap: () => setState(() => _showApproach = !_showApproach),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
            decoration: BoxDecoration(
              color: KiwiColors.creamDark,
              borderRadius: BorderRadius.circular(KiwiSpacing.md),
              border: Border.all(color: KiwiColors.pathLocked),
            ),
            child: Row(
              children: [
                Icon(
                  _showApproach ? Icons.lightbulb : Icons.lightbulb_outline,
                  size: 20,
                  color: KiwiColors.amber,
                ),
                const SizedBox(width: 8),
                Text(
                  _showApproach ? 'Hide Explanation' : 'Show Why (Solution)',
                  style: TextStyle(
                    fontSize: typo.bodySize,
                    fontWeight: FontWeight.w700,
                    color: colors.textPrimary,
                    fontFamily: typo.fontFamily,
                  ),
                ),
                const Spacer(),
                Icon(
                  _showApproach
                      ? Icons.keyboard_arrow_up
                      : Icons.keyboard_arrow_down,
                  size: 20,
                  color: colors.textMuted,
                ),
              ],
            ),
          ),
        ),

        // Approach text
        if (_showApproach) ...[
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: _tier.shape.cardPadding,
            decoration: BoxDecoration(
              color: KiwiColors.visualYellowBg,
              borderRadius: BorderRadius.circular(KiwiSpacing.md),
              border: Border.all(color: KiwiColors.visualYellowBorder),
            ),
            child: Text(
              q.approach,
              style: TextStyle(
                fontSize: typo.bodySize,
                height: 1.5,
                color: KiwiColors.textDark,
                fontFamily: typo.fontFamily,
              ),
            ),
          ),
        ],

        const SizedBox(height: 16),

        // Next button
        SizedBox(
          width: double.infinity,
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [colors.primary, colors.primaryDark],
              ),
              borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
              boxShadow: [
                BoxShadow(
                  color: colors.primary.withOpacity(0.3),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: ElevatedButton(
              onPressed: _nextQuestion,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.transparent,
                foregroundColor: Colors.white,
                shadowColor: Colors.transparent,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
                ),
                textStyle: TextStyle(
                  fontSize: typo.buttonSize,
                  fontWeight: FontWeight.w800,
                  fontFamily: typo.fontFamily,
                ),
              ),
              child: Text(
                _currentIndex + 1 >= _totalQuestions
                    ? 'See Results'
                    : 'Next Question',
              ),
            ),
          ),
        ),
      ],
    );
  }

  String _getCorrectAnswerText(OlympiadQuestion q) {
    switch (q.interactionMode) {
      case 'mcq':
        if (q.correctAnswer < q.choices.length) {
          return 'Answer: ${q.choices[q.correctAnswer]}';
        }
        return '';
      case 'integer':
        return 'Answer: ${q.correctValue}';
      case 'fill_up':
        return 'Answer: ${q.fillBlankAnswer}';
      case 'drag_drop':
        return 'Correct order: ${q.dragItems?.join(', ')}';
      case 'match_column':
        return 'Check the explanation below.';
      default:
        return '';
    }
  }

  // ── Complete screen ─────────────────────────────────────────────────────

  Widget _buildCompleteScreen(KiwiTierColors colors, KiwiTierTypography typo) {
    final accuracy = _totalQuestions > 0 ? _correctCount / _totalQuestions : 0.0;
    final stars = _correctCount >= 11
        ? 3
        : _correctCount >= 8
            ? 2
            : _correctCount >= 5
                ? 1
                : 0;
    final mins = _stopwatch.elapsed.inMinutes;
    final secs = _stopwatch.elapsed.inSeconds % 60;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
      child: Column(
        children: [
          // Trophy/stars
          Text(
            stars >= 3
                ? '\u{1F3C6}' // 🏆
                : stars >= 2
                    ? '\u{2B50}' // ⭐
                    : stars >= 1
                        ? '\u{1F44D}' // 👍
                        : '\u{1F4AA}', // 💪
            style: const TextStyle(fontSize: 72),
          ),
          const SizedBox(height: 12),

          Text(
            stars >= 3
                ? 'Outstanding!'
                : stars >= 2
                    ? 'Great Work!'
                    : stars >= 1
                        ? 'Good Effort!'
                        : 'Keep Practicing!',
            style: TextStyle(
              fontSize: typo.streakNumberSize - 12,
              fontWeight: FontWeight.w900,
              color: colors.textPrimary,
              fontFamily: typo.fontFamily,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Day ${widget.day} Complete',
            style: TextStyle(
              fontSize: typo.bodySize,
              color: colors.textMuted,
              fontFamily: typo.fontFamily,
            ),
          ),
          const SizedBox(height: KiwiSpacing.xl),

          // Stars display
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(3, (i) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Icon(
                  i < stars ? Icons.star_rounded : Icons.star_border_rounded,
                  size: 48,
                  color: i < stars
                      ? KiwiColors.gemGold
                      : KiwiColors.pathLocked,
                ),
              );
            }),
          ),
          const SizedBox(height: 24),

          // Stats cards
          Row(
            children: [
              _resultStat(
                '\u{2705}',
                '$_correctCount/$_totalQuestions',
                'Correct',
                colors,
                typo,
              ),
              const SizedBox(width: 12),
              _resultStat(
                '\u{23F1}\u{FE0F}',
                '$mins:${secs.toString().padLeft(2, '0')}',
                'Time',
                colors,
                typo,
              ),
              const SizedBox(width: 12),
              _resultStat(
                '\u{1F3AF}',
                '${(accuracy * 100).toInt()}%',
                'Accuracy',
                colors,
                typo,
              ),
            ],
          ),
          const SizedBox(height: 32),

          // Buttons
          SizedBox(
            width: double.infinity,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [colors.primary, colors.primaryDark],
                ),
                borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
              ),
              child: ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  shadowColor: Colors.transparent,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
                  ),
                  textStyle: TextStyle(
                    fontSize: typo.buttonSize,
                    fontWeight: FontWeight.w800,
                    fontFamily: typo.fontFamily,
                  ),
                ),
                child: const Text('Back to Worksheets'),
              ),
            ),
          ),

          if (stars < 3) ...[
            const SizedBox(height: 12),
            TextButton(
              onPressed: () {
                setState(() {
                  _currentIndex = 0;
                  _correctCount = 0;
                  _phase = _Phase.answering;
                  _showApproach = false;
                  _stopwatch.reset();
                  _stopwatch.start();
                });
                _slideController.forward(from: 0);
              },
              child: Text(
                'Try Again',
                style: TextStyle(
                  fontSize: typo.topicNameSize,
                  fontWeight: FontWeight.w700,
                  color: colors.primary,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _resultStat(
      String emoji, String value, String label, KiwiTierColors colors, KiwiTierTypography typo) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
          border: Border.all(color: colors.topicCardBorder),
        ),
        child: Column(
          children: [
            Text(emoji, style: TextStyle(fontSize: typo.headlineSize + 4)),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(
                fontSize: typo.headlineSize + 2,
                fontWeight: FontWeight.w900,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                fontSize: typo.chipSize,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Exit dialog ─────────────────────────────────────────────────────────

  void _showExitDialog(KiwiTierColors colors) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Leave Worksheet?'),
        content: Text(
            'You\'ve answered $_currentIndex of $_totalQuestions questions. '
            'Progress won\'t be saved.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Stay'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop();
            },
            child: Text('Leave', style: TextStyle(color: colors.primary)),
          ),
        ],
      ),
    );
  }
}
