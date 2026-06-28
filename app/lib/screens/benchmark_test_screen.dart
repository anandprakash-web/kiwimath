import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/proficiency_card.dart';

/// Structured benchmark / diagnostic test screen.
///
/// Flow: Create test → present 20 questions one-by-one → submit → show results.
/// Parents can trigger this from the parent dashboard to get a formal
/// proficiency score and competency breakdown.
class BenchmarkTestScreen extends StatefulWidget {
  final String userId;
  final int grade;
  final String? childName;
  final String benchmarkType; // baseline, midline, endline, diagnostic
  final VoidCallback? onComplete;

  const BenchmarkTestScreen({
    super.key,
    required this.userId,
    this.grade = 1,
    this.childName,
    this.benchmarkType = 'diagnostic',
    this.onComplete,
  });

  @override
  State<BenchmarkTestScreen> createState() => _BenchmarkTestScreenState();
}

enum _BenchmarkPhase { loading, intro, answering, submitting, results }

class _BenchmarkTestScreenState extends State<BenchmarkTestScreen> {
  final ApiClient _api = ApiClient();

  _BenchmarkPhase _phase = _BenchmarkPhase.loading;
  String? _error;

  // Test data
  String _testId = '';
  List<Map<String, dynamic>> _questions = [];
  int _currentIndex = 0;
  int? _selectedOption;

  // Responses collected
  final List<Map<String, dynamic>> _responses = [];

  // Results
  Map<String, dynamic>? _results;

  @override
  void initState() {
    super.initState();
    _createTest();
  }

  Future<void> _createTest() async {
    setState(() { _phase = _BenchmarkPhase.loading; _error = null; });
    try {
      final data = await _api.createBenchmarkTest(
        userId: widget.userId,
        grade: widget.grade,
        benchmarkType: widget.benchmarkType,
      );
      _testId = data['test_id'] as String? ?? '';
      _questions = (data['questions'] as List<dynamic>? ?? [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      if (!mounted) return;
      if (_questions.isEmpty) {
        setState(() { _error = 'No questions available for the test.'; });
        return;
      }
      setState(() { _phase = _BenchmarkPhase.intro; });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = 'Could not create the test. Please try again.'; });
    }
  }

  void _startTest() {
    setState(() { _phase = _BenchmarkPhase.answering; _currentIndex = 0; });
  }

  void _selectOption(int index) {
    if (_selectedOption != null) return; // already selected
    setState(() { _selectedOption = index; });

    // Record response after a brief delay
    Future.delayed(const Duration(milliseconds: 600), () {
      if (!mounted) return;
      final q = _questions[_currentIndex];
      final options = (q['choices'] as List<dynamic>? ?? []);
      final selectedText = index < options.length ? options[index].toString() : '';

      _responses.add({
        'question_id': q['question_id'] ?? q['id'] ?? '',
        'selected_option': index,
        'selected_text': selectedText,
      });

      if (_currentIndex + 1 < _questions.length) {
        setState(() {
          _currentIndex++;
          _selectedOption = null;
        });
      } else {
        _submitTest();
      }
    });
  }

  void _skipQuestion() {
    final q = _questions[_currentIndex];
    _responses.add({
      'question_id': q['question_id'] ?? q['id'] ?? '',
      'selected_option': -1,
      'selected_text': '',
      'skipped': true,
    });

    if (_currentIndex + 1 < _questions.length) {
      setState(() {
        _currentIndex++;
        _selectedOption = null;
      });
    } else {
      _submitTest();
    }
  }

  Future<void> _submitTest() async {
    setState(() { _phase = _BenchmarkPhase.submitting; });
    try {
      final result = await _api.submitBenchmarkTest(
        userId: widget.userId,
        testId: _testId,
        responses: _responses,
      );
      if (!mounted) return;
      setState(() { _results = result; _phase = _BenchmarkPhase.results; });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = 'Could not submit the test. Please try again.';
        _phase = _BenchmarkPhase.loading;
      });
    }
  }

  KiwiTier get _tier => KiwiTier.forGrade(widget.grade);

  @override
  Widget build(BuildContext context) {
    final colors = _tier.colors;
    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: _buildContent(),
      ),
    );
  }

  Widget _buildContent() {
    if (_error != null) return _buildError();
    switch (_phase) {
      case _BenchmarkPhase.loading:
        return _buildLoading('Preparing your test...');
      case _BenchmarkPhase.intro:
        return _buildIntro();
      case _BenchmarkPhase.answering:
        return _buildQuestion();
      case _BenchmarkPhase.submitting:
        return _buildLoading('Scoring your responses...');
      case _BenchmarkPhase.results:
        return _buildResults();
    }
  }

  Widget _buildLoading(String message) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: colors.primary),
          const SizedBox(height: KiwiSpacing.lg),
          Text(message, style: TextStyle(fontSize: typo.bodySize, color: colors.textSecondary, fontFamily: typo.fontFamily)),
        ],
      ),
    );
  }

  Widget _buildError() {
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(KiwiSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline_rounded, size: 48, color: KiwiColors.coral),
            const SizedBox(height: KiwiSpacing.md),
            Text(_error!, textAlign: TextAlign.center,
                style: TextStyle(fontSize: typo.bodySize, color: colors.textSecondary, fontFamily: typo.fontFamily)),
            const SizedBox(height: KiwiSpacing.lg),
            GestureDetector(
              onTap: _createTest,
              child: Container(
                padding: shape.buttonPadding,
                decoration: BoxDecoration(
                  color: colors.primary,
                  borderRadius: BorderRadius.circular(shape.buttonRadius),
                ),
                child: Text('Try Again',
                    style: TextStyle(fontSize: typo.buttonSize, fontWeight: FontWeight.w700, color: Colors.white, fontFamily: typo.fontFamily)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Intro screen
  // ---------------------------------------------------------------------------

  Widget _buildIntro() {
    final name = widget.childName ?? 'your child';
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    final typeLabel = widget.benchmarkType == 'baseline'
        ? 'Baseline Assessment'
        : widget.benchmarkType == 'midline'
            ? 'Progress Check'
            : widget.benchmarkType == 'endline'
                ? 'Final Assessment'
                : 'Diagnostic Test';

    return Padding(
      padding: const EdgeInsets.all(KiwiSpacing.xl),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(shape.cardRadius),
            ),
            child: const Center(
              child: Text('\u{1F4CA}', style: TextStyle(fontSize: 40)),
            ),
          ),
          const SizedBox(height: KiwiSpacing.xl),
          Text(
            typeLabel,
            style: TextStyle(
              fontSize: typo.headlineSize + 2, fontWeight: typo.headlineWeight, color: colors.textPrimary, fontFamily: typo.fontFamily,
            ),
          ),
          const SizedBox(height: KiwiSpacing.md),
          Text(
            'This short test helps us understand exactly where $name '
            'stands in math. It takes about 10-15 minutes.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: typo.bodySize, color: colors.textSecondary, height: 1.5, fontFamily: typo.fontFamily),
          ),
          const SizedBox(height: KiwiSpacing.sm),
          Text(
            '${_questions.length} questions across different topics and difficulty levels.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: typo.chipSize, color: colors.textMuted, fontFamily: typo.fontFamily),
          ),
          const SizedBox(height: KiwiSpacing.xxl),
          // Tips
          Container(
            padding: shape.cardPadding,
            decoration: BoxDecoration(
              color: colors.cardBg,
              borderRadius: BorderRadius.circular(shape.cardRadius),
              border: Border.all(color: colors.topicCardBorder),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Tips for parents:',
                    style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textPrimary, fontFamily: typo.fontFamily)),
                const SizedBox(height: KiwiSpacing.sm),
                _tipRow(Icons.timer_outlined, 'No time pressure — let them think'),
                const SizedBox(height: KiwiSpacing.sm),
                _tipRow(Icons.block, 'Please don\'t help with answers'),
                const SizedBox(height: KiwiSpacing.sm),
                _tipRow(Icons.favorite_outline, 'It\'s okay to skip hard ones'),
              ],
            ),
          ),
          const SizedBox(height: KiwiSpacing.xxl),
          GestureDetector(
            onTap: _startTest,
            child: Container(
              width: double.infinity,
              padding: shape.buttonPadding,
              decoration: BoxDecoration(
                color: colors.primary,
                borderRadius: BorderRadius.circular(shape.buttonRadius),
              ),
              child: Center(
                child: Text('Start Test',
                    style: TextStyle(fontSize: typo.buttonSize, fontWeight: FontWeight.w700, color: Colors.white, fontFamily: typo.fontFamily)),
              ),
            ),
          ),
          const SizedBox(height: KiwiSpacing.md),
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: Text('Not now',
                style: TextStyle(fontSize: typo.chipSize, color: colors.textMuted, fontWeight: FontWeight.w500, fontFamily: typo.fontFamily)),
          ),
        ],
      ),
    );
  }

  Widget _tipRow(IconData icon, String text) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    return Row(
      children: [
        Icon(icon, size: 16, color: colors.primary),
        const SizedBox(width: KiwiSpacing.sm),
        Expanded(
          child: Text(text, style: TextStyle(fontSize: typo.chipSize, color: colors.textSecondary, fontFamily: typo.fontFamily)),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Question display
  // ---------------------------------------------------------------------------

  Widget _buildQuestion() {
    final q = _questions[_currentIndex];
    final stem = q['stem']?.toString() ?? q['question']?.toString() ?? '';
    final options = (q['choices'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    final progress = (_currentIndex + 1) / _questions.length;
    final correctIndex = q['correct_answer'] as int?;
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;

    return Padding(
      padding: KiwiSpacing.sectionPadding,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: progress bar + counter
          Row(
            children: [
              GestureDetector(
                onTap: () => _confirmExit(),
                child: Icon(Icons.close, size: 22, color: colors.textMuted),
              ),
              const SizedBox(width: KiwiSpacing.md),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(KiwiSpacing.xs),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: colors.backgroundDark,
                    valueColor: AlwaysStoppedAnimation<Color>(colors.primary),
                  ),
                ),
              ),
              const SizedBox(width: KiwiSpacing.md),
              Text(
                '${_currentIndex + 1}/${_questions.length}',
                style: TextStyle(
                    fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textSecondary, fontFamily: typo.fontFamily),
              ),
            ],
          ),
          const SizedBox(height: KiwiSpacing.xl),

          // Question stem
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    stem,
                    style: TextStyle(
                      fontSize: typo.headlineSize, fontWeight: FontWeight.w600,
                      color: colors.textPrimary, height: 1.5, fontFamily: typo.fontFamily,
                    ),
                  ),
                  const SizedBox(height: KiwiSpacing.xl),

                  // Options
                  ...List.generate(options.length, (i) {
                    final isSelected = _selectedOption == i;
                    final isCorrect = correctIndex != null && i == correctIndex;
                    Color bgColor = colors.cardBg;
                    Color borderColor = colors.topicCardBorder;
                    Color textColor = colors.textPrimary;

                    if (_selectedOption != null) {
                      if (isSelected && isCorrect) {
                        bgColor = KiwiColors.correctBg;
                        borderColor = KiwiColors.correct;
                        textColor = KiwiColors.kiwiGreenDark;
                      } else if (isSelected && !isCorrect) {
                        bgColor = KiwiColors.wrongBg;
                        borderColor = KiwiColors.wrong;
                        textColor = KiwiColors.kiwiPrimaryDark;
                      }
                    }

                    return GestureDetector(
                      onTap: () => _selectOption(i),
                      child: Container(
                        width: double.infinity,
                        margin: const EdgeInsets.only(bottom: KiwiSpacing.sm),
                        padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.md),
                        decoration: BoxDecoration(
                          color: bgColor,
                          borderRadius: BorderRadius.circular(shape.buttonRadius),
                          border: Border.all(color: borderColor, width: isSelected ? 2 : 1),
                        ),
                        child: Text(
                          options[i],
                          style: TextStyle(
                            fontSize: typo.bodySize, fontWeight: FontWeight.w500, color: textColor, fontFamily: typo.fontFamily,
                          ),
                        ),
                      ),
                    );
                  }),

                  // Skip button — lets user advance even without selecting
                  if (_selectedOption == null)
                    Padding(
                      padding: const EdgeInsets.only(top: KiwiSpacing.md),
                      child: Center(
                        child: GestureDetector(
                          onTap: _skipQuestion,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.xl, vertical: KiwiSpacing.md),
                            decoration: BoxDecoration(
                              color: colors.backgroundDark,
                              borderRadius: BorderRadius.circular(shape.chipRadius),
                              border: Border.all(color: colors.topicCardBorder),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.skip_next_rounded, size: 18, color: colors.textMuted),
                                const SizedBox(width: KiwiSpacing.sm),
                                Text(
                                  'Skip',
                                  style: TextStyle(
                                    fontSize: typo.bodySize,
                                    fontWeight: FontWeight.w600,
                                    color: colors.textMuted,
                                    fontFamily: typo.fontFamily,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _confirmExit() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Leave the test?'),
        content: const Text(
            'Your progress will be lost and you\'ll need to start over.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Continue test'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop();
            },
            child: const Text('Leave', style: TextStyle(color: KiwiColors.coral)),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Results
  // ---------------------------------------------------------------------------

  Widget _buildResults() {
    final result = _results!;
    final scaleScore = (result['scale_score'] as num?)?.toInt() ?? 500;
    final proficiency = result['proficiency'] as Map<String, dynamic>?;
    final competency = result['competency'] as Map<String, dynamic>?;
    final totalCorrect = (result['total_correct'] as num?)?.toInt() ?? 0;
    final totalQuestions = (result['total_questions'] as num?)?.toInt() ?? _questions.length;
    final accuracy = totalQuestions > 0 ? (totalCorrect / totalQuestions * 100) : 0.0;
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(KiwiSpacing.xl),
      child: Column(
        children: [
          const SizedBox(height: KiwiSpacing.md),
          // Completion header
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(shape.cardRadius),
            ),
            child: const Center(
              child: Text('\u{1F389}', style: TextStyle(fontSize: 32)),
            ),
          ),
          const SizedBox(height: KiwiSpacing.lg),
          Text(
            'Test Complete!',
            style: TextStyle(fontSize: typo.headlineSize + 2, fontWeight: typo.headlineWeight, color: colors.textPrimary, fontFamily: typo.fontFamily),
          ),
          const SizedBox(height: KiwiSpacing.sm),
          Text(
            '$totalCorrect of $totalQuestions correct (${accuracy.round()}%)',
            style: TextStyle(fontSize: typo.bodySize, color: colors.textSecondary, fontFamily: typo.fontFamily),
          ),
          const SizedBox(height: KiwiSpacing.xl),

          // Proficiency card (reuse the widget)
          if (proficiency != null)
            ProficiencyCard(
              proficiency: proficiency,
              competency: competency,
            ),

          // If no proficiency data, show basic score
          if (proficiency == null)
            Container(
              width: double.infinity,
              padding: shape.cardPadding,
              decoration: BoxDecoration(
                color: colors.cardBg,
                borderRadius: BorderRadius.circular(shape.cardRadius),
                border: Border.all(color: colors.topicCardBorder),
              ),
              child: Column(
                children: [
                  Text(
                    '$scaleScore',
                    style: TextStyle(
                      fontSize: 48, fontWeight: FontWeight.w800,
                      color: colors.primary,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                  const SizedBox(height: KiwiSpacing.xs),
                  Text('Scale Score',
                      style: TextStyle(fontSize: typo.bodySize, color: colors.textSecondary, fontFamily: typo.fontFamily)),
                ],
              ),
            ),

          const SizedBox(height: KiwiSpacing.xl),

          // Topic breakdown if available
          if (result['topic_scores'] != null) ...[
            Container(
              width: double.infinity,
              padding: shape.cardPadding,
              decoration: BoxDecoration(
                color: colors.cardBg,
                borderRadius: BorderRadius.circular(shape.cardRadius),
                border: Border.all(color: colors.topicCardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Topic Breakdown',
                      style: TextStyle(fontSize: typo.bodySize, fontWeight: FontWeight.w700, color: colors.textPrimary, fontFamily: typo.fontFamily)),
                  const SizedBox(height: KiwiSpacing.md),
                  ...(result['topic_scores'] as Map<String, dynamic>).entries.map((e) {
                    final topicData = e.value as Map<String, dynamic>;
                    final topicAcc = (topicData['accuracy'] as num?)?.toDouble() ?? 0;
                    final topicColor = topicAcc >= 70
                        ? KiwiColors.kiwiGreen
                        : topicAcc >= 40
                            ? KiwiColors.kiwiPrimary
                            : KiwiColors.sunset;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: KiwiSpacing.sm),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(e.key,
                                style: TextStyle(fontSize: typo.chipSize, color: colors.textSecondary, fontFamily: typo.fontFamily)),
                          ),
                          Text('${topicAcc.round()}%',
                              style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: topicColor, fontFamily: typo.fontFamily)),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ],

          const SizedBox(height: KiwiSpacing.xl),

          // Done button
          GestureDetector(
            onTap: () {
              widget.onComplete?.call();
              Navigator.of(context).pop();
            },
            child: Container(
              width: double.infinity,
              padding: shape.buttonPadding,
              decoration: BoxDecoration(
                color: colors.primary,
                borderRadius: BorderRadius.circular(shape.buttonRadius),
              ),
              child: Center(
                child: Text('Done',
                    style: TextStyle(fontSize: typo.buttonSize, fontWeight: FontWeight.w700, color: Colors.white, fontFamily: typo.fontFamily)),
              ),
            ),
          ),
          const SizedBox(height: KiwiSpacing.lg),
        ],
      ),
    );
  }
}
