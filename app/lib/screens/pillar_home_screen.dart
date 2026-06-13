import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/pillar_progress.dart';
import '../services/pillar_api.dart';
import '../theme/kiwi_theme.dart';
import 'pillar_detail_screen.dart';

/// Pillar Home — the new Olympiad Practice tab landing page.
///
/// Shows a 2×2 grid of the 4 math olympiad pillars:
///   Algebra | Number Theory | Combinatorics | Geometry
///
/// Each card shows pillar name, emoji, tagline, current level, and mastery %.
/// Tapping a card navigates to PillarDetailScreen.
class PillarHomeScreen extends StatefulWidget {
  final String userId;
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;

  /// Opens today's daily puzzle (plumbed from _AppShell via OlympiadTabScreen).
  final VoidCallback? onDailyChallenge;

  const PillarHomeScreen({
    super.key,
    required this.userId,
    required this.selectedGrade,
    required this.onGradeChanged,
    this.onDailyChallenge,
  });

  @override
  State<PillarHomeScreen> createState() => _PillarHomeScreenState();
}

class _PillarHomeScreenState extends State<PillarHomeScreen> {
  PillarSummary? _summary;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadProgress();
  }

  @override
  void didUpdateWidget(covariant PillarHomeScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.userId != widget.userId ||
        oldWidget.selectedGrade != widget.selectedGrade) {
      _loadProgress();
    }
  }

  Future<void> _loadProgress() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final summary = await PillarApi.fetchProgress(userId: widget.userId);
      if (mounted) setState(() { _summary = summary; _loading = false; });
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString();
          // Use empty summary as fallback
          _summary = PillarSummary(pillars: {});
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;

    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(KiwiSpacing.lg, KiwiSpacing.md, KiwiSpacing.lg, KiwiSpacing.xl),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Section header ─────────────────────────────────────────
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: colors.primary.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '4 PILLARS',
                  style: TextStyle(
                    fontSize: typo.chipSize - 3,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                    color: colors.primary,
                    fontFamily: typo.fontFamily,
                  ),
                ),
              ),
              SizedBox(width: KiwiSpacing.sm),
              Text(
                'Grade ${widget.selectedGrade}',
                style: TextStyle(
                  fontSize: typo.chipSize,
                  color: colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ],
          ),
          SizedBox(height: KiwiSpacing.xs),
          Text(
            'Master each pillar from fundamentals to olympiad',
            style: TextStyle(
              fontSize: typo.chipSize,
              color: colors.textMuted,
              fontFamily: typo.fontFamily,
            ),
          ),
          SizedBox(height: KiwiSpacing.lg),

          // ── Pillar grid (2×2) ─────────────────────────────────────
          if (_loading)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(40),
                child: CircularProgressIndicator(),
              ),
            )
          else
            _buildPillarGrid(colors, typo, tier),

          SizedBox(height: KiwiSpacing.lg),

          // ── Daily Challenge card ──────────────────────────────────
          _DailyChallengeCard(
            grade: widget.selectedGrade,
            colors: colors,
            typo: typo,
            tier: tier,
            onTap: widget.onDailyChallenge,
          ),
        ],
      ),
    );
  }

  Widget _buildPillarGrid(KiwiTierColors colors, KiwiTierTypography typo, KiwiTier tier) {
    final pillars = PillarMeta.all;

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 0.85,
      children: pillars.map((meta) {
        final progress = _summary?.pillars[meta.id];
        return _PillarCard(
          meta: meta,
          progress: progress,
          colors: colors,
          typo: typo,
          tier: tier,
          onTap: () => _openPillar(meta),
        );
      }).toList(),
    );
  }

  void _openPillar(PillarMeta meta) {
    HapticFeedback.lightImpact();
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PillarDetailScreen(
          userId: widget.userId,
          pillar: meta,
          grade: widget.selectedGrade,
          progress: _summary?.pillars[meta.id],
        ),
      ),
    );
  }
}

// =============================================================================
// Pillar card — displays one of the 4 pillars
// =============================================================================
class _PillarCard extends StatelessWidget {
  final PillarMeta meta;
  final PillarProgress? progress;
  final KiwiTierColors colors;
  final KiwiTierTypography typo;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _PillarCard({
    required this.meta,
    this.progress,
    required this.colors,
    required this.typo,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final pillarColor = Color(int.parse('FF${meta.colorHex}', radix: 16));
    final mastery = progress?.masteryPercent ?? 0;
    final currentLevel = progress?.currentLevel ?? 1;

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(tier.shape.cardRadius),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(tier.shape.cardRadius),
            border: Border.all(color: pillarColor.withOpacity(0.2), width: 1.5),
            boxShadow: [
              BoxShadow(
                color: pillarColor.withOpacity(0.08),
                blurRadius: 10,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Emoji + level badge row
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          pillarColor.withOpacity(0.15),
                          pillarColor.withOpacity(0.05),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Center(
                      child: Text(meta.emoji, style: const TextStyle(fontSize: 24)),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: pillarColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'L$currentLevel',
                      style: TextStyle(
                        fontSize: typo.chipSize - 2,
                        fontWeight: FontWeight.w800,
                        color: pillarColor,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ),
                ],
              ),
              const Spacer(),

              // Name
              Text(
                meta.name,
                style: TextStyle(
                  fontSize: typo.topicNameSize,
                  fontWeight: FontWeight.w700,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              SizedBox(height: KiwiSpacing.xs - 2),

              // Tagline
              Text(
                meta.tagline,
                style: TextStyle(
                  fontSize: typo.chipSize - 2,
                  color: colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              SizedBox(height: KiwiSpacing.sm),

              // Progress bar
              ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: SizedBox(
                  height: 4,
                  child: LinearProgressIndicator(
                    value: mastery / 100.0,
                    backgroundColor: KiwiColors.pathLocked,
                    valueColor: AlwaysStoppedAnimation<Color>(pillarColor),
                  ),
                ),
              ),
              SizedBox(height: KiwiSpacing.xs - 2),

              // Mastery label
              Text(
                mastery > 0 ? '${mastery.toStringAsFixed(0)}% mastery' : 'Start learning',
                style: TextStyle(
                  fontSize: typo.chipSize - 3,
                  fontWeight: FontWeight.w600,
                  color: mastery > 0 ? pillarColor : colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// =============================================================================
// Daily Challenge card
// =============================================================================
class _DailyChallengeCard extends StatelessWidget {
  final int grade;
  final KiwiTierColors colors;
  final KiwiTierTypography typo;
  final KiwiTier tier;
  final VoidCallback? onTap;

  const _DailyChallengeCard({
    required this.grade,
    required this.colors,
    required this.typo,
    required this.tier,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap == null
          ? null
          : () {
              HapticFeedback.lightImpact();
              onTap!();
            },
      child: Container(
      width: double.infinity,
      padding: EdgeInsets.all(KiwiSpacing.lg),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            colors.buttonGradientStart,
            colors.buttonGradientEnd,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
        boxShadow: [
          BoxShadow(
            color: colors.primary.withOpacity(0.25),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(tier.shape.chipRadius / 2),
            ),
            child: const Icon(Icons.emoji_events, color: Colors.white, size: 22),
          ),
          SizedBox(width: KiwiSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Daily Challenge',
                  style: TextStyle(
                    fontSize: typo.bodySize,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                    fontFamily: typo.fontFamily,
                  ),
                ),
                SizedBox(height: KiwiSpacing.xs - 2),
                Text(
                  'One brain-teaser a day keeps boredom away',
                  style: TextStyle(
                    fontSize: typo.chipSize - 3,
                    fontWeight: FontWeight.w500,
                    color: Colors.white.withOpacity(0.8),
                    fontFamily: typo.fontFamily,
                  ),
                ),
              ],
            ),
          ),
          Icon(
            Icons.arrow_forward_ios,
            size: 16,
            color: Colors.white.withOpacity(0.7),
          ),
        ],
      ),
      ),
    );
  }
}
