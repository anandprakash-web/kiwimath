import 'package:flutter/material.dart';

import '../models/question.dart';
import '../models/session.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/feedback_banner.dart';
import '../widgets/option_card.dart';
import '../widgets/svg_visual.dart';

/// Main screen — implements the full Kiwimath learning loop:
///
///   parentQuestion
///      │
///      ├── tap correct → parentCorrect → (short cheer) → next parentQuestion
///      │
///      └── tap wrong
///             ↓
///        wrongFeedback  (warm banner explaining the misconception)
///             ↓  tap "Let's try it step by step"
///        stepDownQuestion (easier scaffolding Q with inherited params)
///             ├── tap correct → advance to next step-down
///             │       │
///             │       └── if last step → stepDownComplete → next parentQuestion
///             │
///             └── tap wrong → stepDownWrongFeedback → auto-advance to next step-down
///                                                       (step-downs have no
///                                                        deeper scaffolding; we
///                                                        just show the answer)
class QuestionScreen extends StatefulWidget {
  final String locale;
  const QuestionScreen({super.key, this.locale = 'global'});

  @override
  State<QuestionScreen> createState() => _QuestionScreenState();
}

class _QuestionScreenState extends State<QuestionScreen> {
  final ApiClient _api = ApiClient();

  ScreenPhase _phase = ScreenPhase.parentQuestion;
  KiwiQuestion? _question; // current Q on screen (parent or step-down)
  StepDownSession? _session; // non-null only when in step-down mode
  int? _selectedIndex;
  String? _error;

  int _streak = 0;
  int _gems = 0;

  @override
  void initState() {
    super.initState();
    _loadNextParent();
  }

  // ---------------------------------------------------------------------
  // Loaders
  // ---------------------------------------------------------------------

  Future<void> _loadNextParent() async {
    setState(() {
      _phase = ScreenPhase.parentQuestion;
      _question = null;
      _session = null;
      _selectedIndex = null;
      _error = null;
    });
    try {
      final q = await _api.nextQuestion(locale: widget.locale);
      if (!mounted) return;
      setState(() => _question = q);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  Future<void> _loadCurrentStepDown() async {
    final s = _session;
    if (s == null) return;
    final id = s.currentStepId;
    if (id == null) return;

    setState(() {
      _phase = ScreenPhase.stepDownQuestion;
      _question = null;
      _selectedIndex = null;
    });
    try {
      final q = await _api.questionById(
        id,
        locale: widget.locale,
        inheritedParams: s.inheritedParams(),
      );
      if (!mounted) return;
      setState(() => _question = q);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  // ---------------------------------------------------------------------
  // Event handlers
  // ---------------------------------------------------------------------

  void _onOptionTap(int index) {
    final q = _question;
    if (q == null || _selectedIndex != null) return;

    setState(() => _selectedIndex = index);
    final isCorrect = index == q.correctIndex;

    // Decide next phase based on current phase + correctness.
    switch (_phase) {
      case ScreenPhase.parentQuestion:
        if (isCorrect) {
          _streak++;
          _gems += 5;
          _phase = ScreenPhase.parentCorrect;
          Future.delayed(const Duration(seconds: 2), () {
            if (mounted) _loadNextParent();
          });
        } else {
          _streak = 0;
          final diag = q.wrongOptionDiagnosis[index] ?? 'wrong_answer';
          final fb = q.wrongOptionFeedback[index] ??
              "Let's try that one more time, step by step.";
          final path = q.wrongOptionStepDownPath[index] ?? const <String>[];
          // If the author didn't provide a step-down path, skip straight to next parent.
          if (path.isEmpty) {
            Future.delayed(const Duration(seconds: 2), () {
              if (mounted) _loadNextParent();
            });
          } else {
            _session = StepDownSession(
              parent: q,
              diagnosis: diag,
              path: path,
              openingFeedback: fb,
            );
            // Brief pause to show the red state, then transition to feedback banner.
            Future.delayed(const Duration(milliseconds: 900), () {
              if (mounted) {
                setState(() {
                  _phase = ScreenPhase.wrongFeedback;
                  _selectedIndex = null;
                });
              }
            });
          }
        }
        break;

      case ScreenPhase.stepDownQuestion:
        if (isCorrect) {
          _gems += 2; // smaller reward for step-downs
          Future.delayed(const Duration(milliseconds: 1500), () {
            if (!mounted) return;
            final s = _session!;
            s.advance();
            if (s.isComplete) {
              setState(() => _phase = ScreenPhase.stepDownComplete);
            } else {
              _loadCurrentStepDown();
            }
          });
        } else {
          // Step-downs have no deeper scaffolding — show correct briefly, advance.
          _phase = ScreenPhase.stepDownWrongFeedback;
          Future.delayed(const Duration(seconds: 2), () {
            if (!mounted) return;
            final s = _session!;
            s.advance();
            if (s.isComplete) {
              setState(() => _phase = ScreenPhase.stepDownComplete);
            } else {
              _loadCurrentStepDown();
            }
          });
        }
        break;

      default:
        break;
    }

    setState(() {});
  }

  void _onContinueFromWrongFeedback() {
    _loadCurrentStepDown();
  }

  void _onContinueFromComplete() {
    _loadNextParent();
  }

  // ---------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: KiwiColors.kiwiGreen,
        foregroundColor: Colors.white,
        title: Row(
          children: [
            const Text('Kiwimath 🥝',
                style: TextStyle(fontWeight: FontWeight.w700)),
            if (_phase == ScreenPhase.stepDownQuestion ||
                _phase == ScreenPhase.stepDownWrongFeedback)
              Padding(
                padding: const EdgeInsets.only(left: 12),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'Step ${(_session?.currentStep ?? 0) + 1} of ${_session?.path.length ?? 0}',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
          ],
        ),
        actions: [
          _StatChip(icon: Icons.local_fire_department, value: '$_streak'),
          const SizedBox(width: 8),
          _StatChip(icon: Icons.diamond, value: '$_gems', color: KiwiColors.gemGold),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.logout, size: 20),
            tooltip: 'Sign out',
            onPressed: () async {
              await AuthService().signOut();
              // AuthWrapper listens to the stream and swaps back to SignInScreen.
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_error != null) return _ErrorView(error: _error!, onRetry: _loadNextParent);

    switch (_phase) {
      case ScreenPhase.wrongFeedback:
        return _buildFeedbackScreen();
      case ScreenPhase.stepDownComplete:
        return _buildSuccessScreen();
      default:
        if (_question == null) {
          return const Center(child: CircularProgressIndicator());
        }
        return _buildQuestionScreen();
    }
  }

  Widget _buildQuestionScreen() {
    final q = _question!;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (q.visual != null) ...[
              KiwiVisualWidget(visual: q.visual!),
              const SizedBox(height: 16),
            ],
            Text(
              q.stem,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 24),
            Expanded(
              child: ListView.builder(
                itemCount: q.options.length,
                itemBuilder: (context, i) {
                  return OptionCard(
                    text: q.options[i].text,
                    state: _stateFor(i),
                    onTap: () => _onOptionTap(i),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeedbackScreen() {
    final s = _session!;
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Center(
          child: FeedbackBanner(
            message: s.openingFeedback,
            ctaLabel: "Let's try it step by step →",
            onContinue: _onContinueFromWrongFeedback,
          ),
        ),
      ),
    );
  }

  Widget _buildSuccessScreen() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Center(
          child: FeedbackBanner(
            tone: BannerTone.success,
            message: "Awesome — you worked through it! 🎉\nReady for the next one?",
            ctaLabel: "Next question →",
            onContinue: _onContinueFromComplete,
          ),
        ),
      ),
    );
  }

  OptionState _stateFor(int idx) {
    if (_selectedIndex == null) return OptionState.idle;
    final correctIdx = _question!.correctIndex;
    if (idx == _selectedIndex) {
      return idx == correctIdx
          ? OptionState.selectedCorrect
          : OptionState.selectedWrong;
    }
    // Highlight the correct answer green if the kid picked wrong.
    if (_selectedIndex != correctIdx && idx == correctIdx) {
      return OptionState.selectedCorrect;
    }
    return OptionState.disabled;
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String value;
  final Color? color;
  const _StatChip({required this.icon, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: color ?? Colors.white),
        const SizedBox(width: 4),
        Text(
          value,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;
  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
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
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
