import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/kiwi_theme.dart';
import '../models/clan.dart';
import '../widgets/squad_activity_bar.dart';

/// Main clan hub — displayed after a student has joined or created a clan.
///
/// Shows clan identity, XP progress, lifetime points, squad activity,
/// the active Picture Unravel challenge, invite code, and quick actions.
class ClanHubScreen extends StatelessWidget {
  final Clan clan;
  final ChallengeInfo? activeChallenge;
  final ChallengeProgress? challengeProgress;
  final List<DailySquadMember> squadMembers;
  final VoidCallback? onOpenChallenge;
  final VoidCallback? onOpenLeaderboard;
  final VoidCallback? onLeaveClan;
  final VoidCallback? onCopyInviteCode;

  const ClanHubScreen({
    super.key,
    required this.clan,
    this.activeChallenge,
    this.challengeProgress,
    this.squadMembers = const [],
    this.onOpenChallenge,
    this.onOpenLeaderboard,
    this.onLeaveClan,
    this.onCopyInviteCode,
  });

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  String _formatNumber(int n) {
    if (n >= 1000) {
      final thousands = n ~/ 1000;
      final remainder = (n % 1000) ~/ 100;
      return remainder > 0 ? '$thousands,${(n % 1000).toString().padLeft(3, '0')}' : '${thousands},000';
    }
    return n.toString();
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: CustomScrollView(
        slivers: [
          // 1. Header
          _buildHeader(context),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),

                  // 2. Clan XP Bar
                  _buildXpBar(),
                  const SizedBox(height: 20),

                  // 3. Points Cards Row
                  _buildPointsCards(),
                  const SizedBox(height: 24),

                  // 4. Squad Activity
                  _buildSquadActivity(),
                  const SizedBox(height: 24),

                  // 5. Active Challenge Preview
                  if (activeChallenge != null) ...[
                    _buildChallengePreview(),
                    const SizedBox(height: 24),
                  ],

                  // 6. Invite Code Section
                  if (clan.inviteCode != null) ...[
                    _buildInviteCode(),
                    const SizedBox(height: 24),
                  ],

                  // 7. Quick Actions
                  _buildQuickActions(context),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 1. Header — orange gradient with clan identity
  // ---------------------------------------------------------------------------

  Widget _buildHeader(BuildContext context) {
    return SliverAppBar(
      expandedHeight: 180,
      pinned: true,
      backgroundColor: KiwiColors.kiwiPrimary,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Crest + name row
                  Row(
                    children: [
                      // Crest emoji
                      Container(
                        width: 52,
                        height: 52,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          clan.crest.emoji,
                          style: const TextStyle(fontSize: 28),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              clan.name,
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w800,
                                color: Colors.white,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                // Level badge
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 10,
                                    vertical: 3,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Text(
                                    '${clan.clanLevel.emoji} ${clan.clanLevel.name}',
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.white,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                // Member count
                                Row(
                                  children: [
                                    const Icon(
                                      Icons.people_alt_rounded,
                                      size: 16,
                                      color: Colors.white70,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      '${clan.memberCount} members',
                                      style: const TextStyle(
                                        fontSize: 13,
                                        color: Colors.white70,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 2. Clan XP Bar
  // ---------------------------------------------------------------------------

  Widget _buildXpBar() {
    final level = clan.clanLevel;
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                '⭐ Clan XP',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.textDark,
                ),
              ),
              const Spacer(),
              Text(
                'Lvl ${level.level}',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.xpPurple,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: level.progress.clamp(0.0, 1.0),
              minHeight: 14,
              backgroundColor: KiwiColors.kiwiPrimaryLight,
              valueColor: const AlwaysStoppedAnimation<Color>(
                KiwiColors.kiwiPrimary,
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${_formatNumber(level.currentXp)} / ${_formatNumber(level.xpToNext)} XP',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: KiwiColors.textMid,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 3. Points Cards Row
  // ---------------------------------------------------------------------------

  Widget _buildPointsCards() {
    return Row(
      children: [
        Expanded(
          child: _pointCard(
            emoji: '\u{1F9E0}', // 🧠
            label: 'Brain',
            value: clan.lifetimeBrainPoints,
            color: KiwiColors.xpPurple,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _pointCard(
            emoji: '\u{1F4AA}', // 💪
            label: 'Brawn',
            value: clan.lifetimeBrawnPoints,
            color: KiwiColors.kiwiPrimary,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _pointCard(
            emoji: '\u{1F4DD}', // 📝
            label: 'Quiz',
            value: clan.lifetimeQuizPoints,
            color: KiwiColors.gemGold,
          ),
        ),
      ],
    );
  }

  Widget _pointCard({
    required String emoji,
    required String label,
    required int value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 24)),
          const SizedBox(height: 6),
          Text(
            _formatNumber(value),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '$label Pts',
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: KiwiColors.textMuted,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 4. Squad Activity
  // ---------------------------------------------------------------------------

  Widget _buildSquadActivity() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Today's Squad",
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        const SizedBox(height: 10),
        squadMembers.isNotEmpty
            ? SquadActivityBar(members: squadMembers)
            : Container(
                height: 64,
                decoration: BoxDecoration(
                  color: KiwiColors.cardBg,
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                alignment: Alignment.center,
                child: const Text(
                  'Waiting for squad activity...',
                  style: TextStyle(fontSize: 13, color: KiwiColors.textMuted),
                ),
              ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // 5. Active Challenge Preview
  // ---------------------------------------------------------------------------

  Widget _buildChallengePreview() {
    final challenge = activeChallenge!;
    final progress = challengeProgress;
    final revealPct = progress != null
        ? '${progress.revealPercentage.toStringAsFixed(0)}%'
        : '0%';

    return GestureDetector(
      onTap: onOpenChallenge,
      child: _card(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text(
                  '\u{1F5BC}\u{FE0F} Picture Unravel',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.xpPurple,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    color: KiwiColors.kiwiPrimaryLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '${challenge.daysRemaining}d left',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.kiwiPrimaryDark,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              challenge.title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 10),
            // Reveal progress mini-bar
            Row(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: (progress?.revealPercentage ?? 0) / 100,
                      minHeight: 10,
                      backgroundColor: KiwiColors.kiwiPrimaryLight,
                      valueColor: const AlwaysStoppedAnimation<Color>(
                        KiwiColors.xpPurple,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  '$revealPct revealed',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textMid,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Text(
                  'Tap to open  \u{27A1}',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.kiwiPrimary.withOpacity(0.8),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 6. Invite Code
  // ---------------------------------------------------------------------------

  Widget _buildInviteCode() {
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            '\u{1F4E8} Invite Friends',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              // Code display
              Expanded(
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: KiwiColors.kiwiPrimaryLight,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: KiwiColors.kiwiPrimary.withOpacity(0.3),
                    ),
                  ),
                  child: Text(
                    clan.inviteCode ?? '',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 2,
                      color: KiwiColors.kiwiPrimaryDark,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              // Copy button
              Material(
                color: KiwiColors.kiwiPrimary,
                borderRadius: BorderRadius.circular(12),
                child: InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () {
                    if (clan.inviteCode != null) {
                      Clipboard.setData(
                        ClipboardData(text: clan.inviteCode!),
                      );
                    }
                    onCopyInviteCode?.call();
                  },
                  child: const Padding(
                    padding: EdgeInsets.all(12),
                    child: Icon(
                      Icons.copy_rounded,
                      color: Colors.white,
                      size: 22,
                    ),
                  ),
                ),
              ),
            ],
          ),
          if (clan.inviteExpiresAt != null) ...[
            const SizedBox(height: 8),
            Text(
              'Expires: ${clan.inviteExpiresAt}',
              style: const TextStyle(
                fontSize: 11,
                color: KiwiColors.textMuted,
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 7. Quick Actions
  // ---------------------------------------------------------------------------

  Widget _buildQuickActions(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _actionButton(
            icon: Icons.leaderboard_rounded,
            label: 'Leaderboard',
            color: KiwiColors.kiwiPrimary,
            onTap: onOpenLeaderboard,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _actionButton(
            icon: Icons.exit_to_app_rounded,
            label: 'Leave Clan',
            color: Colors.redAccent,
            onTap: () => _confirmLeaveClan(context),
          ),
        ),
      ],
    );
  }

  Widget _actionButton({
    required IconData icon,
    required String label,
    required Color color,
    VoidCallback? onTap,
  }) {
    return Material(
      color: KiwiColors.cardBg,
      borderRadius: BorderRadius.circular(14),
      elevation: 1,
      shadowColor: Colors.black12,
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Column(
            children: [
              Icon(icon, color: color, size: 26),
              const SizedBox(height: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: color,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _confirmLeaveClan(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Leave Clan?',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
        content: Text(
          'Are you sure you want to leave ${clan.name}? '
          'You can rejoin later with an invite code.',
          style: const TextStyle(color: KiwiColors.textMid),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text(
              'Stay',
              style: TextStyle(
                color: KiwiColors.kiwiPrimary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              onLeaveClan?.call();
            },
            child: const Text(
              'Leave',
              style: TextStyle(
                color: Colors.redAccent,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Shared card wrapper
  // ---------------------------------------------------------------------------

  Widget _card({required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: child,
    );
  }
}
