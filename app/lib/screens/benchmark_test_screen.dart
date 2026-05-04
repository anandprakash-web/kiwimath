import 'package:flutter/material.dart';

import '../models/question_v2.dart';
import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/option_card.dart';
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
      if (_questions.isEmpty) {
        setState(() { _error = 'No questions available for the test.'; });
        return;
      }
      setState(() { _phase = _BenchmarkPhase.intro; });
    } catch (e) {
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
      final options = (q['options'] as List<dynamic>? ?? []);
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

  Future<void> _submitTest() async {
    setState(() { _phase = _BenchmarkPhase.submitting; });
    try {
      final result = await _api.submitBenchmarkTest(
        userId: widget.userId,
        testId: _testId,
        responses: _responses,
      );
      setState(() { _results = result; _phase = _BenchmarkPhase.results; });
    } catch (e) {
      setState(() {
        _error = 'Could not submit the test. Please try again.';
        _phase = _BenchmarkPhase.loading;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
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
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: KiwiColors.kiwiPrimary),
          const SizedBox(height: 16),
          Text(message, style: const TextStyle(fontSize: 14, color: KiwiColors.textMid)),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline_rounded, size: 48, color: Colors.red.shade300),
            const SizedBox(height: 12),
            Text(_error!, textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 14, color: KiwiColors.textMid)),
            const SizedBox(height: 18),
            GestureDetector(
              onTap: _createTest,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiPrimary,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text('Try Again',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Colors.white)),
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
    final typeLabel = widget.benchmarkType == 'baseline'
        ? 'Baseline Assessment'
        : widget.benchmarkType == 'midline'
            ? 'Progress Check'
            : widget.benchmarkType == 'endline'
                ? 'Final Assessment'
                : 'Diagnostic Test';

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Center(
              child: Text('\u{1F4CA}', style: TextStyle(fontSize: 40)),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            typeLabel,
            style: const TextStyle(
              fontSize: 22, fontWeight: FontWeight.w800, color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'This short test helps us understand exactly where $name '
            'stands in math. It takes about 10-15 minutes.',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 15, color: KiwiColors.textMid, height: 1.5),
          ),
          const SizedBox(height: 8),
          Text(
            '${_questions.length} questions across different topics and difficulty levels.',
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 13, color: KiwiColors.textMuted),
          ),
          const SizedBox(height: 32),
          // Tips
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: Colors.grey.shade200),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Tips for parents:',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: KiwiColors.textDark)),
                const SizedBox(height: 8),
                _tipRow(Icons.timer_outlined, 'No time pressure — let them think'),
                const SizedBox(height: 6),
                _tipRow(Icons.block, 'Please don\'t help with answers'),
                const SizedBox(height: 6),
                _tipRow(Icons.favorite_outline, 'It\'s okay to skip hard ones'),
              ],
            ),
          ),
          const SizedBox(height: 32),
          GestureDetector(
            onTap: _startTest,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 16),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimary,
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Center(
                child: Text('Start Test',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white)),
              ),
            ),
          ),
          const SizedBox(height: 12),
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: const Text('Not now',
                style: TextStyle(fontSize: 13, color: KiwiColors.textMuted, fontWeight: FontWeight.w500)),
          ),
        ],
      ),
    );
  }

  Widget _tipRow(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 16, color: KiwiColors.kiwiPrimary),
        const SizedBox(width: 8),
        Expanded(
          child: Text(text, style: const TextStyle(fontSize: 13, color: KiwiColors.textMid)),
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
    final options = (q['options'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    final progress = (_currentIndex + 1) / _questions.length;
    final correctIndex = q['correct_option'] as int?;

    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: progress bar + counter
          Row(
            children: [
              GestureDetector(
                onTap: () => _confirmExit(),
                child: const Icon(Icons.close, size: 22, color: KiwiColors.textMuted),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: Colors.grey.shade200,
                    valueColor: AlwaysStoppedAnimation<Color>(KiwiColors.kiwiPrimary),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                '${_currentIndex + 1}/${_questions.length}',
                style: const TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w700, color: KiwiColors.textMid),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Question stem
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    stem,
                    style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w600,
                      color: KiwiColors.textDark, height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Options
                  ...List.generate(options.length, (i) {
                    final isSelected = _selectedOption == i;
                    final isCorrect = correctIndex != null && i == correctIndex;
                    Color bgColor = Colors.white;
                    Color borderColor = Colors.grey.shade300;
                    Color textColor = KiwiColors.textDark;

                    if (_selectedOption != null) {
                      if (isSelected && isCorrect) {
                        bgColor = Colors.green.shade50;
                        borderColor = Colors.green;
                        textColor = Colors.green.shade800;
                      } else if (isSelected && !isCorrect) {
                        bgColor = Colors.red.shade50;
                        borderColor = Colors.red.shade300;
                        textColor = Colors.red.shade800;
                      }
                    }

                    return GestureDetector(
                      onTap: () => _selectOption(i),
                      child: Container(
                        width: double.infinity,
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        decoration: BoxDecoration(
                          color: bgColor,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: borderColor, width: isSelected ? 2 : 1),
                        ),
                        child: Text(
                          options[i],
                          style: TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w500, color: textColor,
                          ),
                        ),
                      ),
                    );
                  }),
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
            child: Text('Leave', style: TextStyle(color: Colors.red.shade400)),
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

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 12),
          // Completion header
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Center(
              child: Text('\u{1F389}', style: TextStyle(fontSize: 32)),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Test Complete!',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: KiwiColors.textDark),
          ),
          const SizedBox(height: 8),
          Text(
            '$totalCorrect of $totalQuestions correct (${accuracy.round()}%)',
            style: const TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 24),

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
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                children: [
                  Text(
                    '$scaleScore',
                    style: TextStyle(
                      fontSize: 48, fontWeight: FontWeight.w800,
                      color: KiwiColors.kiwiPrimary,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text('Scale Score',
                      style: TextStyle(fontSize: 14, color: KiwiColors.textMid)),
                ],
              ),
            ),

          const SizedBox(height: 24),

          // Topic breakdown if available
          if (result['topic_scores'] != null) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Topic Breakdown',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: KiwiColors.textDark)),
                  const SizedBox(height: 12),
                  ...(result['topic_scores'] as Map<String, dynamic>).entries.map((e) {
                    final topicData = e.value as Map<String, dynamic>;
                    final topicAcc = (topicData['accuracy'] as num?)?.toDouble() ?? 0;
                    final topicColor = topicAcc >= 70
                        ? KiwiColors.kiwiGreen
                        : topicAcc >= 40
                            ? KiwiColors.kiwiPrimary
                            : KiwiColors.sunset;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(e.key,
                                style: const TextStyle(fontSize: 13, color: KiwiColors.textMid)),
                          ),
                          Text('${topicAcc.round()}%',
                              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: topicColor)),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ],

          const SizedBox(height: 24),

          // Done button
          GestureDetector(
            onTap: () {
              widget.onComplete?.call();
              Navigator.of(context).pop();
            },
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 16),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimary,
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Center(
                child: Text('Done',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white)),
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
