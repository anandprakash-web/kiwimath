import 'package:flutter/material.dart';

import '../models/clan.dart';
import '../theme/kiwi_theme.dart';

/// Grade-scoped clan leaderboard with top-3 podium and scrollable rankings.
///
/// Layout:
///   1. Orange gradient header with grade filter dropdown
///   2. Top-3 podium (gold / silver / bronze)
///   3. Scrollable list ranks 4-20
///   4. Current clan row highlighted with orange border
class ClanLeaderboardScreen extends StatelessWidget {
  final List<LeaderboardEntry> entries;
  final String? currentClanId;
  final int selectedGrade;
  final void Function(int grade)? onGradeChanged;
  final VoidCallback onBack;

  const ClanLeaderboardScreen({
    super.key,
    required this.entries,
    this.currentClanId,
    required this.selectedGrade,
    this.onGradeChanged,
    required this.onBack,
  });

  // Podium accent colors
  static const _gold = KiwiColors.gemGold;
  static const _silver = Color(0xFFB0BEC5); // decorative — no token
  static const _bronze = KiwiColors.streakWarm;

  @override
  Widget build(BuildContext context) {
    final top3 = entries.where((e) => e.rank <= 3).toList()
      ..sort((a, b) => a.rank.compareTo(b.rank));
    final rest = entries.where((e) => e.rank > 3).toList()
      ..sort((a, b) => a.rank.compareTo(b.rank));

    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context),
            Expanded(
              child: CustomScrollView(
                slivers: [
                  // Top 3 podium
                  if (top3.isNotEmpty)
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: EdgeInsets.fromLTRB(KiwiSpacing.xl, KiwiSpacing.xl, KiwiSpacing.xl, KiwiSpacing.sm),
                        child: _buildPodium(top3),
                      ),
                    ),

                  // Section label
                  if (rest.isNotEmpty)
                    const SliverToBoxAdapter(
                      child: Padding(
                        padding: EdgeInsets.fromLTRB(KiwiSpacing.xxl - 4, KiwiSpacing.lg, KiwiSpacing.xxl - 4, KiwiSpacing.sm),
                        child: Text(
                          'Rankings',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: KiwiColors.textDark,
                          ),
                        ),
                      ),
                    ),

                  // Remaining list
                  SliverPadding(
                    padding: EdgeInsets.fromLTRB(KiwiSpacing.xl, 0, KiwiSpacing.xl, KiwiSpacing.xxl + KiwiSpacing.sm),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) =>
                            _buildRankRow(rest[index]),
                        childCount: rest.length,
                      ),
                    ),
                  ),

                  // Empty state
                  if (entries.isEmpty)
                    const SliverFillRemaining(
                      child: Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.emoji_events_outlined,
                                size: 56, color: KiwiColors.textMuted),
                            SizedBox(height: KiwiSpacing.md),
                            Text(
                              'No clans yet for this grade!',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: KiwiColors.textMid,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              'Be the first to create one',
                              style: TextStyle(
                                fontSize: 13,
                                color: KiwiColors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Header ───────────────────────────────────────────────────────────────

  Widget _buildHeader(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(KiwiSpacing.sm, KiwiSpacing.md, KiwiSpacing.lg, KiwiSpacing.lg),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: onBack,
            icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
          ),
          const Expanded(
            child: Text(
              'Clan Leaderboard',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: Colors.white,
                letterSpacing: 0.3,
              ),
            ),
          ),
          // Grade filter dropdown
          Container(
            padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.sm + 2, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(KiwiSpacing.sm + 2),
              border: Border.all(color: Colors.white.withOpacity(0.4)),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<int>(
                value: selectedGrade,
                dropdownColor: KiwiColors.kiwiPrimaryDark,
                iconEnabledColor: Colors.white,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: Colors.white,
                ),
                items: List.generate(
                  5,
                  (i) => DropdownMenuItem(
                    value: i + 1,
                    child: Text('Grade ${i + 1}'),
                  ),
                ),
                onChanged: onGradeChanged != null
                    ? (v) {
                        if (v != null) onGradeChanged!(v);
                      }
                    : null,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ── Podium ───────────────────────────────────────────────────────────────

  Widget _buildPodium(List<LeaderboardEntry> top3) {
    // Order for visual layout: 2nd, 1st, 3rd
    final first = top3.isNotEmpty ? top3[0] : null;
    final second = top3.length > 1 ? top3[1] : null;
    final third = top3.length > 2 ? top3[2] : null;

    return Container(
      padding: EdgeInsets.symmetric(vertical: KiwiSpacing.xl, horizontal: KiwiSpacing.sm),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 14,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // 2nd place
          if (second != null)
            Expanded(child: _podiumColumn(second, _silver, 80))
          else
            const Expanded(child: SizedBox()),

          // 1st place (taller)
          if (first != null)
            Expanded(child: _podiumColumn(first, _gold, 110))
          else
            const Expanded(child: SizedBox()),

          // 3rd place
          if (third != null)
            Expanded(child: _podiumColumn(third, _bronze, 60))
          else
            const Expanded(child: SizedBox()),
        ],
      ),
    );
  }

  Widget _podiumColumn(LeaderboardEntry entry, Color accent, double height) {
    final isCurrentClan = entry.clanId == currentClanId;
    final rankEmoji = entry.rank == 1
        ? '\u{1F947}'
        : entry.rank == 2
            ? '\u{1F948}'
            : '\u{1F949}';

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Rank emoji
        Text(rankEmoji, style: const TextStyle(fontSize: 28)),
        SizedBox(height: KiwiSpacing.xs + 2),

        // Crest
        Container(
          width: entry.rank == 1 ? 64 : 52,
          height: entry.rank == 1 ? 64 : 52,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [accent, accent.withOpacity(0.7)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
            border: isCurrentClan
                ? Border.all(color: KiwiColors.kiwiPrimary, width: 3)
                : null,
            boxShadow: [
              BoxShadow(
                color: accent.withOpacity(0.3),
                blurRadius: 8,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Center(
            child: Text(
              entry.crest.emoji,
              style: TextStyle(fontSize: entry.rank == 1 ? 28 : 22),
            ),
          ),
        ),
        SizedBox(height: KiwiSpacing.sm),

        // Clan name
        Text(
          entry.name,
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            fontSize: entry.rank == 1 ? 14 : 12,
            fontWeight: FontWeight.w700,
            color: KiwiColors.textDark,
          ),
        ),
        SizedBox(height: KiwiSpacing.xs),

        // Level badge
        Container(
          padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: 3),
          decoration: BoxDecoration(
            color: KiwiColors.xpPurple.withOpacity(0.1),
            borderRadius: BorderRadius.circular(KiwiSpacing.sm),
          ),
          child: Text(
            '${entry.clanLevel.emoji} Lv${entry.clanLevel.level}',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: KiwiColors.xpPurple,
            ),
          ),
        ),
        SizedBox(height: KiwiSpacing.xs),

        // Points
        Text(
          '${_formatPoints(entry.totalPoints)} pts',
          style: TextStyle(
            fontSize: entry.rank == 1 ? 15 : 13,
            fontWeight: FontWeight.w800,
            color: KiwiColors.kiwiPrimary,
          ),
        ),
        SizedBox(height: KiwiSpacing.sm),

        // Podium block
        Container(
          width: double.infinity,
          height: height,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [accent, accent.withOpacity(0.6)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
            borderRadius: BorderRadius.vertical(top: Radius.circular(KiwiSpacing.sm)),
          ),
          child: Center(
            child: Text(
              '#${entry.rank}',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ],
    );
  }

  // ── Rank Row (4-20) ──────────────────────────────────────────────────────

  Widget _buildRankRow(LeaderboardEntry entry) {
    final isCurrentClan = entry.clanId == currentClanId;

    return Container(
      margin: EdgeInsets.only(bottom: KiwiSpacing.sm + 2),
      padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.md + 2, vertical: KiwiSpacing.md),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(KiwiSpacing.md + 2),
        border: isCurrentClan
            ? Border.all(color: KiwiColors.kiwiPrimary, width: 2)
            : null,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(isCurrentClan ? 0.08 : 0.03),
            blurRadius: isCurrentClan ? 12 : 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          // Rank number
          SizedBox(
            width: 32,
            child: Text(
              '#${entry.rank}',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w800,
                color: isCurrentClan
                    ? KiwiColors.kiwiPrimary
                    : KiwiColors.textMid,
              ),
            ),
          ),
          SizedBox(width: KiwiSpacing.sm),

          // Crest
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: isCurrentClan
                  ? KiwiColors.kiwiPrimaryLight
                  : KiwiColors.kiwiPrimaryLight.withOpacity(0.5),
              borderRadius: BorderRadius.circular(KiwiSpacing.md),
            ),
            child: Center(
              child: Text(
                entry.crest.emoji,
                style: const TextStyle(fontSize: 22),
              ),
            ),
          ),
          SizedBox(width: KiwiSpacing.md),

          // Name + level
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  entry.name,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: isCurrentClan
                        ? KiwiColors.kiwiPrimaryDark
                        : KiwiColors.textDark,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                SizedBox(height: KiwiSpacing.xs - 1),
                Row(
                  children: [
                    Text(
                      '${entry.clanLevel.emoji} Lv${entry.clanLevel.level}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: KiwiColors.xpPurple,
                      ),
                    ),
                    SizedBox(width: KiwiSpacing.sm),
                    Text(
                      '${entry.memberCount} members',
                      style: const TextStyle(
                        fontSize: 11,
                        color: KiwiColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Points
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                _formatPoints(entry.totalPoints),
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                  color: isCurrentClan
                      ? KiwiColors.kiwiPrimary
                      : KiwiColors.textDark,
                ),
              ),
              const Text(
                'pts',
                style: TextStyle(
                  fontSize: 11,
                  color: KiwiColors.textMuted,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),

          // Highlight indicator for current clan
          if (isCurrentClan) ...[
            SizedBox(width: KiwiSpacing.sm),
            Container(
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: KiwiColors.kiwiPrimary,
                shape: BoxShape.circle,
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  static String _formatPoints(int points) {
    if (points >= 1000000) {
      return '${(points / 1000000).toStringAsFixed(1)}M';
    } else if (points >= 1000) {
      return '${(points / 1000).toStringAsFixed(1)}K';
    }
    return '$points';
  }
}
