import 'dart:async';

import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';
import '../models/clan.dart';
import '../models/engagement.dart';
import '../widgets/squad_activity_bar.dart';
import '../widgets/streak_fire_widget.dart';

/// Main clan hub — redesigned with full engagement loops.
///
/// Sections: Header, Daily Puzzle, Streak & Rewards Row, Daily Reward Calendar,
/// League Badge, Clan Wars, Pledge, Squad Activity, Picture Unravel,
/// Quick Actions.
class ClanHubScreen extends StatefulWidget {
  final Clan clan;
  final ChallengeInfo? activeChallenge;
  final ChallengeProgress? challengeProgress;
  final List<DailySquadMember> squadMembers;

  // Engagement props
  final DailyPuzzle? dailyPuzzle;
  final StreakData? streakData;
  final LeagueStatus? leagueStatus;
  final ClanWar? clanWar;
  final RewardData? rewardData;
  final Pledge? activePledge;

  // Callbacks
  final VoidCallback? onOpenChallenge;
  final VoidCallback? onOpenLeaderboard;
  final VoidCallback? onLeaveClan;
  final VoidCallback? onCopyInviteCode;
  final VoidCallback? onSolveDailyPuzzle;
  final VoidCallback? onClaimDailyReward;
  final VoidCallback? onOpenMysteryBox;
  final VoidCallback? onOpenRewards;
  final VoidCallback? onOpenClanWar;
  final VoidCallback? onMakePledge;

  const ClanHubScreen({
    super.key,
    required this.clan,
    this.activeChallenge,
    this.challengeProgress,
    this.squadMembers = const [],
    this.dailyPuzzle,
    this.streakData,
    this.leagueStatus,
    this.clanWar,
    this.rewardData,
    this.activePledge,
    this.onOpenChallenge,
    this.onOpenLeaderboard,
    this.onLeaveClan,
    this.onCopyInviteCode,
    this.onSolveDailyPuzzle,
    this.onClaimDailyReward,
    this.onOpenMysteryBox,
    this.onOpenRewards,
    this.onOpenClanWar,
    this.onMakePledge,
  });

  @override
  State<ClanHubScreen> createState() => _ClanHubScreenState();
}

class _ClanHubScreenState extends State<ClanHubScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  Timer? _countdownTimer;
  Duration _countdown = Duration.zero;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _startCountdownTimer();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _countdownTimer?.cancel();
    super.dispose();
  }

  void _startCountdownTimer() {
    _updateCountdown();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      _updateCountdown();
    });
  }

  void _updateCountdown() {
    final puzzle = widget.dailyPuzzle;
    if (puzzle != null && !puzzle.isActive) {
      // Parse dropsAt time
      final now = DateTime.now();
      final dropTime = DateTime.tryParse(puzzle.dropsAt);
      if (dropTime != null && dropTime.isAfter(now)) {
        setState(() {
          _countdown = dropTime.difference(now);
        });
        return;
      }
    }
    setState(() {
      _countdown = Duration.zero;
    });
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  String _formatNumber(int n) {
    if (n >= 1000) {
      final thousands = n ~/ 1000;
      final remainder = (n % 1000) ~/ 100;
      return remainder > 0
          ? '$thousands,${(n % 1000).toString().padLeft(3, '0')}'
          : '${thousands},000';
    }
    return n.toString();
  }

  String _formatCountdown(Duration d) {
    final hours = d.inHours;
    final minutes = d.inMinutes.remainder(60);
    final seconds = d.inSeconds.remainder(60);
    return '${hours.toString().padLeft(2, '0')}:'
        '${minutes.toString().padLeft(2, '0')}:'
        '${seconds.toString().padLeft(2, '0')}';
  }

  String _leagueEmoji(String league) {
    switch (league.toLowerCase()) {
      case 'bronze':
        return '\u{1F949}';
      case 'silver':
        return '\u{1F948}';
      case 'gold':
        return '\u{1F947}';
      case 'platinum':
        return '\u{1F48E}';
      case 'diamond':
        return '\u{2B50}';
      default:
        return '\u{1F3C6}';
    }
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
          // 1. Header (unchanged orange gradient)
          _buildHeader(context),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),

                  // 2. Daily Puzzle Card
                  if (widget.dailyPuzzle != null) ...[
                    _buildDailyPuzzleCard(),
                    const SizedBox(height: 16),
                  ],

                  // 3. Streak & Rewards Row
                  if (widget.streakData != null || widget.rewardData != null) ...[
                    _buildStreakRewardsRow(),
                    const SizedBox(height: 16),
                  ],

                  // 4. Daily Reward Calendar
                  if (widget.rewardData != null &&
                      widget.rewardData!.dailyCalendar.isNotEmpty) ...[
                    _buildDailyRewardCalendar(),
                    const SizedBox(height: 16),
                  ],

                  // 5. League Badge
                  if (widget.leagueStatus != null) ...[
                    _buildLeagueBadge(),
                    const SizedBox(height: 16),
                  ],

                  // 6. Clan Wars Section
                  _buildClanWarsSection(),
                  const SizedBox(height: 16),

                  // 7. Pledge Widget
                  _buildPledgeWidget(),
                  const SizedBox(height: 16),

                  // 8. Squad Activity
                  _buildSquadActivity(),
                  const SizedBox(height: 16),

                  // 9. Picture Unravel
                  if (widget.activeChallenge != null) ...[
                    _buildChallengePreview(),
                    const SizedBox(height: 16),
                  ],

                  // 10. Quick Actions
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
  // 1. Header — orange gradient with clan identity (unchanged)
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
                  Row(
                    children: [
                      Container(
                        width: 52,
                        height: 52,
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.25),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          widget.clan.crest.emoji,
                          style: const TextStyle(fontSize: 28),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.clan.name,
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
                                    '${widget.clan.clanLevel.emoji} ${widget.clan.clanLevel.name}',
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.white,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Row(
                                  children: [
                                    const Icon(
                                      Icons.people_alt_rounded,
                                      size: 16,
                                      color: Colors.white70,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      '${widget.clan.memberCount} members',
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
  // 2. Daily Puzzle Card
  // ---------------------------------------------------------------------------

  Widget _buildDailyPuzzleCard() {
    final puzzle = widget.dailyPuzzle!;
    final isLive = puzzle.isActive;

    return GestureDetector(
      onTap: isLive ? widget.onSolveDailyPuzzle : null,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isLive
                ? [const Color(0xFFFF6D00), const Color(0xFFFF9100)]
                : [const Color(0xFF455A64), const Color(0xFF607D8B)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: (isLive ? KiwiColors.kiwiPrimary : Colors.grey)
                  .withOpacity(0.3),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top row: title + live badge
            Row(
              children: [
                const Text(
                  '\u{1F9E9}',
                  style: TextStyle(fontSize: 24),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Puzzle of the Day',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: Colors.white.withOpacity(0.95),
                    ),
                  ),
                ),
                if (isLive)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.25),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AnimatedBuilder(
                          animation: _pulseController,
                          builder: (_, __) => Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: Colors.greenAccent
                                  .withOpacity(0.5 + _pulseController.value * 0.5),
                            ),
                          ),
                        ),
                        const SizedBox(width: 5),
                        const Text(
                          'LIVE NOW',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),

            // Title
            Text(
              puzzle.title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w900,
                color: Colors.white,
              ),
            ),
            const SizedBox(height: 6),

            // Story snippet
            Text(
              puzzle.storyNarrative,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 14,
                color: Colors.white.withOpacity(0.85),
                height: 1.4,
              ),
            ),
            const SizedBox(height: 14),

            // Countdown or streak row
            Row(
              children: [
                if (!isLive) ...[
                  const Icon(
                    Icons.access_time_rounded,
                    size: 18,
                    color: Colors.white70,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    _countdown.inSeconds > 0
                        ? _formatCountdown(_countdown)
                        : 'Coming at 4 PM',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: Colors.white70,
                    ),
                  ),
                ],
                if (isLive && widget.streakData != null) ...[
                  const Text(
                    '\u{1F525}',
                    style: TextStyle(fontSize: 18),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'x ${widget.streakData!.currentStreak}',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ],
                const Spacer(),
                Text(
                  'Earn up to 1,000 IPS',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Colors.white.withOpacity(0.8),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // CTA button
            SizedBox(
              width: double.infinity,
              child: Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                child: InkWell(
                  borderRadius: BorderRadius.circular(14),
                  onTap: isLive ? widget.onSolveDailyPuzzle : null,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    child: Center(
                      child: Text(
                        isLive ? 'Solve Now  \u{27A1}' : 'Coming at 4 PM  \u{23F0}',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                          color: isLive
                              ? KiwiColors.kiwiPrimary
                              : KiwiColors.textMuted,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 3. Streak & Rewards Row
  // ---------------------------------------------------------------------------

  Widget _buildStreakRewardsRow() {
    final streak = widget.streakData;
    final rewards = widget.rewardData;
    final grade = widget.clan.grade;

    return SizedBox(
      height: 100,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          // Streak flame widget
          if (streak != null)
            _streakRewardTile(
              child: StreakFireWidget(
                streakCount: streak.currentStreak,
                tierName: streak.streakTier ?? 'Starter',
                compact: true,
                showFreezeButton: false,
              ),
            ),
          if (streak != null) const SizedBox(width: 10),

          // Gems count
          if (rewards != null)
            _streakRewardTile(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('\u{1F48E}', style: TextStyle(fontSize: 28)),
                  const SizedBox(height: 4),
                  Text(
                    _formatNumber(rewards.totalGems),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.gemBlue,
                    ),
                  ),
                  const Text(
                    'Gems',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: KiwiColors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
          if (rewards != null) const SizedBox(width: 10),

          // Mystery box (G3+)
          if (grade >= 3 && rewards != null && rewards.mysteryBoxesAvailable > 0)
            GestureDetector(
              onTap: widget.onOpenMysteryBox,
              child: _streakRewardTile(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('\u{1F381}', style: TextStyle(fontSize: 28)),
                    const SizedBox(height: 4),
                    Text(
                      'x${rewards.mysteryBoxesAvailable}',
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: KiwiColors.coral,
                      ),
                    ),
                    const Text(
                      'Mystery',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: KiwiColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ),

          // Sticker album progress (G1-2)
          if (grade <= 2 && rewards != null)
            _streakRewardTile(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('\u{1F4D6}', style: TextStyle(fontSize: 28)),
                  const SizedBox(height: 4),
                  Text(
                    '${(rewards.stickerAlbumProgress * 30).round()}/30',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.xpPurple,
                    ),
                  ),
                  const Text(
                    'Stickers',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
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

  Widget _streakRewardTile({required Widget child}) {
    return Container(
      width: 100,
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: child,
    );
  }

  // ---------------------------------------------------------------------------
  // 4. Daily Reward Calendar (7-day strip)
  // ---------------------------------------------------------------------------

  Widget _buildDailyRewardCalendar() {
    final calendar = widget.rewardData!.dailyCalendar;
    final canClaim = widget.rewardData!.dailyCalendar.any(
      (d) => d['is_today'] == true && d['claimed'] != true,
    );

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                '\u{1F4C5} Daily Rewards',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.textDark,
                ),
              ),
              const Spacer(),
              if (canClaim)
                GestureDetector(
                  onTap: widget.onClaimDailyReward,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      'Claim!',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 72,
            child: Row(
              children: [
                for (int i = 0; i < calendar.length && i < 7; i++) ...[
                  if (i > 0) const SizedBox(width: 6),
                  Expanded(child: _buildDayCircle(calendar[i], i + 1)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDayCircle(Map<String, dynamic> day, int dayNum) {
    final claimed = day['claimed'] == true;
    final isToday = day['is_today'] == true;
    final isFuture = day['is_future'] == true;
    final emoji = day['reward_emoji'] as String? ?? '\u{1F48E}';

    Color bgColor;
    Color borderColor;
    double opacity;

    if (claimed) {
      bgColor = KiwiColors.kiwiGreenLight;
      borderColor = KiwiColors.kiwiGreen;
      opacity = 1.0;
    } else if (isToday) {
      bgColor = KiwiColors.kiwiPrimaryLight;
      borderColor = KiwiColors.kiwiPrimary;
      opacity = 1.0;
    } else if (isFuture) {
      bgColor = KiwiColors.creamDark;
      borderColor = Colors.transparent;
      opacity = 0.4;
    } else {
      bgColor = KiwiColors.cardBg;
      borderColor = Colors.grey.shade300;
      opacity = 0.6;
    }

    return Opacity(
      opacity: opacity,
      child: Column(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: bgColor,
              border: Border.all(color: borderColor, width: isToday ? 2.5 : 1.5),
            ),
            alignment: Alignment.center,
            child: claimed
                ? const Icon(Icons.check_rounded, size: 20, color: KiwiColors.kiwiGreen)
                : Text(emoji, style: const TextStyle(fontSize: 18)),
          ),
          const SizedBox(height: 4),
          Text(
            'D$dayNum',
            style: TextStyle(
              fontSize: 10,
              fontWeight: isToday ? FontWeight.w800 : FontWeight.w600,
              color: isToday ? KiwiColors.kiwiPrimary : KiwiColors.textMuted,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 5. League Badge
  // ---------------------------------------------------------------------------

  Widget _buildLeagueBadge() {
    final league = widget.leagueStatus!;
    final progress = league.promotionThreshold > 0
        ? (league.leaguePoints / league.promotionThreshold).clamp(0.0, 1.0)
        : 0.0;

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                _leagueEmoji(league.league),
                style: const TextStyle(fontSize: 28),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${league.league[0].toUpperCase()}${league.league.substring(1)} League',
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                        color: KiwiColors.textDark,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      '#${league.rankInLeague} in ${league.league[0].toUpperCase()}${league.league.substring(1)} League',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: KiwiColors.textMid,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: KiwiColors.leagueBlue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  'S${league.seasonNumber}',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.leagueBlue,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 12,
              backgroundColor: KiwiColors.leagueBlue.withOpacity(0.12),
              valueColor: const AlwaysStoppedAnimation<Color>(KiwiColors.leagueBlue),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${_formatNumber(league.leaguePoints)} / ${_formatNumber(league.promotionThreshold)} pts',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textMid,
                ),
              ),
              Text(
                'Season ends: ${league.seasonEndsAt}',
                style: const TextStyle(
                  fontSize: 11,
                  color: KiwiColors.textMuted,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 6. Clan Wars Section
  // ---------------------------------------------------------------------------

  Widget _buildClanWarsSection() {
    final war = widget.clanWar;

    if (war == null || war.status == 'upcoming') {
      return _card(
        child: Column(
          children: [
            const Text(
              '\u{2694}\u{FE0F}',
              style: TextStyle(fontSize: 32),
            ),
            const SizedBox(height: 8),
            const Text(
              'Clan Wars',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              war?.startTime.isNotEmpty == true
                  ? 'Next war starts ${war!.startTime}'
                  : 'Next war starts Monday',
              style: const TextStyle(
                fontSize: 13,
                color: KiwiColors.textMid,
              ),
            ),
          ],
        ),
      );
    }

    // Active war
    final opponentName =
        war.opponentClan['name'] as String? ?? 'Opponent';
    final opponentEmoji =
        war.opponentClan['crest_emoji'] as String? ?? '\u{2694}\u{FE0F}';
    final isLosing = war.theirScore > war.ourScore;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFD32F2F), Color(0xFFB71C1C)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.red.withOpacity(0.3),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        children: [
          // Header with pulsing dot
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AnimatedBuilder(
                animation: _pulseController,
                builder: (_, __) => Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.redAccent
                        .withOpacity(0.5 + _pulseController.value * 0.5),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                '\u{2694}\u{FE0F} CLAN WAR',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                  letterSpacing: 1.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // VS matchup
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              // Our clan
              Column(
                children: [
                  Text(
                    widget.clan.crest.emoji,
                    style: const TextStyle(fontSize: 36),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.clan.name,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),

              // Score
              Column(
                children: [
                  Text(
                    '${_formatNumber(war.ourScore)}',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                    ),
                  ),
                  const Text(
                    'vs',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: Colors.white60,
                    ),
                  ),
                  Text(
                    _formatNumber(war.theirScore),
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),

              // Opponent
              Column(
                children: [
                  Text(
                    opponentEmoji,
                    style: const TextStyle(fontSize: 36),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    opponentName,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Comeback boost
          if (isLosing && war.comebackBoost > 1.0) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '\u{1F680} ${war.comebackBoost}x UNDERDOG BOOST!',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                  color: Colors.amberAccent,
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],

          // Battle Now button
          SizedBox(
            width: double.infinity,
            child: Material(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: widget.onOpenClanWar,
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 14),
                  child: Center(
                    child: Text(
                      'Battle Now  \u{2694}\u{FE0F}',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFFD32F2F),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 7. Pledge Widget
  // ---------------------------------------------------------------------------

  Widget _buildPledgeWidget() {
    final pledge = widget.activePledge;

    if (pledge == null || !pledge.active) {
      return GestureDetector(
        onTap: widget.onMakePledge,
        child: _card(
          child: Row(
            children: [
              const Text('\u{1F91D}', style: TextStyle(fontSize: 28)),
              const SizedBox(width: 12),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Make a Pledge',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: KiwiColors.textDark,
                      ),
                    ),
                    SizedBox(height: 2),
                    Text(
                      'Commit to a daily goal and earn bonus rewards!',
                      style: TextStyle(
                        fontSize: 12,
                        color: KiwiColors.textMid,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.arrow_forward_ios_rounded,
                size: 16,
                color: KiwiColors.textMuted,
              ),
            ],
          ),
        ),
      );
    }

    final dayProgress =
        pledge.durationDays > 0 ? (pledge.currentPuzzles / (pledge.targetPuzzles * pledge.durationDays)).clamp(0.0, 1.0) : 0.0;

    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('\u{1F91D}', style: TextStyle(fontSize: 22)),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'My Pledge',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiGreenLight,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'Active',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.kiwiGreenDark,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            '${pledge.targetPuzzles} puzzles/day for ${pledge.durationDays} days',
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: KiwiColors.textMid,
            ),
          ),
          const SizedBox(height: 10),

          // Overall progress
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: dayProgress,
                    minHeight: 10,
                    backgroundColor: KiwiColors.kiwiPrimaryLight,
                    valueColor:
                        const AlwaysStoppedAnimation<Color>(KiwiColors.kiwiPrimary),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                '${pledge.currentPuzzles}/${pledge.targetPuzzles * pledge.durationDays}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textMid,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 8. Squad Activity (enhanced with "We miss you!")
  // ---------------------------------------------------------------------------

  Widget _buildSquadActivity() {
    final inactiveMembers = widget.squadMembers
        .where((m) => !m.practicedToday)
        .toList();
    final hasInactive = inactiveMembers.isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              "Today's Squad",
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            if (hasInactive) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: KiwiColors.wrongBg,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  'We miss ${inactiveMembers.length}!',
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.coral,
                  ),
                ),
              ),
            ],
          ],
        ),
        const SizedBox(height: 10),
        widget.squadMembers.isNotEmpty
            ? SquadActivityBar(members: widget.squadMembers)
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
  // 9. Active Challenge Preview (Picture Unravel)
  // ---------------------------------------------------------------------------

  Widget _buildChallengePreview() {
    final challenge = widget.activeChallenge!;
    final progress = widget.challengeProgress;
    final revealPct = progress != null
        ? '${progress.revealPercentage.toStringAsFixed(0)}%'
        : '0%';

    return GestureDetector(
      onTap: widget.onOpenChallenge,
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
  // 10. Quick Actions (Leaderboard + Leave Clan + Rewards)
  // ---------------------------------------------------------------------------

  Widget _buildQuickActions(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _actionButton(
            icon: Icons.leaderboard_rounded,
            label: 'Leaderboard',
            color: KiwiColors.kiwiPrimary,
            onTap: widget.onOpenLeaderboard,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _actionButton(
            icon: Icons.emoji_events_rounded,
            label: '\u{1F3C6} Rewards',
            color: KiwiColors.gemGold,
            onTap: widget.onOpenRewards,
          ),
        ),
        const SizedBox(width: 10),
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
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: color,
                ),
                textAlign: TextAlign.center,
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
          'Are you sure you want to leave ${widget.clan.name}? '
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
              widget.onLeaveClan?.call();
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
