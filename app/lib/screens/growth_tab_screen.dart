import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/growth.dart';
import '../services/growth_service.dart';
import '../theme/kiwi_theme.dart';

/// Growth Tab — the 6th bottom tab showing the student's improvement journey.
///
/// Two states:
/// - **No diagnostic**: Hero CTA encouraging the child to take the diagnostic.
/// - **Diagnostic taken**: Mountain hero, engagement stats, sparkline, topic
///   heatmap, and milestone timeline.
class GrowthTabScreen extends StatefulWidget {
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;
  final String userId;
  final VoidCallback onStartDiagnostic;
  final void Function(String topicId, String topicName) onStartPractice;

  const GrowthTabScreen({
    super.key,
    required this.selectedGrade,
    required this.onGradeChanged,
    required this.userId,
    required this.onStartDiagnostic,
    required this.onStartPractice,
  });

  @override
  State<GrowthTabScreen> createState() => _GrowthTabScreenState();
}

class _GrowthTabScreenState extends State<GrowthTabScreen>
    with SingleTickerProviderStateMixin {
  final _growth = GrowthService.instance;

  bool _loading = true;
  String? _error;
  bool _hasDiagnostic = false;
  GrowthJourney? _journey;
  List<TopicGrowth> _topics = [];
  List<GrowthMilestone> _milestones = [];
  List<_SparklinePoint> _sparklinePoints = [];

  late AnimationController _pulseController;

  // ── Level names for the mountain ──────────────────────────────────────────
  static const _levelNames = [
    'Explorer',
    'Builder',
    'Achiever',
    'Strategist',
    'Champion',
    'Legend',
  ];

  // ── Level colors ──────────────────────────────────────────────────────────
  static const _levelColors = [
    Color(0xFF90CAF9), // L1 — light blue
    Color(0xFF81C784), // L2 — green
    Color(0xFFFFD54F), // L3 — amber
    Color(0xFFFF8A65), // L4 — orange
    Color(0xFFE57373), // L5 — red
    Color(0xFFCE93D8), // L6 — purple
  ];

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    _loadData();
  }

  @override
  void didUpdateWidget(covariant GrowthTabScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedGrade != widget.selectedGrade ||
        oldWidget.userId != widget.userId) {
      _loadData();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final hasDiag =
          await _growth.hasDiagnostic(userId: widget.userId);
      if (!mounted) return;

      if (!hasDiag) {
        setState(() {
          _hasDiagnostic = false;
          _loading = false;
        });
        return;
      }

      // Load all data in parallel.
      final results = await Future.wait([
        _growth.getJourney(
            userId: widget.userId, grade: widget.selectedGrade),
        _growth.getTopics(
            userId: widget.userId, grade: widget.selectedGrade),
        _growth.getMilestones(
            userId: widget.userId, grade: widget.selectedGrade),
        _growth.getTimeline(userId: widget.userId),
      ]);

      if (!mounted) return;

      final journey = results[0] as GrowthJourney?;
      final topics = results[1] as List<TopicGrowth>;
      final milestones = results[2] as List<GrowthMilestone>;
      final timeline = results[3] as Map<String, dynamic>;

      // Parse sparkline points from snapshots.
      final rawPoints = timeline['snapshots'] as List<dynamic>? ?? [];
      final sparkline = rawPoints.map((p) {
        final m = p as Map<String, dynamic>;
        // Convert theta to scale score for display (200-800 range).
        final theta = (m['theta'] as num?)?.toDouble() ?? 0;
        final scaleScore = 500 + (theta * 50);
        return _SparklinePoint(
          date: m['timestamp'] as String? ?? '',
          score: scaleScore,
        );
      }).toList();

      setState(() {
        _hasDiagnostic = true;
        _journey = journey;
        _topics = topics;
        _milestones = milestones;
        _sparklinePoints = sparkline;
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

  // ═══════════════════════════════════════════════════════════════════════════
  // BUILD
  // ═══════════════════════════════════════════════════════════════════════════

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.dark,
      child: Scaffold(
        backgroundColor: colors.background,
        body: _loading
            ? _buildLoading(colors)
            : _error != null
                ? _buildError(colors, typo)
                : _hasDiagnostic
                    ? _buildJourney(tier)
                    : _buildNoDiagnostic(tier),
      ),
    );
  }

  // ── Loading ───────────────────────────────────────────────────────────────

  Widget _buildLoading(KiwiTierColors colors) {
    return Center(
      child: CircularProgressIndicator(
        color: colors.primary,
        strokeWidth: 3,
      ),
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────

  Widget _buildError(KiwiTierColors colors, KiwiTierTypography typo) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_rounded, size: 48, color: colors.textMuted),
            const SizedBox(height: 16),
            Text(
              'Couldn’t load your growth data',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: typo.fontFamily,
                fontSize: typo.bodySize,
                color: colors.textSecondary,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _loadData,
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // NO DIAGNOSTIC STATE
  // ═══════════════════════════════════════════════════════════════════════════

  Widget _buildNoDiagnostic(KiwiTier tier) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return SafeArea(
      child: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Hero Card ─────────────────────────────────────────────────
            _NoDiagnosticHeroCard(
              tier: tier,
              levelNames: _levelNames,
              levelColors: _levelColors,
              onStart: widget.onStartDiagnostic,
            ),
            const SizedBox(height: 20),

            // ── Info pills ────────────────────────────────────────────────
            Row(
              children: [
                _InfoPill(icon: Icons.quiz_rounded, label: '20 questions', tier: tier),
                const SizedBox(width: 10),
                _InfoPill(icon: Icons.timer_rounded, label: '~15 min', tier: tier),
                const SizedBox(width: 10),
                _InfoPill(icon: Icons.auto_awesome_rounded, label: 'All topics', tier: tier),
              ],
            ),
            const SizedBox(height: 24),

            // ── "What You’ll Discover" ────────────────────────────────
            Text(
              'What You’ll Discover',
              style: TextStyle(
                fontFamily: t.fontFamily,
                fontSize: t.headlineSize,
                fontWeight: t.headlineWeight,
                color: c.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            _DiscoverCard(
              icon: Icons.landscape_rounded,
              title: 'Your starting level on the mountain',
              subtitle: 'Find out which camp you belong to',
              tier: tier,
            ),
            const SizedBox(height: 10),
            _DiscoverCard(
              icon: Icons.insights_rounded,
              title: 'Your strongest and weakest topics',
              subtitle: 'See where you shine and where to grow',
              tier: tier,
            ),
            const SizedBox(height: 10),
            _DiscoverCard(
              icon: Icons.route_rounded,
              title: 'A personalized improvement plan',
              subtitle: 'A path made just for you',
              tier: tier,
            ),
          ],
        ),
      ),
    );
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // JOURNEY STATE (diagnostic taken)
  // ═══════════════════════════════════════════════════════════════════════════

  Widget _buildJourney(KiwiTier tier) {
    final journey = _journey;
    if (journey == null) return _buildLoading(tier.colors);

    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return SafeArea(
      child: RefreshIndicator(
        color: c.primary,
        onRefresh: _loadData,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics(),
          ),
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Mountain Hero Card ────────────────────────────────────
              _MountainHeroCard(
                journey: journey,
                tier: tier,
                levelNames: _levelNames,
                levelColors: _levelColors,
                pulseAnimation: _pulseController,
              ),
              const SizedBox(height: 20),

              // ── Engagement Stats Row ──────────────────────────────────
              _EngagementStatsRow(
                engagement: journey.engagement,
                tier: tier,
              ),
              const SizedBox(height: 24),

              // ── Growth Sparkline ──────────────────────────────────────
              if (_sparklinePoints.length >= 2) ...[
                Text(
                  'Score Over Time',
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.headlineSize,
                    fontWeight: t.headlineWeight,
                    color: c.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  height: 160,
                  decoration: BoxDecoration(
                    color: c.cardBg,
                    borderRadius: BorderRadius.circular(s.cardRadius),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.06),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.fromLTRB(12, 16, 16, 12),
                  child: CustomPaint(
                    painter: _SparklinePainter(
                      points: _sparklinePoints,
                      lineColor: c.primary,
                      fillColor: c.primary.withOpacity(0.12),
                      baselineDotColor: KiwiColors.kiwiGreen,
                      currentDotColor: c.primary,
                      textColor: c.textMuted,
                      fontFamily: t.fontFamily,
                    ),
                    size: Size.infinite,
                  ),
                ),
                const SizedBox(height: 24),
              ],

              // ── Topic Heatmap ─────────────────────────────────────────
              if (_topics.isNotEmpty) ...[
                Text(
                  'Your Topics',
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.headlineSize,
                    fontWeight: t.headlineWeight,
                    color: c.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),
                _TopicHeatmapGrid(
                  topics: _topics,
                  tier: tier,
                  levelColors: _levelColors,
                  onPractice: widget.onStartPractice,
                ),
                const SizedBox(height: 24),
              ],

              // ── Milestone Timeline ────────────────────────────────────
              if (_milestones.isNotEmpty) ...[
                Text(
                  'Your Journey',
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.headlineSize,
                    fontWeight: t.headlineWeight,
                    color: c.textPrimary,
                  ),
                ),
                const SizedBox(height: 12),
                _MilestoneTimeline(
                  milestones: _milestones,
                  tier: tier,
                ),
              ],

              // ── Retake Diagnostic ─────────────────────────────────────
              if (journey.suggestedRetake) ...[
                const SizedBox(height: 20),
                Center(
                  child: TextButton.icon(
                    onPressed: widget.onStartDiagnostic,
                    icon: Icon(Icons.replay_rounded, color: c.primary),
                    label: Text(
                      'Retake Diagnostic',
                      style: TextStyle(
                        fontFamily: t.fontFamily,
                        fontSize: t.buttonSize,
                        fontWeight: FontWeight.w600,
                        color: c.primary,
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

// =============================================================================
// PRIVATE HELPER WIDGETS
// =============================================================================

// ── Sparkline data ──────────────────────────────────────────────────────────

class _SparklinePoint {
  final String date;
  final double score;
  const _SparklinePoint({required this.date, required this.score});
}

// ── No-diagnostic Hero Card ─────────────────────────────────────────────────

class _NoDiagnosticHeroCard extends StatelessWidget {
  final KiwiTier tier;
  final List<String> levelNames;
  final List<Color> levelColors;
  final VoidCallback onStart;

  const _NoDiagnosticHeroCard({
    required this.tier,
    required this.levelNames,
    required this.levelColors,
    required this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(s.cardRadius),
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0xFF1A237E), // deep blue
            Color(0xFF2E7D32), // forest green
            Color(0xFF4CAF50), // green base
          ],
          stops: [0.0, 0.65, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1A237E).withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 20),
      child: Column(
        children: [
          // Title
          Text(
            'Start Your Math Journey!',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: t.fontFamily,
              fontSize: t.headlineSize + 2,
              fontWeight: FontWeight.w800,
              color: Colors.white,
              height: 1.2,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Take a quick 15-minute diagnostic to see where you are',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: t.fontFamily,
              fontSize: t.chipSize,
              color: Colors.white.withOpacity(0.85),
              height: 1.3,
            ),
          ),
          const SizedBox(height: 16),

          // Mountain level camps — 2-column grid (L6-L4 left, L3-L1 right)
          Row(
            children: [
              // Left column: L6, L5, L4 (top levels)
              Expanded(
                child: Column(
                  children: List.generate(3, (i) {
                    final idx = 5 - i; // L6, L5, L4
                    return Padding(
                      padding: EdgeInsets.only(bottom: i < 2 ? 8 : 0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 26,
                            height: 26,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: levelColors[idx],
                              border: Border.all(
                                  color: Colors.white.withOpacity(0.5), width: 1.5),
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              'L${idx + 1}',
                              style: TextStyle(
                                fontFamily: t.fontFamily,
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: Colors.black87,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            levelNames[idx],
                            style: TextStyle(
                              fontFamily: t.fontFamily,
                              fontSize: t.chipSize,
                              color: Colors.white.withOpacity(0.9),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ),
              ),
              // Right column: L3, L2, L1 (entry levels)
              Expanded(
                child: Column(
                  children: List.generate(3, (i) {
                    final idx = 2 - i; // L3, L2, L1
                    return Padding(
                      padding: EdgeInsets.only(bottom: i < 2 ? 8 : 0),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 26,
                            height: 26,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: levelColors[idx],
                              border: Border.all(
                                  color: Colors.white.withOpacity(0.5), width: 1.5),
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              'L${idx + 1}',
                              style: TextStyle(
                                fontFamily: t.fontFamily,
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: Colors.black87,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            levelNames[idx],
                            style: TextStyle(
                              fontFamily: t.fontFamily,
                              fontSize: t.chipSize,
                              color: Colors.white.withOpacity(0.9),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // CTA Button
          SizedBox(
            width: double.infinity,
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(s.buttonRadius),
                gradient: LinearGradient(
                  colors: [c.buttonGradientStart, c.buttonGradientEnd],
                ),
                boxShadow: [
                  BoxShadow(
                    color: c.buttonGradientEnd.withOpacity(0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: ElevatedButton(
                onPressed: onStart,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  padding: s.buttonPadding,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(s.buttonRadius),
                  ),
                ),
                child: Text(
                  'Begin Diagnostic',
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.buttonSize + 1,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Info Pill ────────────────────────────────────────────────────────────────

class _InfoPill extends StatelessWidget {
  final IconData icon;
  final String label;
  final KiwiTier tier;

  const _InfoPill({
    required this.icon,
    required this.label,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: c.cardBg,
          borderRadius: BorderRadius.circular(s.chipRadius),
          border: Border.all(color: c.topicCardBorder),
        ),
        child: Column(
          children: [
            Icon(icon, size: 22, color: c.primary),
            const SizedBox(height: 4),
            Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: t.fontFamily,
                fontSize: t.chipSize,
                fontWeight: FontWeight.w600,
                color: c.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Discover Card ───────────────────────────────────────────────────────────

class _DiscoverCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final KiwiTier tier;

  const _DiscoverCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return Container(
      padding: s.cardPadding,
      decoration: BoxDecoration(
        color: c.cardBg,
        borderRadius: BorderRadius.circular(s.cardRadius),
        border: Border.all(color: c.topicCardBorder),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: c.primary.withOpacity(0.1),
            ),
            child: Icon(icon, color: c.primary, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.bodySize,
                    fontWeight: FontWeight.w700,
                    color: c.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.chipSize,
                    color: c.textMuted,
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

// ═════════════════════════════════════════════════════════════════════════════
// MOUNTAIN HERO CARD (journey state)
// ═════════════════════════════════════════════════════════════════════════════

class _MountainHeroCard extends StatelessWidget {
  final GrowthJourney journey;
  final KiwiTier tier;
  final List<String> levelNames;
  final List<Color> levelColors;
  final Animation<double> pulseAnimation;

  const _MountainHeroCard({
    required this.journey,
    required this.tier,
    required this.levelNames,
    required this.levelColors,
    required this.pulseAnimation,
  });

  @override
  Widget build(BuildContext context) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;
    final current = journey.current;
    final baseline = journey.baseline;
    final lvlIdx = (current.level - 1).clamp(0, 5);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(s.cardRadius),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            const Color(0xFF0D47A1),
            const Color(0xFF1B5E20).withOpacity(0.95),
            const Color(0xFF2E7D32),
          ],
          stops: const [0.0, 0.55, 1.0],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0D47A1).withOpacity(0.35),
            blurRadius: 24,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // Level badge
          AnimatedBuilder(
            animation: pulseAnimation,
            builder: (context, child) {
              final scale = 1.0 + pulseAnimation.value * 0.05;
              return Transform.scale(
                scale: scale,
                child: Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: levelColors[lvlIdx],
                    border: Border.all(color: Colors.white, width: 3),
                    boxShadow: [
                      BoxShadow(
                        color: levelColors[lvlIdx].withOpacity(0.6),
                        blurRadius: 16,
                      ),
                    ],
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    'L${current.level}',
                    style: TextStyle(
                      fontFamily: t.fontFamily,
                      fontSize: 24,
                      fontWeight: FontWeight.w900,
                      color: Colors.black87,
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 12),

          // Level name
          Text(
            current.name,
            style: TextStyle(
              fontFamily: t.fontFamily,
              fontSize: t.headlineSize + 2,
              fontWeight: FontWeight.w800,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 6),

          // Scale score
          Text(
            '${current.scaleScore}',
            style: TextStyle(
              fontFamily: t.fontFamily,
              fontSize: 36,
              fontWeight: FontWeight.w900,
              color: Colors.white,
              height: 1.1,
            ),
          ),
          Text(
            'Scale Score',
            style: TextStyle(
              fontFamily: t.fontFamily,
              fontSize: t.chipSize,
              color: Colors.white.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 16),

          // Journey text
          if (baseline != null)
            Text(
              'You started at L${baseline.level} ${baseline.name}',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: t.fontFamily,
                fontSize: t.bodySize - 1,
                color: Colors.white.withOpacity(0.8),
              ),
            ),
          const SizedBox(height: 12),

          // Delta indicators
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (journey.deltaLevels != 0)
                _DeltaChip(
                  label:
                      '${journey.deltaLevels > 0 ? '+' : ''}${journey.deltaLevels} level${journey.deltaLevels.abs() != 1 ? 's' : ''}',
                  positive: journey.deltaLevels > 0,
                  tier: tier,
                ),
              if (journey.deltaLevels != 0 && journey.deltaScale != 0)
                const SizedBox(width: 10),
              if (journey.deltaScale != 0)
                _DeltaChip(
                  label:
                      '${journey.deltaScale > 0 ? '+' : ''}${journey.deltaScale} pts',
                  positive: journey.deltaScale > 0,
                  tier: tier,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Delta Chip ──────────────────────────────────────────────────────────────

class _DeltaChip extends StatelessWidget {
  final String label;
  final bool positive;
  final KiwiTier tier;

  const _DeltaChip({
    required this.label,
    required this.positive,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    final bg = positive
        ? KiwiColors.kiwiGreen.withOpacity(0.25)
        : KiwiColors.coral.withOpacity(0.25);
    final fg = positive
        ? const Color(0xFFA5D6A7)
        : const Color(0xFFFFAB91);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            positive ? Icons.arrow_upward_rounded : Icons.arrow_downward_rounded,
            size: 14,
            color: fg,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontFamily: tier.typography.fontFamily,
              fontSize: tier.typography.chipSize,
              fontWeight: FontWeight.w700,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// ENGAGEMENT STATS ROW
// ═════════════════════════════════════════════════════════════════════════════

class _EngagementStatsRow extends StatelessWidget {
  final GrowthEngagement engagement;
  final KiwiTier tier;

  const _EngagementStatsRow({
    required this.engagement,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    final items = <_StatItem>[
      _StatItem('\u{1F48E}', '${engagement.totalGems}', 'gems'),
      _StatItem('\u{1F525}', '${engagement.currentStreak}', 'day streak'),
      _StatItem('\u{1F3C5}', '${engagement.badgesEarned}', 'badges'),
      _StatItem('\u{1F4DD}', '${engagement.worksheetsCompleted}', 'worksheets'),
      _StatItem('\u{2B50}', '${engagement.totalQuestionsAnswered}', 'questions'),
      _StatItem('\u{1F4AA}', '${engagement.practiceSessions}', 'sessions'),
      if (engagement.clanWarsWon > 0)
        _StatItem('\u{2694}\u{FE0F}', '${engagement.clanWarsWon}', 'wars won'),
      if (engagement.dailyPuzzlesSolved > 0)
        _StatItem('\u{1F9E9}', '${engagement.dailyPuzzlesSolved}', 'puzzles'),
    ];

    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return SizedBox(
      height: 72,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        physics: const BouncingScrollPhysics(),
        itemCount: items.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (_, i) {
          final item = items[i];
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: c.cardBg,
              borderRadius: BorderRadius.circular(s.chipRadius),
              border: Border.all(color: c.topicCardBorder),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(item.emoji, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 6),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.value,
                      style: TextStyle(
                        fontFamily: t.fontFamily,
                        fontSize: t.bodySize,
                        fontWeight: FontWeight.w800,
                        color: c.textPrimary,
                      ),
                    ),
                    Text(
                      item.label,
                      style: TextStyle(
                        fontFamily: t.fontFamily,
                        fontSize: t.chipSize - 2,
                        color: c.textMuted,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _StatItem {
  final String emoji;
  final String value;
  final String label;
  const _StatItem(this.emoji, this.value, this.label);
}

// ═════════════════════════════════════════════════════════════════════════════
// SPARKLINE PAINTER
// ═════════════════════════════════════════════════════════════════════════════

class _SparklinePainter extends CustomPainter {
  final List<_SparklinePoint> points;
  final Color lineColor;
  final Color fillColor;
  final Color baselineDotColor;
  final Color currentDotColor;
  final Color textColor;
  final String fontFamily;

  _SparklinePainter({
    required this.points,
    required this.lineColor,
    required this.fillColor,
    required this.baselineDotColor,
    required this.currentDotColor,
    required this.textColor,
    required this.fontFamily,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (points.length < 2) return;

    final scores = points.map((p) => p.score).toList();
    final minScore = scores.reduce(math.min) - 10;
    final maxScore = scores.reduce(math.max) + 10;
    final range = maxScore - minScore;

    const leftPad = 36.0;
    const rightPad = 16.0;
    const topPad = 8.0;
    const bottomPad = 24.0;
    final chartW = size.width - leftPad - rightPad;
    final chartH = size.height - topPad - bottomPad;

    double xOf(int i) =>
        leftPad + (i / (points.length - 1)) * chartW;
    double yOf(double score) =>
        topPad + chartH - ((score - minScore) / range) * chartH;

    // Y-axis labels
    final labelPaint = TextPainter(textDirection: TextDirection.ltr);
    for (var v in [minScore, (minScore + maxScore) / 2, maxScore]) {
      labelPaint
        ..text = TextSpan(
          text: v.round().toString(),
          style: TextStyle(
            fontFamily: fontFamily,
            fontSize: 10,
            color: textColor,
          ),
        )
        ..layout();
      labelPaint.paint(
        canvas,
        Offset(leftPad - labelPaint.width - 6, yOf(v) - labelPaint.height / 2),
      );
    }

    // Grid lines
    final gridPaint = Paint()
      ..color = textColor.withOpacity(0.15)
      ..strokeWidth = 0.5;
    for (var v in [minScore, (minScore + maxScore) / 2, maxScore]) {
      canvas.drawLine(
        Offset(leftPad, yOf(v)),
        Offset(size.width - rightPad, yOf(v)),
        gridPaint,
      );
    }

    // Build path
    final path = Path();
    final fillPath = Path();
    for (int i = 0; i < points.length; i++) {
      final x = xOf(i);
      final y = yOf(scores[i]);
      if (i == 0) {
        path.moveTo(x, y);
        fillPath.moveTo(x, topPad + chartH);
        fillPath.lineTo(x, y);
      } else {
        // Smooth curve using quadratic bezier
        final prevX = xOf(i - 1);
        final prevY = yOf(scores[i - 1]);
        final cpX = (prevX + x) / 2;
        path.quadraticBezierTo(cpX, prevY, (cpX + x) / 2, (prevY + y) / 2);
        path.quadraticBezierTo((cpX + x) / 2, (prevY + y) / 2, x, y);
        fillPath.quadraticBezierTo(cpX, prevY, (cpX + x) / 2, (prevY + y) / 2);
        fillPath.quadraticBezierTo((cpX + x) / 2, (prevY + y) / 2, x, y);
      }
    }

    // Fill under curve
    fillPath.lineTo(xOf(points.length - 1), topPad + chartH);
    fillPath.close();
    canvas.drawPath(fillPath, Paint()..color = fillColor);

    // Line
    canvas.drawPath(
      path,
      Paint()
        ..color = lineColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5
        ..strokeCap = StrokeCap.round,
    );

    // Baseline dot (first point)
    canvas.drawCircle(
      Offset(xOf(0), yOf(scores[0])),
      5,
      Paint()..color = baselineDotColor,
    );
    // Baseline flag
    final flagPath = Path()
      ..moveTo(xOf(0), yOf(scores[0]) - 6)
      ..lineTo(xOf(0), yOf(scores[0]) - 20)
      ..lineTo(xOf(0) + 12, yOf(scores[0]) - 16)
      ..lineTo(xOf(0), yOf(scores[0]) - 12);
    canvas.drawPath(flagPath, Paint()..color = baselineDotColor);

    // Current dot (last point)
    final lastX = xOf(points.length - 1);
    final lastY = yOf(scores.last);
    canvas.drawCircle(
      Offset(lastX, lastY),
      7,
      Paint()
        ..color = currentDotColor.withOpacity(0.3)
        ..style = PaintingStyle.fill,
    );
    canvas.drawCircle(
      Offset(lastX, lastY),
      4,
      Paint()..color = currentDotColor,
    );
  }

  @override
  bool shouldRepaint(covariant _SparklinePainter old) =>
      points != old.points || lineColor != old.lineColor;
}

// ═════════════════════════════════════════════════════════════════════════════
// TOPIC HEATMAP GRID
// ═════════════════════════════════════════════════════════════════════════════

class _TopicHeatmapGrid extends StatelessWidget {
  final List<TopicGrowth> topics;
  final KiwiTier tier;
  final List<Color> levelColors;
  final void Function(String topicId, String topicName) onPractice;

  const _TopicHeatmapGrid({
    required this.topics,
    required this.tier,
    required this.levelColors,
    required this.onPractice,
  });

  @override
  Widget build(BuildContext context) {
    // Sort: weakest first (needsLevelup first, then by currentLevel ascending).
    final sorted = List<TopicGrowth>.from(topics)
      ..sort((a, b) {
        if (a.needsLevelup && !b.needsLevelup) return -1;
        if (!a.needsLevelup && b.needsLevelup) return 1;
        return a.currentLevel.compareTo(b.currentLevel);
      });

    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: sorted.map((topic) {
        return SizedBox(
          width: (MediaQuery.of(context).size.width - 42) / 2,
          child: _TopicCard(
            topic: topic,
            tier: tier,
            levelColors: levelColors,
            onPractice: () => onPractice(topic.topicId, topic.name),
          ),
        );
      }).toList(),
    );
  }
}

class _TopicCard extends StatelessWidget {
  final TopicGrowth topic;
  final KiwiTier tier;
  final List<Color> levelColors;
  final VoidCallback onPractice;

  const _TopicCard({
    required this.topic,
    required this.tier,
    required this.levelColors,
    required this.onPractice,
  });

  @override
  Widget build(BuildContext context) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;
    final lvlIdx = (topic.currentLevel - 1).clamp(0, 5);
    final lvlColor = levelColors[lvlIdx];
    final delta = topic.currentLevel - topic.baselineLevel;

    // Theta progress: map to 0-1 range within current level.
    // Levels have theta boundaries roughly [-3, 3] mapped to 6 levels,
    // so we approximate progress as fractional part.
    final thetaNorm = ((topic.currentTheta + 3) / 6).clamp(0.0, 1.0);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: c.cardBg,
        borderRadius: BorderRadius.circular(s.cardRadius),
        border: Border.all(
          color: topic.isSuperpower
              ? KiwiColors.gemGold
              : c.topicCardBorder,
          width: topic.isSuperpower ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: level badge + delta arrow
          Row(
            children: [
              Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: lvlColor,
                ),
                alignment: Alignment.center,
                child: Text(
                  'L${topic.currentLevel}',
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: Colors.black87,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  topic.name,
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.chipSize,
                    fontWeight: FontWeight.w700,
                    color: c.textPrimary,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Delta arrow
          Row(
            children: [
              Icon(
                delta > 0
                    ? Icons.arrow_upward_rounded
                    : delta < 0
                        ? Icons.arrow_downward_rounded
                        : Icons.arrow_forward_rounded,
                size: 14,
                color: delta > 0
                    ? KiwiColors.kiwiGreen
                    : delta < 0
                        ? KiwiColors.coral
                        : c.textMuted,
              ),
              const SizedBox(width: 2),
              Text(
                delta != 0 ? '${delta.abs()}' : '0',
                style: TextStyle(
                  fontFamily: t.fontFamily,
                  fontSize: t.chipSize,
                  fontWeight: FontWeight.w700,
                  color: delta > 0
                      ? KiwiColors.kiwiGreen
                      : delta < 0
                          ? KiwiColors.coral
                          : c.textMuted,
                ),
              ),
              const Spacer(),
              Text(
                '${topic.accuracy.round()}%',
                style: TextStyle(
                  fontFamily: t.fontFamily,
                  fontSize: t.chipSize - 1,
                  color: c.textMuted,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),

          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: thetaNorm,
              backgroundColor: c.topicCardBorder.withOpacity(0.4),
              valueColor: AlwaysStoppedAnimation(lvlColor),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 8),

          // Badges / CTA
          if (topic.isSuperpower)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: KiwiColors.gemGold.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '\u{2B50} Superpower',
                style: TextStyle(
                  fontFamily: t.fontFamily,
                  fontSize: t.chipSize - 2,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFFFF8F00),
                ),
              ),
            )
          else if (topic.needsLevelup)
            GestureDetector(
              onTap: onPractice,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [c.buttonGradientStart, c.buttonGradientEnd],
                  ),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  'Level Up!',
                  style: TextStyle(
                    fontFamily: t.fontFamily,
                    fontSize: t.chipSize - 2,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// MILESTONE TIMELINE
// ═════════════════════════════════════════════════════════════════════════════

class _MilestoneTimeline extends StatelessWidget {
  final List<GrowthMilestone> milestones;
  final KiwiTier tier;

  const _MilestoneTimeline({
    required this.milestones,
    required this.tier,
  });

  static const _typeIcons = {
    'diagnostic': '\u{1F6A9}',
    'level_up': '\u{2B06}\u{FE0F}',
    'topic_breakthrough': '\u{2B50}',
    'streak': '\u{1F525}',
    'gems': '\u{1F48E}',
    'badge': '\u{1F3C5}',
    'worksheet': '\u{1F4DD}',
    'clan_war': '\u{2694}\u{FE0F}',
  };

  static const _typeColors = {
    'diagnostic': Color(0xFF42A5F5),
    'level_up': Color(0xFF66BB6A),
    'topic_breakthrough': Color(0xFFFFD600),
    'streak': Color(0xFFFF8A65),
    'gems': Color(0xFF448AFF),
    'badge': Color(0xFFCE93D8),
    'worksheet': Color(0xFF4DB6AC),
    'clan_war': Color(0xFFFF7043),
  };

  @override
  Widget build(BuildContext context) {
    final c = tier.colors;
    final t = tier.typography;
    final s = tier.shape;

    return Container(
      padding: s.cardPadding,
      decoration: BoxDecoration(
        color: c.cardBg,
        borderRadius: BorderRadius.circular(s.cardRadius),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        children: List.generate(milestones.length, (i) {
          final m = milestones[i];
          final isLast = i == milestones.length - 1;
          final dotColor = _typeColors[m.type] ?? c.primary;
          final emoji = m.icon.isNotEmpty
              ? m.icon
              : (_typeIcons[m.type] ?? '\u{1F4CC}');

          return IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Timeline rail
                SizedBox(
                  width: 36,
                  child: Column(
                    children: [
                      Container(
                        width: 28,
                        height: 28,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: dotColor.withOpacity(0.15),
                          border: Border.all(color: dotColor, width: 2),
                        ),
                        alignment: Alignment.center,
                        child: Text(emoji, style: const TextStyle(fontSize: 12)),
                      ),
                      if (!isLast)
                        Expanded(
                          child: Container(
                            width: 2,
                            color: c.topicCardBorder,
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                // Content
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(bottom: isLast ? 0 : 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          m.description,
                          style: TextStyle(
                            fontFamily: t.fontFamily,
                            fontSize: t.bodySize - 1,
                            fontWeight: FontWeight.w600,
                            color: c.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _formatDate(m.date),
                          style: TextStyle(
                            fontFamily: t.fontFamily,
                            fontSize: t.chipSize - 1,
                            color: c.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        }),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      final now = DateTime.now();
      final diff = now.difference(date);
      if (diff.inDays == 0) return 'Today';
      if (diff.inDays == 1) return 'Yesterday';
      if (diff.inDays < 7) return '${diff.inDays} days ago';
      if (diff.inDays < 14) return 'Last week';
      if (diff.inDays < 30) return '${(diff.inDays / 7).floor()} weeks ago';
      if (diff.inDays < 60) return 'Last month';
      return '${(diff.inDays / 30).floor()} months ago';
    } catch (_) {
      return dateStr;
    }
  }
}
