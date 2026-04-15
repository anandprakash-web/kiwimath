import 'package:flutter/material.dart';

import '../models/question.dart';
import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/option_card.dart';
import '../widgets/svg_visual.dart';

/// The main "do math" screen. v0 flow:
/// - Fetch a question from the backend on load.
/// - Show stem + optional SVG + multiple-choice options.
/// - On tap: show correct/wrong feedback, print diagnosis to console.
/// - After 2 seconds, fetch the next question.
///
/// Week 3 Day 3–4 will add the step-down navigation flow.
class QuestionScreen extends StatefulWidget {
  final String locale;
  const QuestionScreen({super.key, this.locale = 'global'});

  @override
  State<QuestionScreen> createState() => _QuestionScreenState();
}

class _QuestionScreenState extends State<QuestionScreen> {
  final ApiClient _api = ApiClient();
  KiwiQuestion? _question;
  String? _error;
  int? _selectedIndex;
  int _streak = 0;
  int _gems = 0;

  @override
  void initState() {
    super.initState();
    _loadNext();
  }

  Future<void> _loadNext() async {
    setState(() {
      _question = null;
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

  void _onOptionTap(int index) {
    final q = _question;
    if (q == null || _selectedIndex != null) return;

    final isCorrect = index == q.correctIndex;
    setState(() {
      _selectedIndex = index;
      if (isCorrect) {
        _streak++;
        _gems += 5;
      } else {
        _streak = 0;
      }
    });

    // Log the diagnosis (Week 3 Day 3 will turn this into a real step-down flow)
    if (!isCorrect) {
      final diagnosis = q.wrongOptionDiagnosis[index];
      final path = q.wrongOptionStepDownPath[index];
      debugPrint('[kiwimath] wrong answer: $diagnosis, step-downs: $path');
    }

    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) _loadNext();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: KiwiColors.kiwiGreen,
        foregroundColor: Colors.white,
        title: const Text('Kiwimath 🥝', style: TextStyle(fontWeight: FontWeight.w700)),
        actions: [
          _StatChip(icon: Icons.local_fire_department, value: '$_streak'),
          const SizedBox(width: 8),
          _StatChip(icon: Icons.diamond, value: '$_gems', color: KiwiColors.gemGold),
          const SizedBox(width: 16),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_error != null) return _ErrorView(error: _error!, onRetry: _loadNext);
    if (_question == null) return const Center(child: CircularProgressIndicator());

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
                  final state = _stateFor(i);
                  return OptionCard(
                    text: q.options[i].text,
                    state: state,
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

  OptionState _stateFor(int idx) {
    if (_selectedIndex == null) return OptionState.idle;
    if (idx == _selectedIndex) {
      final correct = _question!.correctIndex == idx;
      return correct ? OptionState.selectedCorrect : OptionState.selectedWrong;
    }
    // If we picked wrong, still highlight the correct one in green so the child sees it.
    if (_selectedIndex != _question!.correctIndex && idx == _question!.correctIndex) {
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
              'Can\'t reach Kiwimath backend',
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
