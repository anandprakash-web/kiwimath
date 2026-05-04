import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/question_v2.dart';
import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';

/// Diagnostic onboarding flow (Task #196).
///
/// Steps:
///   1. Welcome screen
///   2. Grade picker (1-5)
///   3. 10-question diagnostic mini-quiz (round-robin across topics)
///   4. Results screen showing strengths and starting difficulty
///
/// On completion, calls `onComplete(result)` with the parsed benchmark
/// result so the home screen can route the user into the right starting
/// difficulty / topic order.
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
  curriculumPicker,
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
  String? _curriculum;   // ncert, icse, igcse, olympiad
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

  void _toCurriculumPicker() {
    final name = _nameController.text.trim();
    if (name.isNotEmpty) {
      _kidName = name;
    }
    setState(() => _phase = _OnboardingPhase.curriculumPicker);
  }

  void _onCurriculumSelected(String curriculum) {
    _curriculum = curriculum;
    setState(() => _phase = _OnboardingPhase.gradePicker);
  }

  void _toGradePicker() {
    // Legacy path — kept for any other callers
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
      // Save kid's profile (name + grade) to backend.
      if (_kidName.isNotEmpty) {
        try {
          await _api.updateStudentProfile(
            userId: widget.userId,
            name: _kidName,
            grade: _grade ?? 1,
            curriculum: _curriculum,
          );
        } catch (_) {
          // Non-fatal — profile save can retry later.
          debugPrint('Profile save failed, continuing with benchmark.');
        }
      }

      final result = await _api.submitBenchmark(
        userId: widget.userId,
        grade: _grade ?? 1,
        answers: _answers,
      );

      // Submit any flagged questions to the backend review queue
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
          // Non-fatal — flags can be retried later
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
      case _OnboardingPhase.curriculumPicker:
        return _buildCurriculumPicker();
      case _OnboardingPhase.gradePicker:
        return _buildGradePicker();
      case _OnboardingPhase.loadingQuiz:
      case _OnboardingPhase.submitting:
        return const Center(child: CircularProgressIndicator());
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
  // Welcome screen
  // -------------------------------------------------------------------

  Widget _buildWelcome() {
    return Padding(
      key: const ValueKey('welcome'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 32),
          const Text('🥝', style: TextStyle(fontSize: 88)),
          const SizedBox(height: 16),
          const Text(
            'Welcome to Kiwimath!',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiGreenDark,
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
                backgroundColor: KiwiColors.kiwiGreen,
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
          const SizedBox(height: 12),
          const Text(
            '10 fun questions • about 3 minutes',
            style: TextStyle(fontSize: 12, color: KiwiColors.textMuted),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Name input (parent fills in kid's name)
  // -------------------------------------------------------------------

  Widget _buildNameInput() {
    return Padding(
      key: const ValueKey('name'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const SizedBox(height: 32),
          const Text('👋', style: TextStyle(fontSize: 64)),
          const SizedBox(height: 16),
          const Text(
            "What's your name?",
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiGreenDark,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Parents, enter your child\'s name so\nwe can make it personal!',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: KiwiColors.textMid,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 32),
          TextField(
            controller: _nameController,
            autofocus: true,
            textCapitalization: TextCapitalization.words,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textDark,
            ),
            textAlign: TextAlign.center,
            decoration: InputDecoration(
              hintText: 'e.g. Aarav, Diya, Kabir',
              hintStyle: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w400,
                color: Colors.grey.shade400,
              ),
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: BorderSide(color: KiwiColors.kiwiGreenLight),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(
                  color: KiwiColors.kiwiGreen,
                  width: 2,
                ),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 20,
                vertical: 18,
              ),
            ),
            onSubmitted: (_) => _toCurriculumPicker(),
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _toCurriculumPicker,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiGreen,
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
          const SizedBox(height: 8),
          TextButton(
            onPressed: _toCurriculumPicker,
            child: const Text(
              'Skip for now',
              style: TextStyle(fontSize: 13, color: KiwiColors.textMuted),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Curriculum picker
  // -------------------------------------------------------------------

  Widget _buildCurriculumPicker() {
    final displayName = _kidName.isNotEmpty ? _kidName : 'your child';
    final curricula = [
      {
        'id': 'ncert',
        'label': 'NCERT / CBSE',
        'icon': Icons.menu_book_rounded,
        'color': const Color(0xFF2E7D32),
        'subtitle': 'National curriculum',
      },
      {
        'id': 'icse',
        'label': 'ICSE',
        'icon': Icons.school_rounded,
        'color': const Color(0xFF1565C0),
        'subtitle': 'CISCE curriculum',
      },
      {
        'id': 'igcse',
        'label': 'IGCSE',
        'icon': Icons.public_rounded,
        'color': const Color(0xFF6A1B9A),
        'subtitle': 'Cambridge International',
      },
      {
        'id': 'olympiad',
        'label': 'Olympiad / Kangaroo',
        'icon': Icons.emoji_events_rounded,
        'color': const Color(0xFFFF6D00),
        'subtitle': 'Competitive maths',
      },
    ];

    return Padding(
      key: const ValueKey('curriculum'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          IconButton(
            onPressed: () =>
                setState(() => _phase = _OnboardingPhase.nameInput),
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(height: 8),
          Text(
            'What does $displayName follow?',
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Pick the curriculum your child studies.',
            style: TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView.separated(
              itemCount: curricula.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final c = curricula[index];
                return _CurriculumCard(
                  label: c['label'] as String,
                  subtitle: c['subtitle'] as String,
                  icon: c['icon'] as IconData,
                  color: c['color'] as Color,
                  onTap: () => _onCurriculumSelected(c['id'] as String),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Grade picker
  // -------------------------------------------------------------------

  Widget _buildGradePicker() {
    return Padding(
      key: const ValueKey('grade'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          IconButton(
            onPressed: () =>
                setState(() => _phase = _OnboardingPhase.curriculumPicker),
            icon: const Icon(Icons.arrow_back),
          ),
          const SizedBox(height: 8),
          const Text(
            'What grade are you in?',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Pick the one that fits you best.',
            style: TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.4,
              children: [
                for (int g = 1; g <= 6; g++)
                  _GradeCard(
                    grade: g,
                    onTap: () => _onGradeSelected(g),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Quiz screen
  // -------------------------------------------------------------------

  void _showFlagDialog(QuestionV2 q) {
    final reasonController = TextEditingController(
      text: _flagReasons[q.questionId] ?? '',
    );
    String severity = _flagSeverities[q.questionId] ?? 'medium';

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            return AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              title: const Text(
                'Flag this question',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Q: ${q.stem}',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: reasonController,
                    maxLines: 3,
                    decoration: InputDecoration(
                      labelText: 'What\'s wrong?',
                      hintText: 'e.g. Wrong answer, hint reveals answer, too easy...',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 10,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Severity',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    children: ['low', 'medium', 'high', 'critical'].map((s) {
                      final isSelected = severity == s;
                      final color = s == 'critical'
                          ? Colors.red
                          : s == 'high'
                              ? Colors.orange
                              : s == 'medium'
                                  ? Colors.amber.shade700
                                  : Colors.green;
                      return Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: ChoiceChip(
                          label: Text(
                            s[0].toUpperCase() + s.substring(1),
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: isSelected ? Colors.white : color,
                            ),
                          ),
                          selected: isSelected,
                          selectedColor: color,
                          backgroundColor: color.withOpacity(0.1),
                          onSelected: (_) {
                            setDialogState(() => severity = s);
                          },
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
              actions: [
                if (_flaggedQuestions.contains(q.questionId))
                  TextButton(
                    onPressed: () {
                      setState(() {
                        _flaggedQuestions.remove(q.questionId);
                        _flagReasons.remove(q.questionId);
                        _flagSeverities.remove(q.questionId);
                      });
                      Navigator.pop(ctx);
                    },
                    child: const Text(
                      'Unflag',
                      style: TextStyle(color: Colors.grey),
                    ),
                  ),
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: () {
                    final reason = reasonController.text.trim();
                    if (reason.isEmpty) return;
                    setState(() {
                      _flaggedQuestions.add(q.questionId);
                      _flagReasons[q.questionId] = reason;
                      _flagSeverities[q.questionId] = severity;
                    });
                    Navigator.pop(ctx);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFE53935),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: const Text('Flag'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _buildQuiz() {
    final q = _questions[_index];
    final progress = (_index + 1) / _questions.length;

    return Padding(
      key: ValueKey('quiz-$_index'),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: KiwiColors.kiwiGreenLight,
              valueColor: const AlwaysStoppedAnimation<Color>(
                KiwiColors.kiwiGreen,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Question ${_index + 1} of ${_questions.length}',
                style: const TextStyle(
                  fontSize: 12,
                  color: KiwiColors.textMuted,
                  fontWeight: FontWeight.w600,
                ),
              ),
              // Flag button for admin review
              GestureDetector(
                onTap: () => _showFlagDialog(q),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: _flaggedQuestions.contains(q.questionId)
                        ? const Color(0xFFFFEBEE)
                        : const Color(0xFFF5F5F5),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: _flaggedQuestions.contains(q.questionId)
                          ? const Color(0xFFE53935)
                          : Colors.grey.shade300,
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _flaggedQuestions.contains(q.questionId)
                            ? Icons.flag
                            : Icons.flag_outlined,
                        size: 16,
                        color: _flaggedQuestions.contains(q.questionId)
                            ? const Color(0xFFE53935)
                            : Colors.grey.shade600,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _flaggedQuestions.contains(q.questionId) ? 'Flagged' : 'Flag',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: _flaggedQuestions.contains(q.questionId)
                              ? const Color(0xFFE53935)
                              : Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (q.visualSvgUrl != null) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF8F9FA),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxHeight: 140),
                        child: SvgPicture.network(
                          _api.visualUrlV2(q.questionId),
                          fit: BoxFit.contain,
                          placeholderBuilder: (_) => const SizedBox(
                            height: 60,
                            child: Center(
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                          errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],
                  Text(
                    q.stem,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.textDark,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ...List.generate(q.choices.length, (i) {
                    final isSelected = _selectedAnswer == i;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: GestureDetector(
                        onTap: () => _onAnswerTap(i),
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 14),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? KiwiColors.kiwiGreenLight
                                : Colors.white,
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: isSelected
                                  ? KiwiColors.kiwiGreen
                                  : Colors.grey.shade200,
                              width: 2,
                            ),
                          ),
                          child: Text(
                            q.choices[i],
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: isSelected
                                  ? FontWeight.w700
                                  : FontWeight.w500,
                              color: isSelected
                                  ? KiwiColors.kiwiGreenDark
                                  : KiwiColors.textDark,
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _selectedAnswer == null ? null : _submitAnswer,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiGreen,
                foregroundColor: Colors.white,
                disabledBackgroundColor: Colors.grey.shade200,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                textStyle: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              child: Text(
                  _index + 1 == _questions.length ? 'Finish' : 'Next'),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------
  // Results screen
  // -------------------------------------------------------------------

  Widget _buildResults() {
    final res = OnboardingResult.fromJson(_resultJson ?? {}, kidName: _kidName);
    final acc = res.overallAccuracy;
    final nameGreet = _kidName.isNotEmpty ? ', $_kidName' : '';
    final tone = acc >= 70 ? 'Wow$nameGreet!' : acc >= 40 ? 'Nice work$nameGreet!' : 'Great start$nameGreet!';

    return Padding(
      key: const ValueKey('results'),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 12),
          const Text('🎉', style: TextStyle(fontSize: 64)),
          const SizedBox(height: 12),
          Text(
            tone,
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiGreenDark,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'You got ${res.totalCorrect} of ${res.totalQuestions} right.',
            style: const TextStyle(fontSize: 16, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 24),
          if (res.strengths.isNotEmpty)
            _ResultCard(
              icon: Icons.star,
              color: KiwiColors.amber,
              title: 'You shined at',
              subtitle: res.strengths
                  .map(_prettyTopic)
                  .take(3)
                  .join(' • '),
            ),
          if (res.suggestedTopics.isNotEmpty)
            _ResultCard(
              icon: Icons.flag,
              color: KiwiColors.kiwiGreen,
              title: "Let's practice",
              subtitle: res.suggestedTopics
                  .map(_prettyTopic)
                  .take(3)
                  .join(' • '),
            ),
          _ResultCard(
            icon: Icons.trending_up,
            color: KiwiColors.indigo,
            title: 'Starting level',
            subtitle: 'Difficulty ${res.recommendedStartingDifficulty} of 100',
          ),
          const Spacer(),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => setState(() => _phase = _OnboardingPhase.plan),
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiGreen,
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
  // Plan — curriculum recommendation (Step 5)
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

    // Determine if user selected a curriculum (not olympiad)
    final isCurriculumUser = _curriculum != null &&
        _curriculum!.isNotEmpty &&
        _curriculum != 'olympiad';

    // Build the recommended plan: suggested (weakest) first, then strengths
    final topicNames = <String, String>{};
    for (final t in perTopic) {
      if (t is Map<String, dynamic>) {
        topicNames[t['topic_id'] as String? ?? ''] =
            t['topic_name'] as String? ?? '';
      }
    }

    // Plan items: for curriculum users, show curriculum-based plan;
    // for olympiad users, show topic-based plan from diagnostic results.
    final planItems = <_PlanItem>[];

    if (isCurriculumUser) {
      // Curriculum users: show chapter-based learning plan
      final curLabel = _curriculum!.toUpperCase();
      final gradeNum = _grade ?? 1;
      planItems.add(_PlanItem(
        topicId: 'chapters',
        topicName: '$curLabel Grade $gradeNum Chapters',
        badge: 'Start here',
        badgeColor: KiwiColors.kiwiGreen,
        reason: 'Follow your $curLabel curriculum chapter by chapter',
        isStrength: false,
      ));
      planItems.add(_PlanItem(
        topicId: 'adaptive',
        topicName: 'Adaptive Practice',
        badge: 'Daily',
        badgeColor: const Color(0xFFFF9800),
        reason: 'Smart practice based on your diagnostic results',
        isStrength: false,
      ));
      planItems.add(_PlanItem(
        topicId: 'olympiad',
        topicName: 'Olympiad Challenges',
        badge: 'Bonus',
        badgeColor: KiwiColors.indigo,
        reason: 'Push further with Kangaroo-style puzzles',
        isStrength: true,
      ));
    } else {
      // Olympiad users: show topic-based plan from diagnostic results
      for (int i = 0; i < suggestedTopics.length && i < 4; i++) {
        final tid = suggestedTopics[i];
        planItems.add(_PlanItem(
          topicId: tid,
          topicName: topicNames[tid] ?? _prettyTopic(tid),
          badge: i == 0 ? 'Start here' : 'Next',
          badgeColor: i == 0
              ? KiwiColors.kiwiGreen
              : const Color(0xFFFF9800),
          reason: i == 0
              ? 'Build confidence here first'
              : 'Practice will boost your score',
          isStrength: false,
        ));
      }
      for (final tid in strengths.take(2)) {
        if (!suggestedTopics.contains(tid)) {
          planItems.add(_PlanItem(
            topicId: tid,
            topicName: topicNames[tid] ?? _prettyTopic(tid),
            badge: 'Strong',
            badgeColor: KiwiColors.indigo,
            reason: 'Already doing great — revisit later',
            isStrength: true,
          ));
        }
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
          const Text('📋', style: TextStyle(fontSize: 48)),
          const SizedBox(height: 12),
          Text(
            'Your learning plan$nameGreet',
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w900,
              color: KiwiColors.kiwiGreenDark,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Based on your quiz, we recommend this path:',
            style: TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 20),
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
                    color: item.isStrength
                        ? Colors.grey.shade50
                        : Colors.white,
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
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _onFinish,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiGreen,
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

  // -------------------------------------------------------------------
  // Error
  // -------------------------------------------------------------------

  Widget _buildError() {
    // Sanitize error messages — never show raw API/backend text to kids.
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
                backgroundColor: KiwiColors.kiwiGreen,
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
    // counting_observation → Counting & Observation
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

class _CurriculumCard extends StatelessWidget {
  final String label;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _CurriculumCard({
    required this.label,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.3), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.08),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: color,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 12,
                      color: KiwiColors.textMid,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, color: color.withOpacity(0.5)),
          ],
        ),
      ),
    );
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

// ===========================================================================
// Plan item model (Step 5 — curriculum recommendation)
// ===========================================================================

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
