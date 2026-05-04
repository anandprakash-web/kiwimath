import 'package:flutter/material.dart';

import '../models/clan.dart';
import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/proficiency_card.dart';
import 'benchmark_test_screen.dart';

/// Parent Dashboard v6 — warm, encouraging, meaningful.
///
/// Designed for parents who care about:
///   1. "Is my child actually learning?" (progress narrative)
///   2. "What should I encourage?" (strengths + areas to grow)
///   3. "Is my child practicing enough?" (gentle weekly check)
///
/// No clinical stat dumps. Warm Kiwimath orange + cream, encouraging tone.
class ParentDashboardScreen extends StatefulWidget {
  final String userId;
  final String? childName;
  final bool embedded;
  final int? weeklyGoal;
  final String? curriculum;
  final Clan? childClan;
  final ChallengeInfo? activeChallengeInfo;
  final ChallengeProgress? challengeProgressInfo;

  const ParentDashboardScreen({
    super.key,
    required this.userId,
    this.childName,
    this.embedded = false,
    this.weeklyGoal,
    this.curriculum,
    this.childClan,
    this.activeChallengeInfo,
    this.challengeProgressInfo,
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

  @override
  void didUpdateWidget(covariant ParentDashboardScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.userId != oldWidget.userId) _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await _api.getParentDashboard(
        userId: widget.userId,
        curriculum: widget.curriculum,
      );
      if (!mounted) return;
      setState(() { _data = data; _loading = false; });
    } catch (e) {
      if (!mounted) return;
      String friendlyMsg;
      final raw = e.toString();
      if (raw.contains('SocketException') || raw.contains('Connection')) {
        friendlyMsg = "Can't reach the server right now. Check your internet and try again.";
      } else {
        friendlyMsg = "Something went wrong loading the dashboard. Give it another try.";
      }
      setState(() { _error = friendlyMsg; _loading = false; });
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: _loading
            ? Center(child: CircularProgressIndicator(color: KiwiColors.kiwiPrimary))
            : _error != null
                ? _buildError()
                : _buildBody(),
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
            Icon(Icons.cloud_off_rounded, size: 48, color: Colors.grey.shade300),
            const SizedBox(height: 12),
            const Text(
              'Could not load the dashboard',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 13, color: KiwiColors.textMid, height: 1.4),
            ),
            const SizedBox(height: 18),
            GestureDetector(
              onTap: _load,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiPrimary,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Try again',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Colors.white),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    final data = _data!;
    final childName = widget.childName ?? 'your child';

    final overallAccuracy = (data['overall_accuracy'] as num?)?.toDouble() ?? 0.0;
    final totalQuestions = (data['total_questions'] as num?)?.toInt() ?? 0;
    final currentStreak = (data['current_streak'] as num?)?.toInt() ?? 0;
    final topics = (data['topics'] as List<dynamic>? ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    final strengths = (data['strengths'] as List<dynamic>? ?? [])
        .map((e) => e.toString()).toList();
    final weaknesses = (data['needs_practice'] as List<dynamic>? ?? [])
        .map((e) => e.toString()).toList();
    final recommendations = (data['recommendations'] as List<dynamic>? ?? [])
        .map((e) => e.toString()).toList();

    final weeklyGoal = widget.weeklyGoal ?? 35;
    final weeklyDone = (data['weekly_questions'] as num?)?.toInt() ??
        (totalQuestions > weeklyGoal ? weeklyGoal : totalQuestions);

    // Proficiency, competency, and growth data (from Vedantu LO system)
    final proficiency = data['proficiency'] as Map<String, dynamic>?;
    final competency = data['competency_breakdown'] as Map<String, dynamic>?;
    final growth = data['growth'] as Map<String, dynamic>?;

    return RefreshIndicator(
      color: KiwiColors.kiwiPrimary,
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 28),
        children: [
          // Kiwi mascot + greeting
          _buildGreeting(childName),
          const SizedBox(height: 18),

          // Progress narrative card (the "story" of how they're doing)
          _buildProgressStory(overallAccuracy, totalQuestions, currentStreak),
          const SizedBox(height: 14),

          // Proficiency level card (scale score, competency breakdown, growth)
          if (proficiency != null && totalQuestions >= 5)
            Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: ProficiencyCard(
                proficiency: proficiency,
                competency: competency,
                growth: growth,
              ),
            ),

          // Diagnostic test button
          _buildDiagnosticButton(),
          const SizedBox(height: 14),

          // Weekly practice check
          _buildWeeklyCheck(weeklyDone, weeklyGoal),
          const SizedBox(height: 14),

          // Clan activity
          _buildClanSection(),
          const SizedBox(height: 18),

          // What they're great at + where to grow
          if (strengths.isNotEmpty || weaknesses.isNotEmpty) ...[
            _buildStrengthsAndGrowth(strengths, weaknesses),
            const SizedBox(height: 18),
          ],

          // Topic progress
          if (topics.isNotEmpty) ...[
            _sectionLabel('Topic progress'),
            const SizedBox(height: 8),
            ...topics.map((t) => _buildTopicRow(t)),
          ],

          // Tips
          if (recommendations.isNotEmpty) ...[
            const SizedBox(height: 18),
            _sectionLabel('Tips for you'),
            const SizedBox(height: 8),
            ...recommendations.map((r) => _buildTip(r)),
          ],
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Widgets
  // ---------------------------------------------------------------------------

  Widget _buildGreeting(String childName) {
    return Row(
      children: [
        // Kiwi avatar
        Container(
          width: 44,
          height: 44,
          decoration: const BoxDecoration(
            color: KiwiColors.kiwiPrimaryLight,
            shape: BoxShape.circle,
          ),
          child: const Center(
            child: Text('\u{1F95D}', style: TextStyle(fontSize: 22)),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "How $childName is doing",
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.textDark,
                ),
              ),
              const Text(
                'Your child\'s learning journey',
                style: TextStyle(fontSize: 12, color: KiwiColors.textMuted),
              ),
            ],
          ),
        ),
        if (_loading)
          SizedBox(
            width: 18, height: 18,
            child: CircularProgressIndicator(strokeWidth: 2, color: KiwiColors.kiwiPrimary),
          )
        else
          GestureDetector(
            onTap: _load,
            child: const Icon(Icons.refresh_rounded, size: 22, color: KiwiColors.textMuted),
          ),
      ],
    );
  }

  Widget _buildProgressStory(double accuracy, int totalQ, int streak) {
    // Choose an encouraging narrative based on performance
    String narrative;
    String emoji;
    if (accuracy >= 80) {
      narrative = 'doing great! Strong understanding across topics.';
      emoji = '\u{1F31F}';
    } else if (accuracy >= 60) {
      narrative = 'making solid progress. Building a good foundation.';
      emoji = '\u{1F4AA}';
    } else if (totalQ > 10) {
      narrative = 'building up. More practice will strengthen understanding.';
      emoji = '\u{1F331}';
    } else {
      narrative = 'just getting started. Every question counts!';
      emoji = '\u{1F680}';
    }

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: KiwiColors.kiwiPrimary.withOpacity(0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Narrative line
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 12),
              Expanded(
                child: RichText(
                  text: TextSpan(
                    style: const TextStyle(
                      fontSize: 15,
                      color: KiwiColors.textDark,
                      height: 1.4,
                    ),
                    children: [
                      const TextSpan(
                        text: 'Your child is ',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                      TextSpan(
                        text: narrative,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Key numbers — simple, not overwhelming
          Row(
            children: [
              _miniStat('${accuracy.round()}%', 'Accuracy',
                  accuracy >= 70 ? KiwiColors.kiwiPrimary : KiwiColors.sunset),
              const SizedBox(width: 16),
              _miniStat('$totalQ', 'Questions', KiwiColors.sky),
              const SizedBox(width: 16),
              _miniStat('$streak days', 'This week', KiwiColors.streakWarm),
            ],
          ),
        ],
      ),
    );
  }

  Widget _miniStat(String value, String label, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w500,
                color: color.withOpacity(0.8),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeeklyCheck(int done, int goal) {
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
                color: isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset,
              ),
              const SizedBox(width: 8),
              const Text(
                'Weekly practice',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: KiwiColors.textDark),
              ),
              const Spacer(),
              Text(
                '$done / $goal questions',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset,
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
              backgroundColor: (isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset).withOpacity(0.12),
              valueColor: AlwaysStoppedAnimation<Color>(
                  isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset),
            ),
          ),
          if (isComplete) ...[
            const SizedBox(height: 6),
            Text(
              'Great job this week! Consistent practice builds confidence.',
              style: TextStyle(fontSize: 11.5, color: KiwiColors.kiwiPrimary, fontWeight: FontWeight.w500),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDiagnosticButton() {
    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => BenchmarkTestScreen(
              userId: widget.userId,
              grade: 1,
              childName: widget.childName,
              benchmarkType: 'diagnostic',
              onComplete: _load,
            ),
          ),
        );
      },
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: KiwiColors.sky.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: KiwiColors.sky.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Center(
                child: Icon(Icons.assignment_outlined, size: 18, color: KiwiColors.sky),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'Run a diagnostic test',
                    style: TextStyle(
                      fontSize: 13, fontWeight: FontWeight.w700, color: KiwiColors.textDark,
                    ),
                  ),
                  SizedBox(height: 2),
                  Text(
                    '20 questions to measure exact proficiency level',
                    style: TextStyle(fontSize: 11.5, color: KiwiColors.textMuted),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded, size: 20, color: KiwiColors.textMuted),
          ],
        ),
      ),
    );
  }

  Widget _buildClanSection() {
    final clan = widget.childClan;

    // Child is not in a clan — show informational card
    if (clan == null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.groups_rounded, size: 20, color: KiwiColors.textMuted),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'Clan Activity',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: KiwiColors.textDark),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Your child hasn\'t joined a study clan yet. '
                    'Clans are moderated groups where kids solve math puzzles together.',
                    style: TextStyle(fontSize: 12.5, color: KiwiColors.textMid, height: 1.4),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    // Child is in a clan — show full clan summary
    final challenge = widget.activeChallengeInfo;
    final progress = widget.challengeProgressInfo;

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
          // Header row: crest emoji + clan name + level
          Row(
            children: [
              const Icon(Icons.groups_rounded, size: 18, color: KiwiColors.kiwiPrimary),
              const SizedBox(width: 8),
              const Text(
                'Clan Activity',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: KiwiColors.textDark),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Clan info row
          Row(
            children: [
              // Crest emoji badge
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiPrimaryLight,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Center(
                  child: Text(clan.crest.emoji, style: const TextStyle(fontSize: 20)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      clan.name,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${clan.clanLevel.emoji} Level ${clan.clanLevel.level} ${clan.clanLevel.name}'
                      '  ·  ${clan.memberCount} members',
                      style: const TextStyle(
                        fontSize: 11.5,
                        fontWeight: FontWeight.w500,
                        color: KiwiColors.textMid,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),

          // Challenge status (if active)
          if (challenge != null && challenge.status == 'active') ...[
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Divider(height: 1, color: Colors.grey.shade200),
            ),
            Row(
              children: [
                Icon(Icons.extension_rounded, size: 16, color: KiwiColors.sky),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    challenge.title,
                    style: const TextStyle(
                      fontSize: 12.5,
                      fontWeight: FontWeight.w600,
                      color: KiwiColors.textDark,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                _miniStat(
                  '${(progress?.revealPercentage ?? 0).round()}%',
                  'Revealed',
                  KiwiColors.sky,
                ),
                const SizedBox(width: 10),
                _miniStat(
                  '${challenge.daysRemaining}d',
                  'Left',
                  challenge.daysRemaining <= 2 ? KiwiColors.sunset : KiwiColors.kiwiGreen,
                ),
              ],
            ),
          ],

          // Reassuring message for parents
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Icon(Icons.verified_user_rounded, size: 14, color: KiwiColors.kiwiPrimaryDark),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Your child is part of a moderated study group. '
                    'No chat — just collaborative puzzle-solving!',
                    style: TextStyle(
                      fontSize: 11.5,
                      color: KiwiColors.kiwiPrimaryDark,
                      height: 1.35,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStrengthsAndGrowth(List<String> strengths, List<String> weaknesses) {
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
                const Icon(Icons.star_rounded, size: 16, color: KiwiColors.kiwiGreen),
                const SizedBox(width: 6),
                Text(
                  'Doing well in',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: KiwiColors.textMid),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: strengths.map((id) => _pill(_prettyTopic(id), KiwiColors.kiwiGreen)).toList(),
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
                Icon(Icons.trending_up_rounded, size: 16, color: KiwiColors.sunset),
                const SizedBox(width: 6),
                Text(
                  'Room to grow',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: KiwiColors.textMid),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: weaknesses.map((id) => _pill(_prettyTopic(id), KiwiColors.sunset)).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _pill(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }

  Widget _sectionLabel(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w800,
        color: KiwiColors.textMid,
      ),
    );
  }

  Widget _buildTopicRow(Map<String, dynamic> t) {
    final name = t['topic_name']?.toString() ?? '';
    final accuracy = (t['accuracy'] as num?)?.toDouble() ?? 0.0;
    final mastery = t['mastery']?.toString() ?? 'learning';

    final color = mastery == 'mastered'
        ? KiwiColors.kiwiGreen
        : mastery == 'practising'
            ? KiwiColors.kiwiPrimary
            : KiwiColors.sunset;

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
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: KiwiColors.textDark),
                  ),
                ),
                Text(
                  '${accuracy.round()}%',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color),
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

  Widget _buildTip(String text) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: KiwiColors.kiwiPrimaryLight,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: KiwiColors.kiwiPrimary.withOpacity(0.15)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.lightbulb_outline_rounded, size: 16, color: KiwiColors.kiwiPrimaryDark),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 13, color: KiwiColors.textDark, height: 1.35),
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
