import 'package:flutter/material.dart';

import '../models/companion.dart';
import '../services/api_client.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import 'question_screen_v2.dart';

/// Learning Path screen (Task #197 — UI layer).
///
/// Renders the per-student plan returned by `/v2/learning-path` as a vertical
/// timeline of "stops". Each stop shows the topic, the reason it was chosen
/// (e.g. "Weakest topic — let's strengthen this"), the target difficulty,
/// and a pill that hints at how many questions are recommended.
///
/// Tapping the first not-yet-mastered stop launches QuestionScreenV2 with
/// the recommended topic and difficulty, so the kid moves seamlessly from
/// "see the plan" to "do the next thing".
class LearningPathScreen extends StatefulWidget {
  final String userId;
  final int grade;
  final CompanionService? companionService;

  const LearningPathScreen({
    super.key,
    required this.userId,
    required this.grade,
    this.companionService,
  });

  @override
  State<LearningPathScreen> createState() => _LearningPathScreenState();
}

class _LearningPathScreenState extends State<LearningPathScreen> {
  final ApiClient _api = ApiClient();
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _api.getLearningPath(
        userId: widget.userId,
        grade: widget.grade,
      );
      if (!mounted) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _startStop(Map<String, dynamic> stop) {
    final topicId = stop['topic_id'] as String?;
    final topicName = stop['topic_name'] as String? ?? 'Practice';
    if (topicId == null) return;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionScreenV2(
          topicId: topicId,
          topicName: topicName,
          userId: widget.userId,
          grade: widget.grade,
          companionService: widget.companionService,
          onBackToHome: () {
            Navigator.of(context).pop();
            _load(); // refresh path on return
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
      backgroundColor: KiwiColors.background,
      appBar: AppBar(
        title: const Text(
          'Your Learning Path',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
        backgroundColor: Colors.white,
        foregroundColor: KiwiColors.textDark,
        elevation: 0,
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return _ErrorView(message: _error!, onRetry: _load);
    }
    final data = _data;
    if (data == null) {
      return const Center(child: Text('No learning path available.'));
    }

    final summary = (data['summary'] as String?) ??
        "Here's the plan we put together for you.";
    final path = (data['path'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();

    // First not-yet-mastered stop is the "current" one — kid taps Start there.
    int currentIdx = path.indexWhere(
      (s) => (s['mastery_label'] as String? ?? '') != 'mastered',
    );
    if (currentIdx < 0) currentIdx = 0;

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 28),
        children: [
          _buildHeader(summary, path.length),
          const SizedBox(height: 16),
          for (int i = 0; i < path.length; i++)
            _StopCard(
              stop: path[i],
              isFirst: i == 0,
              isLast: i == path.length - 1,
              isCurrent: i == currentIdx,
              onStart: i == currentIdx ? () => _startStop(path[i]) : null,
            ),
        ],
      ),
    );
  }

  Widget _buildHeader(String summary, int stops) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFE8F5E9), Color(0xFFFFFBF5)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: KiwiColors.kiwiGreen.withOpacity(0.25)),
      ),
      child: Row(
        children: [
          if (widget.companionService != null &&
              widget.companionService!.isLoaded)
            const Padding(
              padding: EdgeInsets.only(right: 10),
              child: Text('\u{1F95D}', style: TextStyle(fontSize: 32)),
            )
          else
            const Padding(
              padding: EdgeInsets.only(right: 10),
              child: Text('\u{1F4CD}', style: TextStyle(fontSize: 28)),
            ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  summary,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '$stops stop${stops == 1 ? '' : 's'} on your path',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade700,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// =============================================================================
// Stop card with timeline rail
// =============================================================================

class _StopCard extends StatelessWidget {
  final Map<String, dynamic> stop;
  final bool isFirst;
  final bool isLast;
  final bool isCurrent;
  final VoidCallback? onStart;

  const _StopCard({
    required this.stop,
    required this.isFirst,
    required this.isLast,
    required this.isCurrent,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    final mastery = (stop['mastery_label'] as String?) ?? 'learning';
    final isReview = stop['review'] == true;
    final isMastered = mastery == 'mastered';

    final accent = isMastered
        ? KiwiColors.pathDone
        : isCurrent
            ? KiwiColors.pathCurrent
            : KiwiColors.kiwiGreen;

    final difficulty = (stop['target_difficulty'] as num?)?.toInt() ?? 0;
    final qCount = (stop['questions_to_attempt'] as num?)?.toInt() ?? 5;
    final reason = (stop['reason'] as String?) ?? '';
    final topicName = (stop['topic_name'] as String?) ?? 'Topic';
    final seq = (stop['sequence'] as num?)?.toInt() ?? 0;

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline rail
          SizedBox(
            width: 40,
            child: Column(
              children: [
                // Top connector
                Expanded(
                  flex: 1,
                  child: Container(
                    width: 2,
                    color: isFirst ? Colors.transparent : Colors.grey.shade300,
                  ),
                ),
                // Node
                Container(
                  width: 30,
                  height: 30,
                  decoration: BoxDecoration(
                    color: accent,
                    shape: BoxShape.circle,
                    boxShadow: [
                      if (isCurrent)
                        BoxShadow(
                          color: accent.withOpacity(0.4),
                          blurRadius: 10,
                          spreadRadius: 2,
                        ),
                    ],
                  ),
                  alignment: Alignment.center,
                  child: isMastered
                      ? const Icon(Icons.check, color: Colors.white, size: 18)
                      : Text(
                          '$seq',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                          ),
                        ),
                ),
                // Bottom connector
                Expanded(
                  flex: 5,
                  child: Container(
                    width: 2,
                    color: isLast ? Colors.transparent : Colors.grey.shade300,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Card content
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 10, top: 4),
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: isCurrent
                        ? accent.withOpacity(0.5)
                        : Colors.grey.shade200,
                    width: isCurrent ? 1.5 : 1,
                  ),
                  boxShadow: isCurrent
                      ? [
                          BoxShadow(
                            color: accent.withOpacity(0.12),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                        ]
                      : null,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            topicName,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                              color: KiwiColors.textDark,
                            ),
                          ),
                        ),
                        if (isReview)
                          _Pill(
                            text: 'Review',
                            bg: KiwiColors.gemBlue.withOpacity(0.12),
                            fg: KiwiColors.gemBlue,
                          )
                        else
                          _Pill(
                            text: mastery,
                            bg: accent.withOpacity(0.12),
                            fg: accent,
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    if (reason.isNotEmpty)
                      Text(
                        reason,
                        style: TextStyle(
                          fontSize: 12.5,
                          color: Colors.grey.shade700,
                          height: 1.4,
                        ),
                      ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        _MiniMetric(
                          icon: Icons.show_chart,
                          label: 'Level $difficulty',
                        ),
                        const SizedBox(width: 12),
                        _MiniMetric(
                          icon: Icons.list_alt,
                          label: '$qCount questions',
                        ),
                      ],
                    ),
                    if (onStart != null) ...[
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: onStart,
                          icon: const Icon(Icons.play_arrow_rounded, size: 20),
                          label: const Text(
                            'Start this stop',
                            style: TextStyle(fontWeight: FontWeight.w800),
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: accent,
                            foregroundColor: Colors.white,
                            padding:
                                const EdgeInsets.symmetric(vertical: 11),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  final String text;
  final Color bg;
  final Color fg;
  const _Pill({required this.text, required this.bg, required this.fg});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 10.5,
          fontWeight: FontWeight.w800,
          color: fg,
          letterSpacing: 0.2,
        ),
      ),
    );
  }
}

class _MiniMetric extends StatelessWidget {
  final IconData icon;
  final String label;
  const _MiniMetric({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: Colors.grey.shade600),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            color: Colors.grey.shade700,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off, size: 56, color: Colors.grey.shade400),
            const SizedBox(height: 12),
            Text(
              "Couldn't load your path",
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 12.5,
                color: Colors.grey.shade600,
              ),
            ),
            const SizedBox(height: 14),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Try again'),
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiGreen,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
