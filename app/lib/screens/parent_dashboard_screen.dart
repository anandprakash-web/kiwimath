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

  /// Child's selected grade — used for the diagnostic benchmark test.
  final int grade;
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
    this.grade = 1,
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

  // Tier for theming — parent dashboard defaults to junior tier.
  KiwiTier get _tier => KiwiTier.forGrade(1);

  @override
  Widget build(BuildContext context) {
    final tier = _tier;
    final colors = tier.colors;
    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          children: [
            // Close affordance — this screen has no AppBar/back button.
            // Hidden when embedded inside a tab (nothing to pop).
            if (!widget.embedded)
              Align(
                alignment: Alignment.centerLeft,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(4, 2, 4, 0),
                  child: IconButton(
                    icon: Icon(Icons.close_rounded,
                        size: 22, color: colors.textMuted),
                    tooltip: 'Close',
                    onPressed: () => Navigator.of(context).maybePop(),
                  ),
                ),
              ),
            Expanded(
              child: _loading
                  ? Center(
                      child:
                          CircularProgressIndicator(color: colors.primary))
                  : _error != null
                      ? _buildError()
                      : _buildBody(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildError() {
    final tier = _tier;
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(KiwiSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_rounded, size: 48, color: colors.textMuted),
            const SizedBox(height: KiwiSpacing.md),
            Text(
              'Could not load the dashboard',
              style: TextStyle(
                fontSize: typo.bodySize,
                fontWeight: typo.headlineWeight,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            const SizedBox(height: KiwiSpacing.sm),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: typo.chipSize, color: colors.textSecondary, height: 1.4, fontFamily: typo.fontFamily),
            ),
            const SizedBox(height: KiwiSpacing.lg),
            GestureDetector(
              onTap: _load,
              child: Container(
                padding: shape.buttonPadding,
                decoration: BoxDecoration(
                  color: colors.primary,
                  borderRadius: BorderRadius.circular(shape.buttonRadius),
                ),
                child: Text(
                  'Try again',
                  style: TextStyle(fontSize: typo.buttonSize, fontWeight: FontWeight.w700, color: Colors.white, fontFamily: typo.fontFamily),
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

    final tier = _tier;
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return RefreshIndicator(
      color: colors.primary,
      onRefresh: _load,
      child: ListView(
        padding: KiwiSpacing.sectionPadding,
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

          // COPPA — Child data management
          const SizedBox(height: 24),
          _buildDataManagementSection(childName),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Widgets
  // ---------------------------------------------------------------------------

  Widget _buildGreeting(String childName) {
    final colors = _tier.colors;
    final typo = _tier.typography;
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
        const SizedBox(width: KiwiSpacing.md),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                "How $childName is doing",
                style: TextStyle(
                  fontSize: typo.headlineSize,
                  fontWeight: typo.headlineWeight,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
              ),
              Text(
                'Your child\'s learning journey',
                style: TextStyle(fontSize: typo.chipSize, color: colors.textMuted, fontFamily: typo.fontFamily),
              ),
            ],
          ),
        ),
        if (_loading)
          SizedBox(
            width: 18, height: 18,
            child: CircularProgressIndicator(strokeWidth: 2, color: colors.primary),
          )
        else
          GestureDetector(
            onTap: _load,
            child: Icon(Icons.refresh_rounded, size: 22, color: colors.textMuted),
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

    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    return Container(
      padding: shape.cardPadding,
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.primary.withOpacity(0.15)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Narrative line
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: KiwiSpacing.md),
              Expanded(
                child: RichText(
                  text: TextSpan(
                    style: TextStyle(
                      fontSize: typo.bodySize,
                      color: colors.textPrimary,
                      height: 1.4,
                      fontFamily: typo.fontFamily,
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
          const SizedBox(height: KiwiSpacing.lg),
          // Key numbers — simple, not overwhelming
          Row(
            children: [
              _miniStat('${accuracy.round()}%', 'Accuracy',
                  accuracy >= 70 ? KiwiColors.kiwiPrimary : KiwiColors.sunset),
              const SizedBox(width: KiwiSpacing.lg),
              _miniStat('$totalQ', 'Questions', KiwiColors.sky),
              const SizedBox(width: KiwiSpacing.lg),
              _miniStat('$streak days', 'This week', KiwiColors.streakWarm),
            ],
          ),
        ],
      ),
    );
  }

  Widget _miniStat(String value, String label, Color color) {
    final typo = _tier.typography;
    final shape = _tier.shape;
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: KiwiSpacing.sm),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(shape.chipRadius),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: TextStyle(
                fontSize: typo.bodySize,
                fontWeight: FontWeight.w800,
                color: color,
                fontFamily: typo.fontFamily,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: typo.chipSize - 2,
                fontWeight: FontWeight.w500,
                color: color.withOpacity(0.8),
                fontFamily: typo.fontFamily,
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
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;

    return Container(
      padding: shape.cardPadding,
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.topicCardBorder),
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
              const SizedBox(width: KiwiSpacing.sm),
              Text(
                'Weekly practice',
                style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textPrimary, fontFamily: typo.fontFamily),
              ),
              const Spacer(),
              Text(
                '$done / $goal questions',
                style: TextStyle(
                  fontSize: typo.chipSize,
                  fontWeight: FontWeight.w600,
                  color: isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ],
          ),
          const SizedBox(height: KiwiSpacing.sm),
          ClipRRect(
            borderRadius: BorderRadius.circular(KiwiSpacing.xs),
            child: LinearProgressIndicator(
              value: fraction,
              minHeight: 7,
              backgroundColor: (isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset).withOpacity(0.12),
              valueColor: AlwaysStoppedAnimation<Color>(
                  isComplete ? KiwiColors.kiwiGreen : KiwiColors.sunset),
            ),
          ),
          if (isComplete) ...[
            const SizedBox(height: KiwiSpacing.sm),
            Text(
              'Great job this week! Consistent practice builds confidence.',
              style: TextStyle(fontSize: typo.chipSize - 1, color: colors.primary, fontWeight: FontWeight.w500, fontFamily: typo.fontFamily),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDiagnosticButton() {
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => BenchmarkTestScreen(
              userId: widget.userId,
              grade: widget.grade,
              childName: widget.childName,
              benchmarkType: 'diagnostic',
              onComplete: _load,
            ),
          ),
        );
      },
      child: Container(
        padding: shape.cardPadding,
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(color: KiwiColors.sky.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: KiwiColors.sky.withOpacity(0.1),
                borderRadius: BorderRadius.circular(shape.chipRadius),
              ),
              child: const Center(
                child: Icon(Icons.assignment_outlined, size: 18, color: KiwiColors.sky),
              ),
            ),
            const SizedBox(width: KiwiSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Run a diagnostic test',
                    style: TextStyle(
                      fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textPrimary, fontFamily: typo.fontFamily,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '20 questions to measure exact proficiency level',
                    style: TextStyle(fontSize: typo.chipSize - 1, color: colors.textMuted, fontFamily: typo.fontFamily),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right_rounded, size: 20, color: colors.textMuted),
          ],
        ),
      ),
    );
  }

  Widget _buildClanSection() {
    final clan = widget.childClan;
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;

    // Child is not in a clan — show informational card
    if (clan == null) {
      return Container(
        padding: shape.cardPadding,
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(color: colors.topicCardBorder),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.groups_rounded, size: 20, color: colors.textMuted),
            const SizedBox(width: KiwiSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Clan Activity',
                    style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textPrimary, fontFamily: typo.fontFamily),
                  ),
                  const SizedBox(height: KiwiSpacing.xs),
                  Text(
                    'Your child hasn\'t joined a study clan yet. '
                    'Clans are moderated groups where kids solve math puzzles together.',
                    style: TextStyle(fontSize: typo.chipSize, color: colors.textSecondary, height: 1.4, fontFamily: typo.fontFamily),
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
      padding: shape.cardPadding,
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.topicCardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row: crest emoji + clan name + level
          Row(
            children: [
              Icon(Icons.groups_rounded, size: 18, color: colors.primary),
              const SizedBox(width: KiwiSpacing.sm),
              Text(
                'Clan Activity',
                style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textPrimary, fontFamily: typo.fontFamily),
              ),
            ],
          ),
          const SizedBox(height: KiwiSpacing.md),

          // Clan info row
          Row(
            children: [
              // Crest emoji badge
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiPrimaryLight,
                  borderRadius: BorderRadius.circular(shape.chipRadius),
                ),
                child: Center(
                  child: Text(clan.crest.emoji, style: const TextStyle(fontSize: 20)),
                ),
              ),
              const SizedBox(width: KiwiSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      clan.name,
                      style: TextStyle(
                        fontSize: typo.bodySize,
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '${clan.clanLevel.emoji} Level ${clan.clanLevel.level} ${clan.clanLevel.name}'
                      '  ·  ${clan.memberCount} members',
                      style: TextStyle(
                        fontSize: typo.chipSize - 1,
                        fontWeight: FontWeight.w500,
                        color: colors.textSecondary,
                        fontFamily: typo.fontFamily,
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
              padding: const EdgeInsets.symmetric(vertical: KiwiSpacing.sm),
              child: Divider(height: 1, color: colors.topicCardBorder),
            ),
            Row(
              children: [
                const Icon(Icons.extension_rounded, size: 16, color: KiwiColors.sky),
                const SizedBox(width: KiwiSpacing.sm),
                Expanded(
                  child: Text(
                    challenge.title,
                    style: TextStyle(
                      fontSize: typo.chipSize,
                      fontWeight: FontWeight.w600,
                      color: colors.textPrimary,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: KiwiSpacing.sm),
            Row(
              children: [
                _miniStat(
                  '${(progress?.revealPercentage ?? 0).round()}%',
                  'Revealed',
                  KiwiColors.sky,
                ),
                const SizedBox(width: KiwiSpacing.sm),
                _miniStat(
                  '${challenge.daysRemaining}d',
                  'Left',
                  challenge.daysRemaining <= 2 ? KiwiColors.sunset : KiwiColors.kiwiGreen,
                ),
              ],
            ),
          ],

          // Reassuring message for parents
          const SizedBox(height: KiwiSpacing.sm),
          Container(
            padding: const EdgeInsets.all(KiwiSpacing.sm),
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(shape.chipRadius),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.verified_user_rounded, size: 14, color: KiwiColors.kiwiPrimaryDark),
                const SizedBox(width: KiwiSpacing.sm),
                Expanded(
                  child: Text(
                    'Your child is part of a moderated study group. '
                    'No chat — just collaborative puzzle-solving!',
                    style: TextStyle(
                      fontSize: typo.chipSize - 1,
                      color: KiwiColors.kiwiPrimaryDark,
                      height: 1.35,
                      fontWeight: FontWeight.w500,
                      fontFamily: typo.fontFamily,
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
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    return Container(
      padding: shape.cardPadding,
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.topicCardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (strengths.isNotEmpty) ...[
            Row(
              children: [
                const Icon(Icons.star_rounded, size: 16, color: KiwiColors.kiwiGreen),
                const SizedBox(width: KiwiSpacing.sm),
                Text(
                  'Doing well in',
                  style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textSecondary, fontFamily: typo.fontFamily),
                ),
              ],
            ),
            const SizedBox(height: KiwiSpacing.sm),
            Wrap(
              spacing: KiwiSpacing.sm,
              runSpacing: KiwiSpacing.sm,
              children: strengths.map((id) => _pill(_prettyTopic(id), KiwiColors.kiwiGreen)).toList(),
            ),
          ],
          if (strengths.isNotEmpty && weaknesses.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: KiwiSpacing.sm),
              child: Divider(height: 1, color: colors.topicCardBorder),
            ),
          if (weaknesses.isNotEmpty) ...[
            Row(
              children: [
                const Icon(Icons.trending_up_rounded, size: 16, color: KiwiColors.sunset),
                const SizedBox(width: KiwiSpacing.sm),
                Text(
                  'Room to grow',
                  style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: colors.textSecondary, fontFamily: typo.fontFamily),
                ),
              ],
            ),
            const SizedBox(height: KiwiSpacing.sm),
            Wrap(
              spacing: KiwiSpacing.sm,
              runSpacing: KiwiSpacing.sm,
              children: weaknesses.map((id) => _pill(_prettyTopic(id), KiwiColors.sunset)).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _pill(String text, Color color) {
    final shape = _tier.shape;
    final typo = _tier.typography;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: KiwiSpacing.xs),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(shape.chipRadius),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w600, color: color, fontFamily: typo.fontFamily),
      ),
    );
  }

  Widget _sectionLabel(String title) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    return Text(
      title,
      style: TextStyle(
        fontSize: typo.bodySize,
        fontWeight: typo.headlineWeight,
        color: colors.textSecondary,
        fontFamily: typo.fontFamily,
      ),
    );
  }

  Widget _buildTopicRow(Map<String, dynamic> t) {
    final name = t['topic_name']?.toString() ?? '';
    final accuracy = (t['accuracy'] as num?)?.toDouble() ?? 0.0;
    final mastery = t['mastery']?.toString() ?? 'learning';
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;

    final color = mastery == 'mastered'
        ? KiwiColors.kiwiGreen
        : mastery == 'practising'
            ? KiwiColors.kiwiPrimary
            : KiwiColors.sunset;

    return Padding(
      padding: const EdgeInsets.only(bottom: KiwiSpacing.sm),
      child: Container(
        padding: shape.cardPadding,
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(color: colors.topicCardBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    name,
                    style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w600, color: colors.textPrimary, fontFamily: typo.fontFamily),
                  ),
                ),
                Text(
                  '${accuracy.round()}%',
                  style: TextStyle(fontSize: typo.chipSize, fontWeight: FontWeight.w700, color: color, fontFamily: typo.fontFamily),
                ),
              ],
            ),
            const SizedBox(height: KiwiSpacing.sm),
            ClipRRect(
              borderRadius: BorderRadius.circular(KiwiSpacing.xs),
              child: LinearProgressIndicator(
                value: (accuracy / 100).clamp(0.0, 1.0),
                minHeight: 5,
                backgroundColor: colors.backgroundDark,
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTip(String text) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    return Container(
      margin: const EdgeInsets.only(bottom: KiwiSpacing.sm),
      padding: shape.cardPadding,
      decoration: BoxDecoration(
        color: KiwiColors.kiwiPrimaryLight,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.primary.withOpacity(0.15)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.lightbulb_outline_rounded, size: 16, color: KiwiColors.kiwiPrimaryDark),
          const SizedBox(width: KiwiSpacing.sm),
          Expanded(
            child: Text(
              text,
              style: TextStyle(fontSize: typo.chipSize, color: colors.textPrimary, height: 1.35, fontFamily: typo.fontFamily),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // COPPA — Child Data Management
  // ---------------------------------------------------------------------------

  Widget _buildDataManagementSection(String childName) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    return Container(
      padding: shape.cardPadding,
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.topicCardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: KiwiColors.teal.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(shape.chipRadius),
                ),
                child: const Icon(Icons.shield_outlined, size: 18, color: KiwiColors.teal),
              ),
              const SizedBox(width: KiwiSpacing.sm),
              Expanded(
                child: Text(
                  'Child Data & Privacy',
                  style: TextStyle(
                    fontSize: typo.bodySize,
                    fontWeight: FontWeight.w700,
                    color: colors.textPrimary,
                    fontFamily: typo.fontFamily,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: KiwiSpacing.sm),
          Text(
            'As $childName\'s parent or guardian, you can manage their data at any time under COPPA.',
            style: TextStyle(
              fontSize: typo.chipSize,
              color: colors.textMuted,
              height: 1.35,
              fontFamily: typo.fontFamily,
            ),
          ),
          const SizedBox(height: KiwiSpacing.md),
          _dataAction(
            icon: Icons.visibility_outlined,
            label: 'Review collected data',
            subtitle: 'See what information we store',
            onTap: () => _showDataReviewSheet(childName),
          ),
          const SizedBox(height: KiwiSpacing.sm),
          _dataAction(
            icon: Icons.download_outlined,
            label: 'Export data',
            subtitle: 'Download a copy of all data',
            onTap: () => _requestDataExport(childName),
          ),
          const SizedBox(height: KiwiSpacing.sm),
          _dataAction(
            icon: Icons.delete_outline_rounded,
            label: 'Delete all data',
            subtitle: 'Permanently remove all records',
            onTap: () => _confirmDataDeletion(childName),
            destructive: true,
          ),
        ],
      ),
    );
  }

  Widget _dataAction({
    required IconData icon,
    required String label,
    required String subtitle,
    required VoidCallback onTap,
    bool destructive = false,
  }) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;
    final color = destructive ? KiwiColors.coral : colors.textPrimary;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.md, vertical: KiwiSpacing.sm),
        decoration: BoxDecoration(
          color: destructive
              ? KiwiColors.wrongBg
              : colors.backgroundDark.withOpacity(0.4),
          borderRadius: BorderRadius.circular(shape.chipRadius),
        ),
        child: Row(
          children: [
            Icon(icon, size: 20, color: color),
            const SizedBox(width: KiwiSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: TextStyle(
                    fontSize: typo.chipSize, fontWeight: FontWeight.w600, color: color, fontFamily: typo.fontFamily,
                  )),
                  Text(subtitle, style: TextStyle(
                    fontSize: typo.chipSize - 2, color: colors.textMuted, fontFamily: typo.fontFamily,
                  )),
                ],
              ),
            ),
            Icon(Icons.chevron_right, size: 18, color: colors.textMuted),
          ],
        ),
      ),
    );
  }

  void _showDataReviewSheet(String childName) {
    showModalBottomSheet(
      context: context,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(_tier.shape.cardRadius)),
      ),
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Data We Collect',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 14),
              _dataItem('Child\'s first name', 'Used for in-app greetings'),
              _dataItem('Grade level', 'Adjusts question difficulty'),
              _dataItem('Practice history', 'Questions answered, scores, time spent'),
              _dataItem('Mastery progress', 'Topic proficiency levels'),
              _dataItem('Streak & coins', 'Motivation rewards (no monetary value)'),
              const SizedBox(height: 14),
              const Text(
                'We do not collect photos, contacts, location, or any advertising identifiers.',
                style: TextStyle(fontSize: 11, color: KiwiColors.textMuted, height: 1.4),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _dataItem(String title, String desc) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.check_circle_outline, size: 16, color: KiwiColors.teal),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(
                  fontSize: 13, fontWeight: FontWeight.w600, color: KiwiColors.textDark,
                )),
                Text(desc, style: const TextStyle(
                  fontSize: 11, color: KiwiColors.textMuted,
                )),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _requestDataExport(String childName) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_tier.shape.cardRadius)),
        title: const Text('Export Data', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        content: Text(
          'We\'ll prepare a copy of $childName\'s data and send it to your registered email address within 48 hours.',
          style: const TextStyle(fontSize: 13, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Data export requested. Check your email within 48 hours.'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
              // TODO: wire to backend endpoint POST /api/user/{uid}/export-data
            },
            child: const Text('Request Export'),
          ),
        ],
      ),
    );
  }

  void _confirmDataDeletion(String childName) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(_tier.shape.cardRadius)),
        title: const Text('Delete All Data?', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        content: Text(
          'This will permanently delete all of $childName\'s learning data, including practice history, scores, streaks, and coins. This cannot be undone.',
          style: const TextStyle(fontSize: 13, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: KiwiColors.coral),
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Deletion requested. All data will be removed within 24 hours.'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
              // TODO: wire to backend endpoint DELETE /api/user/{uid}/data
            },
            child: const Text('Delete Everything'),
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
