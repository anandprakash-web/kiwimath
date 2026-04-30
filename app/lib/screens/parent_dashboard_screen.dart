import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';

/// Parent Dashboard (Task #199).
///
/// Shows a snapshot of the child's progress for a parent reviewing the app:
///   • Summary cards (accuracy, total questions, streak, level)
///   • Per-topic progress bars
///   • Strengths / needs-practice section
///   • Plain-language recommendations
///   • Recent activity list
class ParentDashboardScreen extends StatefulWidget {
  final String userId;
  final String? childName;

  const ParentDashboardScreen({
    super.key,
    required this.userId,
    this.childName,
  });

  @override
  State<ParentDashboardScreen> createState() => _ParentDashboardScreenState();
}

class _ParentDashboardScreenState extends State<ParentDashboardScreen> {
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
      final data = await _api.getParentDashboard(userId: widget.userId);
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

  @override
  Widget build(BuildContext context) {
    final childName = widget.childName ?? 'your child';

    return Scaffold(
      backgroundColor: KiwiColors.background,
      appBar: AppBar(
        title: Text(
          'How $childName is doing',
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        backgroundColor: Colors.white,
        foregroundColor: KiwiColors.textDark,
        elevation: 0,
        actions: [
          IconButton(
            onPressed: _loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? _buildError()
                : _buildBody(),
      ),
    );
  }

  Widget _buildError() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 80),
        const Icon(Icons.cloud_off, size: 56, color: Colors.redAccent),
        const SizedBox(height: 12),
        const Text(
          'Could not load the dashboard',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 8),
        Text(
          _error ?? 'Unknown error',
          textAlign: TextAlign.center,
          style: const TextStyle(color: KiwiColors.textMuted),
        ),
        const SizedBox(height: 16),
        TextButton(onPressed: _load, child: const Text('Try again')),
      ],
    );
  }

  Widget _buildBody() {
    final data = _data!;
    final overallAccuracy =
        (data['overall_accuracy'] as num?)?.toDouble() ?? 0.0;
    final totalQuestions = (data['total_questions'] as num?)?.toInt() ?? 0;
    final correctQuestions =
        (data['correct_questions'] as num?)?.toInt() ?? 0;
    final currentStreak = (data['current_streak'] as num?)?.toInt() ?? 0;
    final level = (data['level'] as num?)?.toInt() ?? 1;
    final levelName = data['level_name'] as String?;
    final xp = (data['xp'] as num?)?.toInt() ?? 0;
    final topics = (data['topics'] as List<dynamic>? ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    final strengths =
        (data['strengths'] as List<dynamic>? ?? []).map((e) => e.toString()).toList();
    final weaknesses =
        (data['needs_practice'] as List<dynamic>? ?? []).map((e) => e.toString()).toList();
    final recommendations = (data['recommendations'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    final recent = (data['recent_activity'] as List<dynamic>? ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Summary cards in a 2x2 grid
        Row(
          children: [
            Expanded(
              child: _SummaryCard(
                label: 'Accuracy',
                value: '${overallAccuracy.toStringAsFixed(0)}%',
                icon: Icons.track_changes,
                color: KiwiColors.kiwiGreen,
                subtitle: '$correctQuestions of $totalQuestions correct',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _SummaryCard(
                label: 'Streak',
                value: '$currentStreak',
                icon: Icons.local_fire_department,
                color: KiwiColors.streakOrange,
                subtitle: 'days in a row',
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: _SummaryCard(
                label: 'Level',
                value: '$level',
                icon: Icons.shield,
                color: KiwiColors.indigo,
                subtitle: levelName ?? 'Math Explorer',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _SummaryCard(
                label: 'XP',
                value: '$xp',
                icon: Icons.bolt,
                color: KiwiColors.xpPurple,
                subtitle: 'experience earned',
              ),
            ),
          ],
        ),

        // Recommendations
        if (recommendations.isNotEmpty) ...[
          const SizedBox(height: 24),
          const _SectionHeader(title: 'Recommendations'),
          const SizedBox(height: 8),
          ...recommendations.map((r) => _RecommendationTile(text: r)),
        ],

        // Strengths
        if (strengths.isNotEmpty) ...[
          const SizedBox(height: 24),
          const _SectionHeader(title: 'Strengths', icon: Icons.star),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: strengths
                .map((id) => _Pill(
                      text: _prettyTopic(id),
                      color: KiwiColors.amber,
                    ))
                .toList(),
          ),
        ],

        // Needs practice
        if (weaknesses.isNotEmpty) ...[
          const SizedBox(height: 16),
          const _SectionHeader(title: 'Needs practice', icon: Icons.flag),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: weaknesses
                .map((id) => _Pill(
                      text: _prettyTopic(id),
                      color: KiwiColors.coral,
                    ))
                .toList(),
          ),
        ],

        // Per-topic progress
        const SizedBox(height: 24),
        const _SectionHeader(title: 'Topic breakdown'),
        const SizedBox(height: 8),
        ...topics.map(_buildTopicTile),

        // Recent activity
        if (recent.isNotEmpty) ...[
          const SizedBox(height: 24),
          const _SectionHeader(title: 'Recent activity'),
          const SizedBox(height: 8),
          ...recent.map(_buildActivityTile),
        ],
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildTopicTile(Map<String, dynamic> t) {
    final name = t['topic_name']?.toString() ?? '';
    final accuracy = (t['accuracy'] as num?)?.toDouble() ?? 0.0;
    final attempts = (t['attempts'] as num?)?.toInt() ?? 0;
    final mastery = t['mastery']?.toString() ?? 'learning';
    final color = _masteryColor(mastery);

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  mastery,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (accuracy / 100).clamp(0.0, 1.0),
              minHeight: 6,
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${accuracy.toStringAsFixed(0)}% accuracy • $attempts answered',
            style: const TextStyle(fontSize: 12, color: KiwiColors.textMuted),
          ),
        ],
      ),
    );
  }

  Widget _buildActivityTile(Map<String, dynamic> a) {
    final correct = a['correct'] == true;
    final qid = a['question_id']?.toString() ?? '';
    final topicId = a['topic_id']?.toString() ?? '';
    final difficulty = (a['difficulty'] as num?)?.toInt() ?? 0;
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          Icon(
            correct ? Icons.check_circle : Icons.cancel,
            color: correct ? KiwiColors.correct : KiwiColors.wrong,
            size: 18,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${_prettyTopic(topicId)} · $qid',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textDark,
                  ),
                ),
                Text(
                  'Difficulty $difficulty',
                  style: const TextStyle(
                    fontSize: 11,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _masteryColor(String label) {
    switch (label) {
      case 'mastered':
        return KiwiColors.kiwiGreen;
      case 'practising':
        return KiwiColors.amber;
      case 'learning':
      default:
        return KiwiColors.coral;
    }
  }

  String _prettyTopic(String id) {
    return id
        .split('_')
        .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}

// ===========================================================================
// Sub-widgets
// ===========================================================================

class _SummaryCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? subtitle;

  const _SummaryCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.14),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, size: 16, color: color),
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: const TextStyle(
                  fontSize: 12,
                  color: KiwiColors.textMuted,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            value,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w900,
              color: KiwiColors.textDark,
            ),
          ),
          if (subtitle != null) ...[
            const SizedBox(height: 2),
            Text(
              subtitle!,
              style: const TextStyle(
                fontSize: 11,
                color: KiwiColors.textMuted,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final IconData? icon;

  const _SectionHeader({required this.title, this.icon});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        if (icon != null) ...[
          Icon(icon, size: 16, color: KiwiColors.textMid),
          const SizedBox(width: 6),
        ],
        Text(
          title,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textMid,
            letterSpacing: 0.4,
          ),
        ),
      ],
    );
  }
}

class _Pill extends StatelessWidget {
  final String text;
  final Color color;

  const _Pill({required this.text, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }
}

class _RecommendationTile extends StatelessWidget {
  final String text;
  const _RecommendationTile({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: KiwiColors.kiwiGreenLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: KiwiColors.kiwiGreen.withOpacity(0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.lightbulb,
              size: 18, color: KiwiColors.kiwiGreenDark),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                fontSize: 13,
                color: KiwiColors.textDark,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
