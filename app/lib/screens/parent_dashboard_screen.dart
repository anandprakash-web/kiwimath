import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';

/// Parent Dashboard v4 — clean redesign focused on what parents care about:
///   1. Overall score (accuracy %) with trend indicator
///   2. Weekly goal progress (questions this week vs target)
///   3. Strengths (green) & needs practice (orange) pills
///   4. Topic breakdown with progress bars
///   5. Recommendations in plain language
///
/// No AppBar — uses in-body header consistent with home/path screens.
class ParentDashboardScreen extends StatefulWidget {
  final String userId;
  final String? childName;
  final bool embedded;
  final int? weeklyGoal;
  final String? curriculum;

  const ParentDashboardScreen({
    super.key,
    required this.userId,
    this.childName,
    this.embedded = false,
    this.weeklyGoal,
    this.curriculum,
  });

  @override
  State<ParentDashboardScreen> createState() => _ParentDashboardScreenState();
}

class _ParentDashboardScreenState extends State<ParentDashboardScreen> {
  final ApiClient _api = ApiClient();
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  static const _teal = Color(0xFF1D9E75);
  static const _orange = Color(0xFFFF6D00);
  static const _coral = Color(0xFFE85D4A);
  static const _blue = Color(0xFF1976D2);

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant ParentDashboardScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.userId != oldWidget.userId) _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _api.getParentDashboard(
        userId: widget.userId,
        curriculum: widget.curriculum,
      );
      if (!mounted) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      String friendlyMsg;
      final raw = e.toString();
      if (raw.contains('SocketException') || raw.contains('Connection')) {
        friendlyMsg =
            "Can't reach the server right now. Check your internet and try again.";
      } else {
        friendlyMsg =
            "Something went wrong loading the dashboard. Give it another try.";
      }
      setState(() {
        _error = friendlyMsg;
        _loading = false;
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(1); // Parent view uses default tier
    return Scaffold(
      backgroundColor: tier.colors.background,
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? _buildError(tier)
                : _buildBody(tier),
      ),
    );
  }

  Widget _buildError(KiwiTier tier) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_rounded, size: 48, color: Colors.grey.shade300),
            const SizedBox(height: 12),
            Text(
              'Could not load the dashboard',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: tier.colors.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: tier.colors.textPrimary.withOpacity(0.6),
                height: 1.4,
              ),
            ),
            const SizedBox(height: 18),
            GestureDetector(
              onTap: _load,
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: _teal,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Try again',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody(KiwiTier tier) {
    final data = _data!;
    final childName = widget.childName ?? 'your child';

    final overallAccuracy =
        (data['overall_accuracy'] as num?)?.toDouble() ?? 0.0;
    final totalQuestions = (data['total_questions'] as num?)?.toInt() ?? 0;
    final currentStreak = (data['current_streak'] as num?)?.toInt() ?? 0;
    final topics = (data['topics'] as List<dynamic>? ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    final strengths = (data['strengths'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    final weaknesses = (data['needs_practice'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    final recommendations = (data['recommendations'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();

    // Weekly goal: default to 35 questions/week (5/day)
    final weeklyGoal = widget.weeklyGoal ?? 35;
    final weeklyDone = (data['weekly_questions'] as num?)?.toInt() ??
        (totalQuestions > weeklyGoal ? weeklyGoal : totalQuestions);

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          // Header
          _buildHeader(childName, tier),
          const SizedBox(height: 18),

          // Score card (big accuracy circle)
          _buildScoreCard(overallAccuracy, currentStreak, totalQuestions, tier),
          const SizedBox(height: 14),

          // Weekly goal
          _buildWeeklyGoal(weeklyDone, weeklyGoal, tier),
          const SizedBox(height: 18),

          // Strengths & weaknesses
          if (strengths.isNotEmpty || weaknesses.isNotEmpty) ...[
            _buildStrengthsWeaknesses(strengths, weaknesses, tier),
            const SizedBox(height: 18),
          ],

          // Topic breakdown
          _buildSectionLabel('Topic breakdown', tier),
          const SizedBox(height: 8),
          ...topics.map((t) => _buildTopicRow(t, tier)),

          // Recommendations
          if (recommendations.isNotEmpty) ...[
            const SizedBox(height: 18),
            _buildSectionLabel('Tips for you', tier),
            const SizedBox(height: 8),
            ...recommendations.map((r) => _buildRecommendation(r, tier)),
          ],
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Widgets
  // ---------------------------------------------------------------------------

  Widget _buildHeader(String childName, KiwiTier tier) {
    return Row(
      children: [
        Expanded(
          child: Text(
            "How $childName is doing",
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: tier.colors.textPrimary,
            ),
          ),
        ),
        if (_loading)
          const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        else
          GestureDetector(
            onTap: _load,
            child: Icon(
              Icons.refresh_rounded,
              size: 22,
              color: tier.colors.textPrimary.withOpacity(0.5),
            ),
          ),
      ],
    );
  }

  Widget _buildScoreCard(
    double accuracy,
    int streak,
    int totalQ,
    KiwiTier tier,
  ) {
    final scoreColor = accuracy >= 70
        ? _teal
        : accuracy >= 50
            ? _orange
            : _coral;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Row(
        children: [
          // Big accuracy circle
          SizedBox(
            width: 72,
            height: 72,
            child: Stack(
              alignment: Alignment.center,
              children: [
                SizedBox(
                  width: 72,
                  height: 72,
                  child: CircularProgressIndicator(
                    value: (accuracy / 100).clamp(0.0, 1.0),
                    strokeWidth: 6,
                    backgroundColor: scoreColor.withOpacity(0.12),
                    valueColor: AlwaysStoppedAnimation<Color>(scoreColor),
                  ),
                ),
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '${accuracy.round()}%',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                        color: scoreColor,
                      ),
                    ),
                    Text(
                      'accuracy',
                      style: TextStyle(
                        fontSize: 10,
                        color: tier.colors.textPrimary.withOpacity(0.5),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 18),
          // Stats column
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMiniStat(
                  Icons.local_fire_department_rounded,
                  '$streak day streak',
                  _orange,
                  tier,
                ),
                const SizedBox(height: 10),
                _buildMiniStat(
                  Icons.quiz_outlined,
                  '$totalQ questions answered',
                  _blue,
                  tier,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniStat(
      IconData icon, String label, Color color, KiwiTier tier) {
    return Row(
      children: [
        Container(
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, size: 15, color: color),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: tier.colors.textPrimary,
          ),
        ),
      ],
    );
  }

  Widget _buildWeeklyGoal(int done, int goal, KiwiTier tier) {
    final fraction = goal > 0 ? (done / goal).clamp(0.0, 1.0) : 0.0;
    final isComplete = done >= goal;

    return Container(
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
              Icon(
                isComplete ? Icons.check_circle : Icons.flag_rounded,
                size: 18,
                color: isComplete ? _teal : _orange,
              ),
              const SizedBox(width: 8),
              Text(
                'Weekly goal',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: tier.colors.textPrimary,
                ),
              ),
              const Spacer(),
              Text(
                '$done / $goal questions',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isComplete ? _teal : _orange,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: fraction,
              minHeight: 7,
              backgroundColor: (isComplete ? _teal : _orange).withOpacity(0.12),
              valueColor:
                  AlwaysStoppedAnimation<Color>(isComplete ? _teal : _orange),
            ),
          ),
          if (isComplete) ...[
            const SizedBox(height: 6),
            Text(
              'Goal reached! Great job this week.',
              style: TextStyle(
                fontSize: 11.5,
                color: _teal,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStrengthsWeaknesses(
    List<String> strengths,
    List<String> weaknesses,
    KiwiTier tier,
  ) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (strengths.isNotEmpty) ...[
            Row(
              children: [
                Icon(Icons.star_rounded, size: 16, color: _teal),
                const SizedBox(width: 6),
                Text(
                  'Strengths',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: tier.colors.textPrimary.withOpacity(0.6),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: strengths
                  .map((id) => _buildPill(_prettyTopic(id), _teal))
                  .toList(),
            ),
          ],
          if (strengths.isNotEmpty && weaknesses.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Divider(height: 1, color: Colors.grey.shade200),
            ),
          if (weaknesses.isNotEmpty) ...[
            Row(
              children: [
                Icon(Icons.trending_up_rounded, size: 16, color: _orange),
                const SizedBox(width: 6),
                Text(
                  'Needs practice',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: tier.colors.textPrimary.withOpacity(0.6),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: weaknesses
                  .map((id) => _buildPill(_prettyTopic(id), _orange))
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildPill(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }

  Widget _buildSectionLabel(String title, KiwiTier tier) {
    return Text(
      title,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w800,
        color: tier.colors.textPrimary.withOpacity(0.6),
      ),
    );
  }

  Widget _buildTopicRow(Map<String, dynamic> t, KiwiTier tier) {
    final name = t['topic_name']?.toString() ?? '';
    final accuracy = (t['accuracy'] as num?)?.toDouble() ?? 0.0;
    final mastery = t['mastery']?.toString() ?? 'learning';

    final color = mastery == 'mastered'
        ? _teal
        : mastery == 'practising'
            ? _orange
            : _coral;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
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
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: tier.colors.textPrimary,
                    ),
                  ),
                ),
                Text(
                  '${accuracy.round()}%',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: LinearProgressIndicator(
                value: (accuracy / 100).clamp(0.0, 1.0),
                minHeight: 5,
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendation(String text, KiwiTier tier) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _teal.withOpacity(0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.lightbulb_outline_rounded, size: 16, color: _teal),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 13,
                color: tier.colors.textPrimary,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  String _prettyTopic(String id) {
    return _topicNameFixups[id] ?? id.split('_').map((w) {
      if (w.isEmpty) return w;
      if (w == '3d') return '3D';
      return '${w[0].toUpperCase()}${w.substring(1)}';
    }).join(' ');
  }

  static const _topicNameFixups = <String, String>{
    'counting_observation': 'Counting & Observation',
    'arithmetic_missing_numbers': 'Arithmetic & Missing Numbers',
    'patterns_sequences': 'Patterns & Sequences',
    'logic_ordering': 'Logic & Ordering',
    'spatial_reasoning_3d': 'Spatial Reasoning & 3D',
    'shapes_folding_symmetry': 'Shapes, Folding & Symmetry',
    'word_problems_stories': 'Word Problems & Stories',
    'number_puzzles_games': 'Number Puzzles & Games',
  };
}
