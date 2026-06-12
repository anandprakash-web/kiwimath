import 'dart:math';

import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';

/// Admin analytics dashboard with 4 tabs: Content, Engagement, Learning, Revenue.
class AnalyticsDashboardScreen extends StatefulWidget {
  final String email;
  const AnalyticsDashboardScreen({super.key, required this.email});

  @override
  State<AnalyticsDashboardScreen> createState() =>
      _AnalyticsDashboardScreenState();
}

class _AnalyticsDashboardScreenState extends State<AnalyticsDashboardScreen>
    with SingleTickerProviderStateMixin {
  final _api = ApiClient();
  late final KiwiTier _tier;
  late final TabController _tabController;

  // Data holders
  Map<String, dynamic>? _contentData;
  Map<String, dynamic>? _engagementData;
  Map<String, dynamic>? _learningData;
  Map<String, dynamic>? _revenueData;

  // Loading / error per tab
  final _loading = <int, bool>{0: true, 1: true, 2: true, 3: true};
  final _errors = <int, String?>{0: null, 1: null, 2: null, 3: null};

  @override
  void initState() {
    super.initState();
    _tier = KiwiTier.forGrade(3);
    _tabController = TabController(length: 4, vsync: this);
    _loadAll();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadAll() {
    return Future.wait([
      _loadContent(),
      _loadEngagement(),
      _loadLearning(),
      _loadRevenue(),
    ]);
  }

  Future<void> _loadContent() async {
    setState(() {
      _loading[0] = true;
      _errors[0] = null;
    });
    try {
      final data = await _api.getAnalyticsContent(widget.email);
      if (mounted) setState(() => _contentData = data);
    } catch (e) {
      if (mounted) setState(() => _errors[0] = '$e');
    } finally {
      if (mounted) setState(() => _loading[0] = false);
    }
  }

  Future<void> _loadEngagement() async {
    setState(() {
      _loading[1] = true;
      _errors[1] = null;
    });
    try {
      final data = await _api.getAnalyticsEngagement(widget.email);
      if (mounted) setState(() => _engagementData = data);
    } catch (e) {
      if (mounted) setState(() => _errors[1] = '$e');
    } finally {
      if (mounted) setState(() => _loading[1] = false);
    }
  }

  Future<void> _loadLearning() async {
    setState(() {
      _loading[2] = true;
      _errors[2] = null;
    });
    try {
      final data = await _api.getAnalyticsLearning(widget.email);
      if (mounted) setState(() => _learningData = data);
    } catch (e) {
      if (mounted) setState(() => _errors[2] = '$e');
    } finally {
      if (mounted) setState(() => _loading[2] = false);
    }
  }

  Future<void> _loadRevenue() async {
    setState(() {
      _loading[3] = true;
      _errors[3] = null;
    });
    try {
      final data = await _api.getAnalyticsRevenue(widget.email);
      if (mounted) setState(() => _revenueData = data);
    } catch (e) {
      if (mounted) setState(() => _errors[3] = '$e');
    } finally {
      if (mounted) setState(() => _loading[3] = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = _tier.colors;
    return Scaffold(
      backgroundColor: c.background,
      appBar: AppBar(
        backgroundColor: c.primary,
        foregroundColor: Colors.white,
        title: const Text(
          'Analytics Dashboard',
          style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
        ),
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          labelStyle:
              const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
          unselectedLabelStyle:
              const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
          tabs: const [
            Tab(text: 'Content'),
            Tab(text: 'Engagement'),
            Tab(text: 'Learning'),
            Tab(text: 'Revenue'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildTabBody(0, _contentData, _buildContentTab),
          _buildTabBody(1, _engagementData, _buildEngagementTab),
          _buildTabBody(2, _learningData, _buildLearningTab),
          _buildTabBody(3, _revenueData, _buildRevenueTab),
        ],
      ),
    );
  }

  Widget _buildTabBody(
    int index,
    Map<String, dynamic>? data,
    Widget Function(Map<String, dynamic>) builder,
  ) {
    final refreshers = [
      _loadContent,
      _loadEngagement,
      _loadLearning,
      _loadRevenue,
    ];
    if (_loading[index] == true) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_errors[index] != null) {
      return _buildErrorState(_errors[index]!, refreshers[index]);
    }
    if (data == null) {
      return _buildEmptyState();
    }
    return RefreshIndicator(
      onRefresh: refreshers[index],
      color: _tier.colors.primary,
      child: builder(data),
    );
  }

  Widget _buildErrorState(String error, Future<void> Function() onRetry) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 48, color: _tier.colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Failed to load data',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: _tier.colors.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              error,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: _tier.colors.textMuted),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh, size: 18),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Text(
        'No data available',
        style: TextStyle(fontSize: 14, color: _tier.colors.textMuted),
      ),
    );
  }

  // ===========================================================================
  // Content Tab
  // ===========================================================================

  Widget _buildContentTab(Map<String, dynamic> data) {
    final totalQuestions = _num(data['total_questions']);
    final curricula = _num(data['total_curricula']);
    final reviewed = _num(data['reviewed']);
    final flagged = _num(data['flagged']);
    final byGrade =
        (data['questions_by_grade'] as Map<String, dynamic>?) ?? {};
    final curriculumBreakdown =
        (data['curriculum_breakdown'] as List<dynamic>?) ?? [];
    final difficulty =
        (data['difficulty_distribution'] as Map<String, dynamic>?) ?? {};
    final hardest = (data['hardest_questions'] as List<dynamic>?) ?? [];
    final easiest = (data['easiest_questions'] as List<dynamic>?) ?? [];

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // KPI row
          _buildKpiRow([
            _KpiItem('Total Questions', _fmtNum(totalQuestions), KiwiColors.kiwiPrimary),
            _KpiItem('Curricula', _fmtNum(curricula), KiwiColors.sky),
            _KpiItem('Reviewed', _fmtNum(reviewed), KiwiColors.kiwiGreen),
            _KpiItem('Flagged', _fmtNum(flagged), KiwiColors.coral),
          ]),
          const SizedBox(height: 20),

          // Questions by grade bar chart
          _sectionTitle('Questions by Grade'),
          const SizedBox(height: 8),
          _buildHorizontalBarChart(
            _gradeEntries(byGrade),
            KiwiColors.kiwiPrimary,
          ),
          const SizedBox(height: 20),

          // Curriculum breakdown
          if (curriculumBreakdown.isNotEmpty) ...[
            _sectionTitle('Curriculum Breakdown'),
            const SizedBox(height: 8),
            ...curriculumBreakdown.map((item) {
              final m = item as Map<String, dynamic>;
              return _buildCurriculumCard(m);
            }),
            const SizedBox(height: 20),
          ],

          // Difficulty distribution
          if (difficulty.isNotEmpty) ...[
            _sectionTitle('Difficulty Distribution'),
            const SizedBox(height: 8),
            _buildDifficultyBars(difficulty),
            const SizedBox(height: 20),
          ],

          // Hardest questions
          if (hardest.isNotEmpty) ...[
            _sectionTitle('Hardest Questions (Top 10)'),
            const SizedBox(height: 8),
            _buildQuestionTable(hardest, isHard: true),
            const SizedBox(height: 20),
          ],

          // Easiest questions
          if (easiest.isNotEmpty) ...[
            _sectionTitle('Easiest Questions (Top 10)'),
            const SizedBox(height: 8),
            _buildQuestionTable(easiest, isHard: false),
          ],

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  List<_BarEntry> _gradeEntries(Map<String, dynamic> byGrade) {
    final entries = <_BarEntry>[];
    for (int g = 1; g <= 6; g++) {
      final key = '$g';
      entries.add(_BarEntry('Grade $g', _num(byGrade[key]).toDouble()));
    }
    return entries;
  }

  Widget _buildCurriculumCard(Map<String, dynamic> m) {
    final name = m['name'] as String? ?? 'Unknown';
    final count = _num(m['question_count']);
    final grades = (m['grades'] as List<dynamic>?)?.join(', ') ?? '';
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: _tier.colors.textPrimary,
                  ),
                ),
                if (grades.isNotEmpty)
                  Text(
                    'Grades: $grades',
                    style: TextStyle(
                      fontSize: 12,
                      color: _tier.colors.textMuted,
                    ),
                  ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              _fmtNum(count),
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w700,
                color: KiwiColors.kiwiPrimaryDark,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDifficultyBars(Map<String, dynamic> difficulty) {
    final easy = _num(difficulty['easy']).toDouble();
    final medium = _num(difficulty['medium']).toDouble();
    final hard = _num(difficulty['hard']).toDouble();
    final total = easy + medium + hard;
    if (total == 0) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: [
          // Proportional bar
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: SizedBox(
              height: 24,
              child: Row(
                children: [
                  _proportionalSegment(easy / total, KiwiColors.kiwiGreen),
                  _proportionalSegment(medium / total, KiwiColors.amber),
                  _proportionalSegment(hard / total, KiwiColors.coral),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _difficultyLegend('Easy', easy.toInt(), KiwiColors.kiwiGreen),
              _difficultyLegend('Medium', medium.toInt(), KiwiColors.amber),
              _difficultyLegend('Hard', hard.toInt(), KiwiColors.coral),
            ],
          ),
        ],
      ),
    );
  }

  Widget _proportionalSegment(double fraction, Color color) {
    return Expanded(
      flex: (fraction * 1000).round().clamp(1, 1000),
      child: Container(color: color),
    );
  }

  Widget _difficultyLegend(String label, int count, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(
          '$label ($count)',
          style: TextStyle(fontSize: 12, color: _tier.colors.textSecondary),
        ),
      ],
    );
  }

  Widget _buildQuestionTable(List<dynamic> questions, {required bool isHard}) {
    return Container(
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: isHard
                  ? KiwiColors.coral.withOpacity(0.08)
                  : KiwiColors.kiwiGreen.withOpacity(0.08),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(14)),
            ),
            child: Row(
              children: [
                Expanded(
                  flex: 4,
                  child: Text('Question',
                      style: _tableHeaderStyle()),
                ),
                Expanded(
                  flex: 2,
                  child: Text('Topic',
                      style: _tableHeaderStyle()),
                ),
                Expanded(
                  flex: 1,
                  child: Text(isHard ? 'Err%' : 'Acc%',
                      textAlign: TextAlign.right,
                      style: _tableHeaderStyle()),
                ),
              ],
            ),
          ),
          ...questions.asMap().entries.map((entry) {
            final i = entry.key;
            final q = entry.value as Map<String, dynamic>;
            final stem = q['stem'] as String? ?? q['id'] as String? ?? '-';
            final topic = q['topic'] as String? ?? '';
            final pct = (q['error_rate'] ?? q['accuracy'] ?? 0).toString();
            return Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              color: i.isEven ? Colors.transparent : KiwiColors.pathLocked.withOpacity(0.15),
              child: Row(
                children: [
                  Expanded(
                    flex: 4,
                    child: Text(
                      stem.length > 50 ? '${stem.substring(0, 50)}...' : stem,
                      style: TextStyle(
                          fontSize: 12, color: _tier.colors.textPrimary),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Expanded(
                    flex: 2,
                    child: Text(
                      topic,
                      style: TextStyle(
                          fontSize: 11, color: _tier.colors.textMuted),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Expanded(
                    flex: 1,
                    child: Text(
                      pct,
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: isHard ? KiwiColors.coral : KiwiColors.kiwiGreen,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }

  // ===========================================================================
  // Engagement Tab
  // ===========================================================================

  Widget _buildEngagementTab(Map<String, dynamic> data) {
    final totalUsers = _num(data['total_users']);
    final activeUsers = _num(data['active_users']);
    final avgAccuracy = _dbl(data['avg_accuracy']);
    final avgStreak = _dbl(data['avg_streak']);
    final dailyActivity =
        (data['daily_activity'] as List<dynamic>?) ?? [];
    final streakDist =
        (data['streak_distribution'] as Map<String, dynamic>?) ?? {};
    final gradeDist =
        (data['grade_distribution'] as Map<String, dynamic>?) ?? {};
    final topUsers = (data['top_users'] as List<dynamic>?) ?? [];

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildKpiRow([
            _KpiItem('Total Users', _fmtNum(totalUsers), KiwiColors.kiwiPrimary),
            _KpiItem('Active Users', _fmtNum(activeUsers), KiwiColors.sky),
            _KpiItem('Avg Accuracy', '${avgAccuracy.toStringAsFixed(1)}%', KiwiColors.kiwiGreen),
            _KpiItem('Avg Streak', avgStreak.toStringAsFixed(1), KiwiColors.streakWarm),
          ]),
          const SizedBox(height: 20),

          // Daily activity chart
          if (dailyActivity.isNotEmpty) ...[
            _sectionTitle('Daily Activity (Last 30 Days)'),
            const SizedBox(height: 8),
            _buildDailyActivityChart(dailyActivity),
            const SizedBox(height: 20),
          ],

          // Streak distribution
          if (streakDist.isNotEmpty) ...[
            _sectionTitle('Streak Distribution'),
            const SizedBox(height: 8),
            _buildHorizontalBarChart(
              streakDist.entries
                  .map((e) => _BarEntry(e.key, _num(e.value).toDouble()))
                  .toList(),
              KiwiColors.streakWarm,
            ),
            const SizedBox(height: 20),
          ],

          // Grade distribution
          if (gradeDist.isNotEmpty) ...[
            _sectionTitle('Grade Distribution'),
            const SizedBox(height: 8),
            _buildGradeDistribution(gradeDist),
            const SizedBox(height: 20),
          ],

          // Top users leaderboard
          if (topUsers.isNotEmpty) ...[
            _sectionTitle('Top Users'),
            const SizedBox(height: 8),
            _buildLeaderboard(topUsers),
          ],

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildDailyActivityChart(List<dynamic> dailyActivity) {
    final values = dailyActivity.map((d) {
      final m = d as Map<String, dynamic>;
      return _num(m['count'] ?? m['sessions'] ?? m['active_users']).toDouble();
    }).toList();
    final maxVal = values.fold<double>(0, (a, b) => max(a, b));
    if (maxVal == 0) return const SizedBox.shrink();

    return Container(
      height: 160,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: values.asMap().entries.map((entry) {
          final fraction = entry.value / maxVal;
          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 1),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Flexible(
                    child: FractionallySizedBox(
                      heightFactor: fraction.clamp(0.02, 1.0),
                      child: Container(
                        decoration: BoxDecoration(
                          color: KiwiColors.sky.withOpacity(0.8),
                          borderRadius:
                              const BorderRadius.vertical(top: Radius.circular(2)),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildGradeDistribution(Map<String, dynamic> gradeDist) {
    final total = gradeDist.values.fold<num>(0, (a, b) => a + _num(b));
    if (total == 0) return const SizedBox.shrink();

    final colors = [
      KiwiColors.kiwiPrimary,
      KiwiColors.sky,
      KiwiColors.coral,
      KiwiColors.indigo,
      KiwiColors.teal,
      KiwiColors.amber,
    ];

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: [
          // Segmented bar
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: SizedBox(
              height: 28,
              child: Row(
                children: gradeDist.entries.toList().asMap().entries.map((e) {
                  final fraction = _num(e.value.value) / total;
                  return Expanded(
                    flex: (fraction * 1000).round().clamp(1, 1000),
                    child: Container(
                      color: colors[e.key % colors.length],
                      alignment: Alignment.center,
                      child: fraction > 0.08
                          ? Text(
                              e.value.key,
                              style: const TextStyle(
                                  fontSize: 10,
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600),
                            )
                          : null,
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 14,
            runSpacing: 6,
            children: gradeDist.entries.toList().asMap().entries.map((e) {
              final color = colors[e.key % colors.length];
              final count = _num(e.value.value);
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                        color: color, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '${e.value.key}: $count',
                    style: TextStyle(
                        fontSize: 12, color: _tier.colors.textSecondary),
                  ),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildLeaderboard(List<dynamic> topUsers) {
    return Container(
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: topUsers.asMap().entries.map((entry) {
          final i = entry.key;
          final u = entry.value as Map<String, dynamic>;
          final name = u['name'] as String? ?? u['user_id'] as String? ?? '-';
          final score = u['score'] ?? u['xp'] ?? u['accuracy'] ?? 0;
          final medal = i == 0
              ? '\u{1F947}'
              : i == 1
                  ? '\u{1F948}'
                  : i == 2
                      ? '\u{1F949}'
                      : '${i + 1}';
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: i.isEven
                  ? Colors.transparent
                  : KiwiColors.pathLocked.withOpacity(0.15),
              borderRadius: i == 0
                  ? const BorderRadius.vertical(top: Radius.circular(14))
                  : i == topUsers.length - 1
                      ? const BorderRadius.vertical(
                          bottom: Radius.circular(14))
                      : null,
            ),
            child: Row(
              children: [
                SizedBox(
                  width: 30,
                  child: Text(
                    medal,
                    style: TextStyle(
                      fontSize: i < 3 ? 18 : 14,
                      fontWeight: FontWeight.w700,
                      color: _tier.colors.textPrimary,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    name,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: _tier.colors.textPrimary,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  '$score',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.kiwiPrimary,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // ===========================================================================
  // Learning Tab
  // ===========================================================================

  Widget _buildLearningTab(Map<String, dynamic> data) {
    final skillsTracked = _num(data['skills_tracked']);
    final avgMastery = _dbl(data['avg_mastery']);
    final fsrsReviewsDue = _num(data['fsrs_reviews_due']);
    final avgRecall = _dbl(data['avg_recall']);
    final skillGaps = (data['skill_gaps'] as List<dynamic>?) ?? [];
    final strongSkills = (data['strongest_skills'] as List<dynamic>?) ?? [];
    final fsrsStats = (data['fsrs_stats'] as Map<String, dynamic>?) ?? {};
    final mistakePatterns =
        (data['mistake_patterns'] as List<dynamic>?) ?? [];
    final funnel =
        (data['improvement_funnel'] as List<dynamic>?) ?? [];

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildKpiRow([
            _KpiItem('Skills Tracked', _fmtNum(skillsTracked), KiwiColors.indigo),
            _KpiItem('Avg Mastery', '${avgMastery.toStringAsFixed(1)}%', KiwiColors.kiwiGreen),
            _KpiItem('FSRS Due', _fmtNum(fsrsReviewsDue), KiwiColors.amber),
            _KpiItem('Avg Recall', '${avgRecall.toStringAsFixed(1)}%', KiwiColors.sky),
          ]),
          const SizedBox(height: 20),

          // Skill gaps
          if (skillGaps.isNotEmpty) ...[
            _sectionTitle('Skill Gaps (Weakest)'),
            const SizedBox(height: 8),
            _buildSkillBars(skillGaps, KiwiColors.coral),
            const SizedBox(height: 20),
          ],

          // Strongest skills
          if (strongSkills.isNotEmpty) ...[
            _sectionTitle('Strongest Skills'),
            const SizedBox(height: 8),
            _buildSkillBars(strongSkills, KiwiColors.kiwiGreen),
            const SizedBox(height: 20),
          ],

          // FSRS stats card
          if (fsrsStats.isNotEmpty) ...[
            _sectionTitle('FSRS Stats'),
            const SizedBox(height: 8),
            _buildFsrsCard(fsrsStats),
            const SizedBox(height: 20),
          ],

          // Mistake patterns
          if (mistakePatterns.isNotEmpty) ...[
            _sectionTitle('Common Mistake Patterns'),
            const SizedBox(height: 8),
            _buildMistakePatterns(mistakePatterns),
            const SizedBox(height: 20),
          ],

          // Improvement funnel
          if (funnel.isNotEmpty) ...[
            _sectionTitle('Improvement Funnel'),
            const SizedBox(height: 8),
            _buildFunnel(funnel),
          ],

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSkillBars(List<dynamic> skills, Color barColor) {
    final maxVal = skills.fold<double>(0, (a, b) {
      final m = b as Map<String, dynamic>;
      return max(a, _dbl(m['mastery'] ?? m['score'] ?? m['value']));
    });
    final effectiveMax = maxVal > 0 ? maxVal : 100.0;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: skills.map((s) {
          final m = s as Map<String, dynamic>;
          final name = m['name'] as String? ?? m['skill'] as String? ?? '-';
          final value = _dbl(m['mastery'] ?? m['score'] ?? m['value']);
          final fraction = (value / effectiveMax).clamp(0.0, 1.0);
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(
                      child: Text(
                        name,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: _tier.colors.textPrimary,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      '${value.toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: barColor,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: SizedBox(
                    height: 10,
                    child: LinearProgressIndicator(
                      value: fraction,
                      backgroundColor: barColor.withOpacity(0.12),
                      valueColor: AlwaysStoppedAnimation(barColor),
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFsrsCard(Map<String, dynamic> stats) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: stats.entries.map((e) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _formatKey(e.key),
                  style: TextStyle(
                    fontSize: 13,
                    color: _tier.colors.textSecondary,
                  ),
                ),
                Text(
                  '${e.value}',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: _tier.colors.textPrimary,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildMistakePatterns(List<dynamic> patterns) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: patterns.asMap().entries.map((entry) {
          final i = entry.key;
          final p = entry.value as Map<String, dynamic>;
          final patternName =
              p['pattern'] as String? ?? p['name'] as String? ?? '-';
          final count = _num(p['count'] ?? p['occurrences']);
          return Container(
            padding: const EdgeInsets.symmetric(vertical: 8),
            decoration: i < patterns.length - 1
                ? BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                          color: KiwiColors.pathLocked.withOpacity(0.4)),
                    ),
                  )
                : null,
            child: Row(
              children: [
                Container(
                  width: 28,
                  height: 28,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: KiwiColors.coral.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '${i + 1}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.coral,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    patternName,
                    style: TextStyle(
                      fontSize: 13,
                      color: _tier.colors.textPrimary,
                    ),
                  ),
                ),
                Text(
                  '$count',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.coral,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFunnel(List<dynamic> funnel) {
    if (funnel.isEmpty) return const SizedBox.shrink();
    final maxVal = funnel.fold<double>(0, (a, b) {
      final m = b as Map<String, dynamic>;
      return max(a, _num(m['count'] ?? m['value']).toDouble());
    });
    if (maxVal == 0) return const SizedBox.shrink();

    final funnelColors = [
      KiwiColors.sky,
      KiwiColors.teal,
      KiwiColors.kiwiGreen,
      KiwiColors.amber,
      KiwiColors.kiwiPrimary,
    ];

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: funnel.asMap().entries.map((entry) {
          final i = entry.key;
          final m = entry.value as Map<String, dynamic>;
          final label = m['stage'] as String? ?? m['label'] as String? ?? '-';
          final count = _num(m['count'] ?? m['value']).toDouble();
          final fraction = (count / maxVal).clamp(0.1, 1.0);
          final color = funnelColors[i % funnelColors.length];

          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(label,
                        style: TextStyle(
                            fontSize: 13, color: _tier.colors.textSecondary)),
                    Text('${count.toInt()}',
                        style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: color)),
                  ],
                ),
                const SizedBox(height: 4),
                FractionallySizedBox(
                  widthFactor: fraction,
                  child: Container(
                    height: 22,
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // ===========================================================================
  // Revenue Tab
  // ===========================================================================

  Widget _buildRevenueTab(Map<String, dynamic> data) {
    final totalSignups = _num(data['total_signups']);
    final premiumUsers = _num(data['premium_users']);
    final premiumRate = _dbl(data['premium_rate']);
    final coinEconomy =
        (data['coin_economy'] as Map<String, dynamic>?) ?? {};
    final gemEconomy =
        (data['gem_economy'] as Map<String, dynamic>?) ?? {};
    final topicUnlocks =
        (data['topic_unlock_breakdown'] as List<dynamic>?) ?? [];
    final paywallFunnel =
        (data['paywall_funnel'] as List<dynamic>?) ?? [];

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildKpiRow([
            _KpiItem('Total Signups', _fmtNum(totalSignups), KiwiColors.kiwiPrimary),
            _KpiItem('Premium Users', _fmtNum(premiumUsers), KiwiColors.indigo),
            _KpiItem('Premium Rate', '${premiumRate.toStringAsFixed(1)}%', KiwiColors.kiwiGreen),
          ]),
          const SizedBox(height: 20),

          // Coin economy
          if (coinEconomy.isNotEmpty) ...[
            _sectionTitle('Coin Economy'),
            const SizedBox(height: 8),
            _buildEconomyCard(coinEconomy, KiwiColors.gemGold),
            const SizedBox(height: 20),
          ],

          // Gem economy
          if (gemEconomy.isNotEmpty) ...[
            _sectionTitle('Gem Economy'),
            const SizedBox(height: 8),
            _buildEconomyCard(gemEconomy, KiwiColors.gemBlue),
            const SizedBox(height: 20),
          ],

          // Topic unlock breakdown
          if (topicUnlocks.isNotEmpty) ...[
            _sectionTitle('Topic Unlock Breakdown'),
            const SizedBox(height: 8),
            _buildHorizontalBarChart(
              topicUnlocks.map((t) {
                final m = t as Map<String, dynamic>;
                final label = m['topic'] as String? ?? m['name'] as String? ?? '-';
                final count = _num(m['unlocks'] ?? m['count']).toDouble();
                return _BarEntry(label, count);
              }).toList(),
              KiwiColors.indigo,
            ),
            const SizedBox(height: 20),
          ],

          // Paywall funnel
          if (paywallFunnel.isNotEmpty) ...[
            _sectionTitle('Paywall Funnel'),
            const SizedBox(height: 8),
            _buildFunnel(paywallFunnel),
          ],

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildEconomyCard(Map<String, dynamic> economy, Color accent) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: accent.withOpacity(0.3)),
      ),
      child: Column(
        children: economy.entries.map((e) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _formatKey(e.key),
                  style: TextStyle(
                    fontSize: 13,
                    color: _tier.colors.textSecondary,
                  ),
                ),
                Text(
                  '${e.value}',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: accent,
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // ===========================================================================
  // Shared widgets
  // ===========================================================================

  Widget _buildKpiRow(List<_KpiItem> items) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: items.map((item) {
        return SizedBox(
          width: (MediaQuery.of(context).size.width - 32 - 10 * (min(items.length, 2) - 1)) /
              min(items.length, 2),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
            decoration: BoxDecoration(
              color: _tier.colors.cardBg,
              borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
              border: Border.all(color: item.color.withOpacity(0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.value,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: item.color,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  item.label,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: _tier.colors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _sectionTitle(String title) {
    return Text(
      title,
      style: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w700,
        color: _tier.colors.textPrimary,
      ),
    );
  }

  Widget _buildHorizontalBarChart(List<_BarEntry> entries, Color barColor) {
    final maxVal =
        entries.fold<double>(0, (a, b) => max(a, b.value));
    if (maxVal == 0) {
      return Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: _tier.colors.cardBg,
          borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
          border: Border.all(color: _tier.colors.topicCardBorder),
        ),
        child: Center(
          child: Text('No data',
              style: TextStyle(
                  fontSize: 13, color: _tier.colors.textMuted)),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _tier.colors.cardBg,
        borderRadius: BorderRadius.circular(_tier.shape.cardRadius),
        border: Border.all(color: _tier.colors.topicCardBorder),
      ),
      child: Column(
        children: entries.map((e) {
          final fraction = (e.value / maxVal).clamp(0.0, 1.0);
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                SizedBox(
                  width: 70,
                  child: Text(
                    e.label,
                    style: TextStyle(
                      fontSize: 12,
                      color: _tier.colors.textSecondary,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Stack(
                    children: [
                      Container(
                        height: 18,
                        decoration: BoxDecoration(
                          color: barColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      FractionallySizedBox(
                        widthFactor: fraction,
                        child: Container(
                          height: 18,
                          decoration: BoxDecoration(
                            color: barColor,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 6),
                          child: fraction > 0.15
                              ? Text(
                                  e.value.toInt().toString(),
                                  style: const TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.white,
                                  ),
                                )
                              : null,
                        ),
                      ),
                    ],
                  ),
                ),
                if (fraction <= 0.15) ...[
                  const SizedBox(width: 6),
                  Text(
                    e.value.toInt().toString(),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: barColor,
                    ),
                  ),
                ],
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  TextStyle _tableHeaderStyle() {
    return TextStyle(
      fontSize: 12,
      fontWeight: FontWeight.w700,
      color: _tier.colors.textSecondary,
    );
  }

  // ===========================================================================
  // Helpers
  // ===========================================================================

  num _num(dynamic v) => v is num ? v : (num.tryParse('$v') ?? 0);
  double _dbl(dynamic v) => _num(v).toDouble();

  String _fmtNum(num n) {
    if (n >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}M';
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}K';
    return n.toString();
  }

  String _formatKey(String key) {
    return key
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty ? '' : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}

class _KpiItem {
  final String label;
  final String value;
  final Color color;
  const _KpiItem(this.label, this.value, this.color);
}

class _BarEntry {
  final String label;
  final double value;
  const _BarEntry(this.label, this.value);
}
