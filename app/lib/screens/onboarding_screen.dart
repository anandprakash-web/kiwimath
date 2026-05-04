import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/question_v2.dart';
import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';

/// Onboarding v5.0 — adaptive-first, ground-up rebuild.
///
/// New flow (curriculum is NO LONGER step 3):
///   1. Welcome — "Let's find your level"
///   2. Name input — "What should we call you?"
///   3. Grade picker (1-5)
///   4. 10-question diagnostic mini-quiz
///   5. Results — strengths, starting difficulty
///   6. Plan — adaptive practice is #1, syllabus tracking is optional toggle
///
/// Curriculum selection is now a simple toggle on the plan page, not a
/// mandatory step. The default experience is pure adaptive.
class OnboardingScreen extends StatefulWidget {
  final String userId;
  final void Function(OnboardingResult result) onComplete;

  const OnboardingScreen({
    super.key,
    required this.userId,
    required this.onComplete,
  });

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

enum _OnboardingPhase {
  welcome,
  nameInput,
  gradePicker,
  loadingQuiz,
  quiz,
  submitting,
  results,
  plan,
  error,
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final ApiClient _api = ApiClient();

  _OnboardingPhase _phase = _OnboardingPhase.welcome;
  int? _grade;
  String? _curriculum;   // null by default — pure adaptive
  String? _error;
  String _kidName = '';
  final _nameController = TextEditingController();

  // Quiz state
  List<QuestionV2> _questions = [];
  int _index = 0;
  int? _selectedAnswer;
  DateTime? _questionStart;
  final List<Map<String, dynamic>> _answers = [];

  // Flagging state (admin diagnostic review)
  final Set<String> _flaggedQuestions = {};
  final Map<String, String> _flagReasons = {};
  final Map<String, String> _flagSeverities = {};

  // Result state
  Map<String, dynamic>? _resultJson;

  // -------------------------------------------------------------------
  // Phase transitions
  // -------------------------------------------------------------------

  void _toNameInput() {
    setState(() => _phase = _OnboardingPhase.nameInput);
  }

  void _toGradePicker() {
    final name = _nameController.text.trim();
    if (name.isNotEmpty) {
      _kidName = name;
    }
    setState(() => _phase = _OnboardingPhase.gradePicker);
  }

  Future<void> _onGradeSelected(int grade) async {
    setState(() {
      _grade = grade;
      _phase = _OnboardingPhase.loadingQuiz;
      _error = null;
    });
    try {
      final qs = await _api.getBenchmarkQuestions(grade: grade, count: 10, userId: widget.userId);
      if (!mounted) return;
      if (qs.isEmpty) {
        setState(() {
          _phase = _OnboardingPhase.error;
          _error = 'No benchmark questions available.';
        });
        return;
      }
      setState(() {
        _questions = qs;
        _index = 0;
        _answers.clear();
        _selectedAnswer = null;
        _phase = _OnboardingPhase.quiz;
        _questionStart = DateTime.now();
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = _OnboardingPhase.error;
        _error = e.toString();
      });
    }
  }

  void _onAnswerTap(int idx) {
    setState(() => _selectedAnswer = idx);
  }

  Future<void> _submitAnswer() async {
    if (_selectedAnswer == null) return;
    final q = _questions[_index];
    final timeMs = _questionStart != null
        ? DateTime.now().difference(_questionStart!).inMilliseconds
        : 0;

    _answers.add({
      'question_id': q.questionId,
      'selected_answer': _selectedAnswer,
      'time_taken_ms': timeMs,
    });

    if (_index + 1 >= _questions.length) {
      await _submitAllAnswers();
      return;
    }
    setState(() {
      _index += 1;
      _selectedAnswer = null;
      _questionStart = DateTime.now();
    });
  }

  Future<void> _submitAllAnswers() async {
    setState(() => _phase = _OnboardingPhase.submitting);
    try {
      if (_kidName.isNotEmpty) {
        try {
          await _api.updateStudentProfile(
            userId: widget.userId,
            name: _kidName,
            grade: _grade ?? 1,
            curriculum: _curriculum,
          );
        } catch (_) {
          debugPrint('Profile save failed, continuing with benchmark.');
        }
      }

      final result = await _api.submitBenchmark(
        userId: widget.userId,
        grade: _grade ?? 1,
        answers: _answers,
      );

      // Submit any flagged questions
      if (_flaggedQuestions.isNotEmpty) {
        try {
          await _api.submitDiagnosticReview(
            reviewerId: widget.userId,
            flags: _flaggedQuestions.map((qid) => <String, dynamic>{
              'question_id': qid,
              'reason': _flagReasons[qid] ?? 'No reason given',
              'severity': _flagSeverities[qid] ?? 'medium',
              'grade': _grade,
            }).toList(),
          );
        } catch (_) {
          debugPrint('Diagnostic review submission failed, continuing.');
        }
      }

      if (!mounted) return;
      setState(() {
        _resultJson = result;
        _phase = _OnboardingPhase.results;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = _OnboardingPhase.error;
        _error = e.toString();
      });
    }
  }

  void _onFinish() {
    final json = _resultJson;
    if (json == null) {
      Navigator.of(context).maybePop();
      return;
    }
    widget.onComplete(OnboardingResult.fromJson(json, kidName: _kidName));
  }

  // -------------------------------------------------------------------
  // Build
  // -------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.background,
      body: SafeArea(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          child: _buildPhase(),
        ),
      ),
    );
  }

  Widget _buildPhase() {
    switch (_phase) {
      case _OnboardingPhase.welcome:
        return _buildWelcome();
      case _OnboardingPhase.nameInput:
        return _buildNameInput();
      case _OnboardingPhase.gradePicker:
        return _buildGradePicker();
      case _OnboardingPhase.loadingQuiz:
      case _OnboardingPhase.submitting:
        return _buildLoading();
      case _OnboardingPhase.quiz:
        return _buildQuiz();
      case _OnboardingPhase.results:
        return _buildResults();
      case _OnboardingPhase.plan:
        return _buildPlan();
      case _OnboardingPhase.error:
        return _buildError();
    }
  }

  // -------------------------------------------------------------------
  // Welcome — v5: Vedantu orange, adaptive-first messaging
  // -------------------------------------------------------------------

  Widget _buildWelcome() {
    return Padding(
      key: const ValueKey('welcome'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 32),
          const Text('\u{1F95D}', style: TextStyle(fontSize: 88)),
          const SizedBox(height: 16),
          const Text(
            'Welcome to Kiwimath!',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiPrimaryDark,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            "Let's play a quick game so I can find\njust-right puzzles for you.",
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: KiwiColors.textMid,
              height: 1.4,
            ),
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _toNameInput,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                textStyle: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
              child: const Text("Let's go!"),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Name input
  // -------------------------------------------------------------------

  Widget _buildNameInput() {
    return Padding(
      key: const ValueKey('nameInput'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 32),
          const Text('\u{1F44B}', style: TextStyle(fontSize: 56)),
          const SizedBox(height: 16),
          const Text(
            "What should we call you?",
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiPrimaryDark,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            "Your first name is perfect!",
            style: TextStyle(
              fontSize: 14,
              color: KiwiColors.textMid,
            ),
          ),
          const SizedBox(height: 28),
          TextField(
            controller: _nameController,
            autofocus: true,
            textCapitalization: TextCapitalization.words,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
            decoration: InputDecoration(
              hintText: 'Type your name',
              hintStyle: TextStyle(color: KiwiColors.textMuted.withOpacity(0.5)),
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide(color: KiwiColors.kiwiPrimary.withOpacity(0.3)),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: const BorderSide(color: KiwiColors.kiwiPrimary, width: 2),
              ),
            ),
            onSubmitted: (_) => _toGradePicker(),
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _toGradePicker,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                textStyle: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
              child: const Text('Next'),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Grade picker — goes DIRECTLY to quiz (no curriculum picker)
  // -------------------------------------------------------------------

  Widget _buildGradePicker() {
    return Padding(
      key: const ValueKey('gradePicker'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 16),
          const Text('\u{1F393}', style: TextStyle(fontSize: 56)),
          const SizedBox(height: 12),
          Text(
            _kidName.isNotEmpty
                ? 'Which grade are you in, $_kidName?'
                : 'Which grade are you in?',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiPrimaryDark,
            ),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 14,
              mainAxisSpacing: 14,
              childAspectRatio: 1.6,
              children: List.generate(
                5,
                (i) => _GradeCard(
                  grade: i + 1,
                  onTap: () => _onGradeSelected(i + 1),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Loading
  // -------------------------------------------------------------------

  Widget _buildLoading() {
    return Center(
      key: const ValueKey('loading'),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(
            color: KiwiColors.kiwiPrimary,
          ),
          const SizedBox(height: 16),
          Text(
            _phase == _OnboardingPhase.submitting
                ? 'Analyzing your answers...'
                : 'Loading your quiz...',
            style: const TextStyle(
              fontSize: 14,
              color: KiwiColors.textMid,
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Quiz
  // -------------------------------------------------------------------

  Widget _buildQuiz() {
    if (_questions.isEmpty) return const SizedBox.shrink();
    final q = _questions[_index];
    final progress = (_index + 1) / _questions.length;

    return Padding(
      key: ValueKey('quiz_$_index'),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Progress bar
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: const Color(0xFFE0E0E0),
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      KiwiColors.kiwiPrimary,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                '${_index + 1}/${_questions.length}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textMuted,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Question text
          Text(
            q.stem,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textDark,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 24),

          // Options (2x2 grid)
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              childAspectRatio: 2.2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              children: List.generate(
                q.choices.length,
                (i) {
                  final selected = _selectedAnswer == i;
                  return GestureDetector(
                    onTap: () => _onAnswerTap(i),
                    child: Container(
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: selected
                            ? KiwiColors.kiwiPrimary.withOpacity(0.12)
                            : Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                          color: selected
                              ? KiwiColors.kiwiPrimary
                              : Colors.grey.shade200,
                          width: selected ? 2 : 1,
                        ),
                      ),
                      child: Text(
                        q.choices[i],
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                          color: selected
                              ? KiwiColors.kiwiPrimaryDark
                              : KiwiColors.textDark,
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),

          // Flag + Submit
          Row(
            children: [
              // Flag button
              GestureDetector(
                onTap: () => _showFlagDialog(q),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: _flaggedQuestions.contains(q.questionId)
                        ? const Color(0xFFFFF3E0)
                        : Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    _flaggedQuestions.contains(q.questionId)
                        ? Icons.flag
                        : Icons.flag_outlined,
                    size: 20,
                    color: _flaggedQuestions.contains(q.questionId)
                        ? KiwiColors.kiwiPrimary
                        : KiwiColors.textMuted,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: _selectedAnswer != null ? _submitAnswer : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: KiwiColors.kiwiPrimary,
                    foregroundColor: Colors.white,
                    disabledBackgroundColor: Colors.grey.shade200,
                    disabledForegroundColor: Colors.grey.shade400,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: Text(
                    _index + 1 >= _questions.length ? 'Finish' : 'Next',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
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

  void _showFlagDialog(QuestionV2 q) {
    showDialog(
      context: context,
      builder: (ctx) {
        String reason = _flagReasons[q.questionId] ?? '';
        String severity = _flagSeverities[q.questionId] ?? 'medium';
        return AlertDialog(
          title: const Text('Flag this question'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                decoration: const InputDecoration(
                  hintText: "What's wrong with this question?",
                  border: OutlineInputBorder(),
                ),
                maxLines: 2,
                onChanged: (v) => reason = v,
                controller: TextEditingController(text: reason),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: severity,
                items: const [
                  DropdownMenuItem(value: 'low', child: Text('Low')),
                  DropdownMenuItem(value: 'medium', child: Text('Medium')),
                  DropdownMenuItem(value: 'high', child: Text('High')),
                ],
                onChanged: (v) => severity = v ?? 'medium',
                decoration: const InputDecoration(
                  labelText: 'Severity',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                _flaggedQuestions.remove(q.questionId);
                _flagReasons.remove(q.questionId);
                _flagSeverities.remove(q.questionId);
                setState(() {});
                Navigator.pop(ctx);
              },
              child: const Text('Remove flag'),
            ),
            FilledButton(
              onPressed: () {
                _flaggedQuestions.add(q.questionId);
                _flagReasons[q.questionId] = reason;
                _flagSeverities[q.questionId] = severity;
                setState(() {});
                Navigator.pop(ctx);
              },
              child: const Text('Flag'),
            ),
          ],
        );
      },
    );
  }

  // -------------------------------------------------------------------
  // Results
  // -------------------------------------------------------------------

  Widget _buildResults() {
    final json = _resultJson ?? {};
    final res = OnboardingResult.fromJson(json, kidName: _kidName);
    final pct = (res.overallAccuracy * 100).round();
    final greet = _kidName.isNotEmpty ? ', $_kidName' : '';

    return Padding(
      key: const ValueKey('results'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 12),
          const Text('\u{1F3AF}', style: TextStyle(fontSize: 56)),
          const SizedBox(height: 12),
          Text(
            'Great job$greet!',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiPrimaryDark,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Here\'s what I learned about you:',
            style: const TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 24),
          _ResultCard(
            icon: Icons.check_circle_outline,
            color: KiwiColors.correct,
            title: 'Accuracy',
            subtitle: '${res.totalCorrect}/${res.totalQuestions} correct ($pct%)',
          ),
          if (res.strengths.isNotEmpty)
            _ResultCard(
              icon: Icons.star_rounded,
              color: KiwiColors.kiwiPrimary,
              title: 'Strengths',
              subtitle: res.strengths.map(_prettyTopic).join(', '),
            ),
          if (res.suggestedTopics.isNotEmpty)
            _ResultCard(
              icon: Icons.trending_up,
              color: KiwiColors.indigo,
              title: 'Focus areas',
              subtitle: res.suggestedTopics.take(3).map(_prettyTopic).join(', '),
            ),
          _ResultCard(
            icon: Icons.speed,
            color: KiwiColors.teal,
            title: 'Starting level',
            subtitle: 'Difficulty ${res.recommendedStartingDifficulty} of 100',
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => setState(() => _phase = _OnboardingPhase.plan),
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                textStyle: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
              child: const Text('See my plan'),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Plan — v5: ADAPTIVE FIRST. Curriculum is optional toggle.
  // -------------------------------------------------------------------

  Widget _buildPlan() {
    final json = _resultJson ?? {};
    final perTopic = (json['per_topic'] as List<dynamic>? ?? []);
    final suggestedTopics = (json['suggested_topics'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    final strengths = (json['strengths'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toSet();

    // Topic name lookup
    final topicNames = <String, String>{};
    for (final t in perTopic) {
      if (t is Map<String, dynamic>) {
        topicNames[t['topic_id'] as String? ?? ''] =
            t['topic_name'] as String? ?? '';
      }
    }

    // v5: Adaptive is ALWAYS #1. Focus areas from diagnostic.
    final planItems = <_PlanItem>[];

    // #1 — Adaptive Practice (always first, always primary)
    planItems.add(_PlanItem(
      topicId: 'adaptive',
      topicName: 'Adaptive Practice',
      badge: 'Start here',
      badgeColor: KiwiColors.kiwiPrimary,
      reason: 'Smart practice personalized to your level',
      isStrength: false,
    ));

    // #2-4 — Focus areas from diagnostic
    for (int i = 0; i < suggestedTopics.length && i < 3; i++) {
      final tid = suggestedTopics[i];
      planItems.add(_PlanItem(
        topicId: tid,
        topicName: topicNames[tid] ?? _prettyTopic(tid),
        badge: 'Focus',
        badgeColor: KiwiColors.indigo,
        reason: 'Practice will boost your score',
        isStrength: false,
      ));
    }

    // Strengths
    for (final tid in strengths.take(2)) {
      if (!suggestedTopics.contains(tid)) {
        planItems.add(_PlanItem(
          topicId: tid,
          topicName: topicNames[tid] ?? _prettyTopic(tid),
          badge: 'Strong',
          badgeColor: KiwiColors.correct,
          reason: 'Already doing great — keep it up!',
          isStrength: true,
        ));
      }
    }

    final nameGreet = _kidName.isNotEmpty ? ', $_kidName' : '';

    return Padding(
      key: const ValueKey('plan'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 12),
          const Text('\u{1F680}', style: TextStyle(fontSize: 48)),
          const SizedBox(height: 12),
          Text(
            'Your learning plan$nameGreet',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiPrimaryDark,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Based on your quiz, here\'s your personalized path:',
            style: TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 20),

          // Plan items
          Expanded(
            child: ListView.separated(
              itemCount: planItems.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final item = planItems[index];
                return Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: item.isStrength ? Colors.grey.shade50 : Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: item.isStrength
                          ? Colors.grey.shade200
                          : item.badgeColor.withOpacity(0.3),
                      width: 1.5,
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: item.badgeColor.withOpacity(0.12),
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            '${index + 1}',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: item.badgeColor,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item.topicName,
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w700,
                                color: item.isStrength
                                    ? KiwiColors.textMid
                                    : KiwiColors.textDark,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              item.reason,
                              style: const TextStyle(
                                fontSize: 12,
                                color: KiwiColors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 10,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: item.badgeColor.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          item.badge,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: item.badgeColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),

          // v5: Optional syllabus toggle (not a mandatory step)
          const SizedBox(height: 12),
          _buildSyllabusToggle(),
          const SizedBox(height: 16),

          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _onFinish,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                textStyle: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
              child: const Text('Start practicing!'),
            ),
          ),
        ],
      ),
    );
  }

  /// Optional curriculum toggle — appears at bottom of plan page.
  /// Default is OFF (pure adaptive). User can opt-in to syllabus tracking.
  Widget _buildSyllabusToggle() {
    final hasSelected = _curriculum != null && _curriculum!.isNotEmpty;
    return GestureDetector(
      onTap: () => _showSyllabusSheet(),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: hasSelected
              ? KiwiColors.kiwiPrimaryLight
              : Colors.grey.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: hasSelected
                ? KiwiColors.kiwiPrimary.withOpacity(0.3)
                : Colors.grey.shade200,
          ),
        ),
        child: Row(
          children: [
            Icon(
              hasSelected ? Icons.menu_book_rounded : Icons.add_rounded,
              size: 18,
              color: hasSelected
                  ? KiwiColors.kiwiPrimary
                  : KiwiColors.textMuted,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                hasSelected
                    ? 'Following ${_curriculum!.toUpperCase()} syllabus'
                    : 'Want to follow a school syllabus? (optional)',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: hasSelected ? FontWeight.w600 : FontWeight.w500,
                  color: hasSelected
                      ? KiwiColors.kiwiPrimaryDark
                      : KiwiColors.textMid,
                ),
              ),
            ),
            Icon(
              Icons.chevron_right_rounded,
              size: 18,
              color: KiwiColors.textMuted,
            ),
          ],
        ),
      ),
    );
  }

  void _showSyllabusSheet() {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Track a school syllabus',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.textDark,
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'This adds a Syllabus tab so you can see chapter-wise progress. Your main practice stays adaptive.',
                style: TextStyle(fontSize: 13, color: KiwiColors.textMid),
              ),
              const SizedBox(height: 20),
              _syllabusOption(ctx, 'NCERT', 'CBSE schools', Icons.school_rounded, const Color(0xFF2E7D32), 'ncert'),
              const SizedBox(height: 8),
              _syllabusOption(ctx, 'ICSE', 'ICSE/ISC schools', Icons.auto_stories_rounded, const Color(0xFF1565C0), 'icse'),
              const SizedBox(height: 8),
              _syllabusOption(ctx, 'Cambridge Primary', 'International', Icons.language_rounded, const Color(0xFF6A1B9A), 'cambridge'),
              const SizedBox(height: 8),
              _syllabusOption(ctx, 'None', 'Pure adaptive practice', Icons.bolt_rounded, KiwiColors.kiwiPrimary, ''),
            ],
          ),
        ),
      ),
    );
  }

  Widget _syllabusOption(BuildContext ctx, String label, String subtitle, IconData icon, Color color, String value) {
    final selected = _curriculum == value || (_curriculum == null && value.isEmpty);
    return GestureDetector(
      onTap: () {
        setState(() => _curriculum = value.isEmpty ? null : value);
        Navigator.pop(ctx);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: selected ? color.withOpacity(0.08) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? color : Colors.grey.shade200,
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: color)),
                  Text(subtitle, style: const TextStyle(fontSize: 11, color: KiwiColors.textMuted)),
                ],
              ),
            ),
            if (selected)
              Icon(Icons.check_circle_rounded, color: color, size: 20),
          ],
        ),
      ),
    );
  }

  // -------------------------------------------------------------------
  // Error
  // -------------------------------------------------------------------

  Widget _buildError() {
    String friendlyMsg;
    final raw = _error ?? '';
    if (raw.contains('SocketException') || raw.contains('Connection')) {
      friendlyMsg = "Hmm, can't reach our servers. Check your internet and try again!";
    } else if (raw.contains('No benchmark')) {
      friendlyMsg = "We're getting your quiz ready. Try again in a moment!";
    } else {
      friendlyMsg = "Oops! Something didn't work. Let's try again!";
    }
    return Padding(
      key: const ValueKey('error'),
      padding: const EdgeInsets.all(24),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('\u{1F62E}', style: TextStyle(fontSize: 56)),
            const SizedBox(height: 12),
            const Text(
              'Hmm, something went wrong',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              friendlyMsg,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: KiwiColors.textMid,
                fontSize: 14,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () =>
                  setState(() => _phase = _OnboardingPhase.welcome),
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Try again'),
            ),
          ],
        ),
      ),
    );
  }

  String _prettyTopic(String topicId) {
    const fixups = <String, String>{
      'counting_observation': 'Counting & Observation',
      'arithmetic_missing_numbers': 'Arithmetic & Missing Numbers',
      'patterns_sequences': 'Patterns & Sequences',
      'logic_ordering': 'Logic & Ordering',
      'spatial_reasoning_3d': 'Spatial Reasoning & 3D',
      'shapes_folding_symmetry': 'Shapes, Folding & Symmetry',
      'word_problems_stories': 'Word Problems & Stories',
      'number_puzzles_games': 'Number Puzzles & Games',
    };
    if (fixups.containsKey(topicId)) return fixups[topicId]!;
    return topicId
        .split('_')
        .map((w) => w.isEmpty
            ? w
            : w == '3d'
                ? '3D'
                : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}

// ===========================================================================
// Sub-widgets
// ===========================================================================

class _GradeCard extends StatelessWidget {
  final int grade;
  final VoidCallback onTap;

  const _GradeCard({required this.grade, required this.onTap});

  @override
  Widget build(BuildContext context) {
    // Use Vedantu orange gradients
    final colors = KiwiColors.topicGradients[(grade - 1) % 12];
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: colors),
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: colors.last.withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Grade $grade',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _ageRange(grade),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _ageRange(int grade) {
    switch (grade) {
      case 1: return 'ages 6–7';
      case 2: return 'ages 7–8';
      case 3: return 'ages 8–9';
      case 4: return 'ages 9–10';
      case 5: return 'ages 10–11';
      case 6: return 'ages 11–12';
      default: return '';
    }
  }
}

class _ResultCard extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;

  const _ResultCard({
    required this.icon,
    required this.color,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 12,
                      color: KiwiColors.textMuted,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.textDark,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanItem {
  final String topicId;
  final String topicName;
  final String badge;
  final Color badgeColor;
  final String reason;
  final bool isStrength;

  const _PlanItem({
    required this.topicId,
    required this.topicName,
    required this.badge,
    required this.badgeColor,
    required this.reason,
    required this.isStrength,
  });
}

// ===========================================================================
// Result model
// ===========================================================================

class OnboardingResult {
  final String userId;
  final int grade;
  final int totalQuestions;
  final int totalCorrect;
  final double overallAccuracy;
  final int estimatedAbility;
  final int recommendedStartingDifficulty;
  final List<String> suggestedTopics;
  final List<String> strengths;
  final String kidName;

  OnboardingResult({
    required this.userId,
    required this.grade,
    required this.totalQuestions,
    required this.totalCorrect,
    required this.overallAccuracy,
    required this.estimatedAbility,
    required this.recommendedStartingDifficulty,
    required this.suggestedTopics,
    required this.strengths,
    this.kidName = '',
  });

  factory OnboardingResult.fromJson(Map<String, dynamic> json, {String kidName = ''}) {
    return OnboardingResult(
      userId: json['user_id'] as String? ?? '',
      grade: (json['grade'] as num?)?.toInt() ?? 1,
      totalQuestions: (json['total_questions'] as num?)?.toInt() ?? 0,
      totalCorrect: (json['total_correct'] as num?)?.toInt() ?? 0,
      overallAccuracy:
          (json['overall_accuracy'] as num?)?.toDouble() ?? 0.0,
      estimatedAbility: (json['estimated_ability'] as num?)?.toInt() ?? 1,
      recommendedStartingDifficulty:
          (json['recommended_starting_difficulty'] as num?)?.toInt() ?? 1,
      suggestedTopics: (json['suggested_topics'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      strengths: (json['strengths'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      kidName: kidName,
    );
  }
}
