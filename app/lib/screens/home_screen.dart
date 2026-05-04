import 'package:flutter/material.dart';
import '../models/question_v2.dart';
import '../models/student_levels.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';
import '../models/companion.dart';

/// Home Screen v7.0 — Kiwimath orange + cream, play-first.
///
/// Architecture: Pure adaptive engine IS the primary experience.
/// No curriculum gating. Kiwi brand identity.
///
/// Layout (top → bottom):
///   1. Top bar: avatar · name · grade · gentle practice-days
///   2. SMART PRACTICE HERO — compact, with play button
///   3. Daily progress (gentle framing)
///   4. Topic list — always shows adaptive topics
///   5. Badge milestone
class HomeScreen extends StatelessWidget {
  final int streak;
  final int kiwiCoins;
  final int masteryGems;
  final int xp;
  final int dailyProgress;
  final int dailyGoal;
  final void Function(String topicId, String topicName) onTopicTap;
  final VoidCallback onSignOut;
  final int selectedGrade;
  final void Function(int grade)? onGradeChanged;
  final List<TopicV2>? topicsV2;
  final bool topicsV2Loading;
  final CompanionService? companionService;
  final StudentLevels? studentLevels;
  final VoidCallback? onOpenLearningPath;
  final VoidCallback? onOpenParentDashboard;
  final VoidCallback? onRestartOnboarding;
  final Map<String, dynamic>? masteryOverview;
  final Set<String> lockedTopics;
  final void Function(String topicId, String topicName)? onTopicUnlock;
  final VoidCallback? onSmartSession;
  final VoidCallback? onAvatarTap;
  final String studentName;

  const HomeScreen({
    super.key,
    required this.streak,
    required this.kiwiCoins,
    required this.masteryGems,
    required this.xp,
    required this.dailyProgress,
    required this.dailyGoal,
    required this.onTopicTap,
    required this.onSignOut,
    this.selectedGrade = 1,
    this.onGradeChanged,
    this.topicsV2,
    this.topicsV2Loading = false,
    this.companionService,
    this.studentLevels,
    this.onOpenLearningPath,
    this.onOpenParentDashboard,
    this.onRestartOnboarding,
    this.masteryOverview,
    this.lockedTopics = const {},
    this.onTopicUnlock,
    this.onSmartSession,
    this.onAvatarTap,
    this.studentName = 'Chikoo',
  });

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  /// Orange gradient — Kiwimath brand.
  static const _greenStart = Color(0xFFFF6D00);
  static const _greenEnd = Color(0xFFE65100);

  /// Level color tiers.
  static const _greenBorder = Color(0xFFFF6D00);
  static const _greenBg = Color(0xFFFFF3E0);
  static const _blueBorder = Color(0xFF1E88E5);
  static const _blueBg = Color(0xFFE3F2FD);
  static const _purpleBorder = Color(0xFF8E24AA);
  static const _purpleBg = Color(0xFFF3E5F5);

  /// Badge milestones — every 50 questions.
  static const _badgeMilestones = <int, String>{
    50: 'Explorer',
    100: 'Adventurer',
    150: 'Champion',
    200: 'Master',
    250: 'Legend',
    300: 'Grandmaster',
  };

  /// Topic emoji map.
  static const _topicEmojis = <String, String>{
    'count': '\u{1F522}',
    'number': '\u{1F522}',
    'arithmetic': '\u{2795}',
    'add': '\u{2795}',
    'subtract': '\u{2795}',
    'pattern': '\u{1F504}',
    'logic': '\u{1F9E9}',
    'puzzle': '\u{1F9E9}',
    'shape': '\u{1F4D0}',
    'geo': '\u{1F4D0}',
    'spatial': '\u{1F9E0}',
    '3d': '\u{1F9E0}',
    'word': '\u{1F4D6}',
    'story': '\u{1F4D6}',
    'data': '\u{1F4CA}',
    'graph': '\u{1F4CA}',
    'place_value': '\u{1F522}',
    'multipli': '\u{2716}\u{FE0F}',
    'times': '\u{2716}\u{FE0F}',
    'divis': '\u{2797}',
    'fraction': '\u{1F967}',
    'decimal': '\u{1F522}',
    'time': '\u{1F550}',
    'clock': '\u{1F550}',
    'money': '\u{1F4B0}',
    'measur': '\u{1F4CF}',
  };

  /// Topic background colors.
  static const _topicIconBgs = <String, Color>{
    'count': Color(0xFFE3F2FD),
    'number': Color(0xFFE3F2FD),
    'arithmetic': Color(0xFFFFF3E0),
    'add': Color(0xFFFFF3E0),
    'subtract': Color(0xFFFFF3E0),
    'pattern': Color(0xFFFFF8E1),
    'logic': Color(0xFFF3E5F5),
    'puzzle': Color(0xFFF3E5F5),
    'shape': Color(0xFFE8F5E9),
    'geo': Color(0xFFE8F5E9),
    'spatial': Color(0xFFFCE4EC),
    '3d': Color(0xFFFCE4EC),
    'word': Color(0xFFE8EAF6),
    'story': Color(0xFFE8EAF6),
    'data': Color(0xFFE1F5FE),
    'graph': Color(0xFFE1F5FE),
    'measur': Color(0xFFE0F2F1),
  };

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  String _emojiForTopic(TopicV2 topic) {
    final lower = topic.topicName.toLowerCase();
    final cid = topic.topicId.toLowerCase();
    for (final entry in _topicEmojis.entries) {
      if (lower.contains(entry.key) || cid.contains(entry.key)) {
        return entry.value;
      }
    }
    return '\u{1F4D8}';
  }

  Color _iconBgForTopic(TopicV2 topic) {
    final lower = topic.topicName.toLowerCase();
    final cid = topic.topicId.toLowerCase();
    for (final entry in _topicIconBgs.entries) {
      if (lower.contains(entry.key) || cid.contains(entry.key)) {
        return entry.value;
      }
    }
    return const Color(0xFFF5F5F5);
  }

  (Color, Color) _levelColors(int level) {
    if (level <= 3) return (_greenBorder, _greenBg);
    if (level <= 6) return (_blueBorder, _blueBg);
    return (_purpleBorder, _purpleBg);
  }

  String _levelName(int level) {
    const names = [
      'Starter', 'Beginner', 'Explorer', 'Adventurer', 'Navigator',
      'Trailblazer', 'Champion', 'Master', 'Legend', 'Grandmaster',
    ];
    return names[(level - 1).clamp(0, 9)];
  }

  int get _totalQuestionsAnswered => (xp / 10).round();

  (int, int, String) get _badgeProgress {
    final total = _totalQuestionsAnswered;
    for (final entry in _badgeMilestones.entries) {
      if (total < entry.key) {
        return (total, entry.key, entry.value);
      }
    }
    final nextTarget = ((total ~/ 50) + 1) * 50;
    return (total, nextTarget, 'Grandmaster+');
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(selectedGrade);
    return Scaffold(
      backgroundColor: tier.colors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 10),
              _buildTopBar(context, tier),
              const SizedBox(height: 16),
              _buildAdaptiveHero(tier),
              const SizedBox(height: 14),
              _buildDailyProgress(tier),
              const SizedBox(height: 14),
              _buildBadgeMilestone(tier),
              const SizedBox(height: 16),
              _buildTopicSectionHeader(tier),
              const SizedBox(height: 8),
              _buildTopicList(context, tier),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 1. TOP BAR
  // ---------------------------------------------------------------------------

  Widget _buildTopBar(BuildContext context, KiwiTier tier) {
    final name = studentName.isNotEmpty ? studentName : 'Kiwi Learner';
    return Row(
      children: [
        GestureDetector(
          onTap: onAvatarTap,
          child: Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [_greenStart, _greenEnd],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
            ),
            child: companionService != null && companionService!.isLoaded
                ? ClipOval(
                    child: CompanionView(
                      surface: CompanionSurface.homeAdventure,
                      config: companionService!.config!,
                      size: 36,
                    ),
                  )
                : Center(
                    child: Text(
                      name.isNotEmpty ? name[0].toUpperCase() : 'K',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                  ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hi, $name!',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: tier.colors.textPrimary,
                ),
              ),
              Text(
                'Grade $selectedGrade',
                style: TextStyle(
                  fontSize: 11,
                  color: tier.colors.textMuted,
                ),
              ),
            ],
          ),
        ),
        // Currency badges
        _buildCurrencyChip('\u{1FA99}', '$kiwiCoins', tier),
        const SizedBox(width: 6),
        // Streak badge
        if (streak > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: KiwiColors.kiwiPrimaryLight,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('\u{1F525}', style: TextStyle(fontSize: 12)),
                const SizedBox(width: 3),
                Text(
                  '$streak',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.kiwiPrimaryDark,
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildCurrencyChip(String emoji, String value, KiwiTier tier) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey.withOpacity(0.12)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 11)),
          const SizedBox(width: 3),
          Text(
            value,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: tier.colors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 2. ADAPTIVE PRACTICE HERO — large, dominant, THE primary CTA
  // ---------------------------------------------------------------------------

  Widget _buildAdaptiveHero(KiwiTier tier) {
    return GestureDetector(
      onTap: onSmartSession,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [_greenStart, _greenEnd],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: _greenStart.withOpacity(0.3),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Row(
          children: [
            // Companion or icon
            if (companionService != null && companionService!.isLoaded)
              CompanionView(
                surface: CompanionSurface.homeAdventure,
                config: companionService!.config!,
                size: 52,
              )
            else
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Center(
                  child: Text('\u{1F9E0}', style: TextStyle(fontSize: 28)),
                ),
              ),
            const SizedBox(width: 16),
            // Text
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'SMART PRACTICE',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                      color: Colors.white.withOpacity(0.8),
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Smart Practice',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Adaptive questions at your level',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.white.withOpacity(0.75),
                    ),
                  ),
                ],
              ),
            ),
            // Play button
            Container(
              width: 48,
              height: 48,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Padding(
                  padding: EdgeInsets.only(left: 3),
                  child: Icon(
                    Icons.play_arrow_rounded,
                    size: 30,
                    color: _greenStart,
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
  // 3. DAILY PROGRESS RING
  // ---------------------------------------------------------------------------

  Widget _buildDailyProgress(KiwiTier tier) {
    final progress = dailyGoal > 0
        ? (dailyProgress / dailyGoal).clamp(0.0, 1.0)
        : 0.0;
    final remaining = (dailyGoal - dailyProgress).clamp(0, dailyGoal);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.grey.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          // Mini progress ring
          SizedBox(
            width: 36,
            height: 36,
            child: Stack(
              children: [
                CircularProgressIndicator(
                  value: progress,
                  strokeWidth: 4,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: const AlwaysStoppedAnimation<Color>(_greenStart),
                ),
                Center(
                  child: Text(
                    '\u{1F3AF}',
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  remaining > 0
                      ? '$remaining more to hit today\'s goal!'
                      : 'Daily goal complete!',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: tier.colors.textPrimary,
                  ),
                ),
                Text(
                  '$dailyProgress / $dailyGoal questions',
                  style: TextStyle(
                    fontSize: 10,
                    color: tier.colors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 4. BADGE MILESTONE
  // ---------------------------------------------------------------------------

  Widget _buildBadgeMilestone(KiwiTier tier) {
    final (current, target, badgeName) = _badgeProgress;
    final progress = target > 0 ? (current / target).clamp(0.0, 1.0) : 0.0;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFFFD54F).withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFFFFD54F), Color(0xFFFFB300)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
            ),
            child: const Center(
              child: Text('\u{2B50}', style: TextStyle(fontSize: 12)),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '$badgeName Badge',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: tier.colors.textPrimary,
                      ),
                    ),
                    Text(
                      '$current/$target',
                      style: TextStyle(
                        fontSize: 10,
                        color: tier.colors.textMuted,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                ClipRRect(
                  borderRadius: BorderRadius.circular(2),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 4,
                    backgroundColor: tier.colors.background,
                    valueColor: const AlwaysStoppedAnimation<Color>(
                      Color(0xFFFFB300),
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

  // ---------------------------------------------------------------------------
  // 5. TOPIC LIST — always adaptive topics, never chapters
  // ---------------------------------------------------------------------------

  Widget _buildTopicSectionHeader(KiwiTier tier) {
    return Row(
      children: [
        Text(
          'TOPICS',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8,
            color: tier.colors.textMuted,
          ),
        ),
        if (topicsV2Loading) ...[
          const SizedBox(width: 8),
          SizedBox(
            width: 12,
            height: 12,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: tier.colors.textMuted,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildTopicList(BuildContext context, KiwiTier tier) {
    if (topicsV2Loading && (topicsV2 == null || topicsV2!.isEmpty)) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (topicsV2 == null || topicsV2!.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: tier.colors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.withOpacity(0.15)),
        ),
        child: Text(
          'No topics available yet. Check your connection.',
          style: TextStyle(fontSize: 12, color: tier.colors.textMuted),
        ),
      );
    }

    return Column(
      children: topicsV2!.asMap().entries.map((entry) {
        final topic = entry.value;
        return Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: _buildTopicRow(context, topic, tier),
        );
      }).toList(),
    );
  }

  Widget _buildTopicRow(BuildContext context, TopicV2 topic, KiwiTier tier) {
    final isLocked = lockedTopics.contains(topic.topicId);
    final topicLevels = studentLevels?.forTopic(topic.topicId);
    final currentLv = topicLevels?.currentLevel ?? 1;
    final levelName = _levelName(currentLv);
    final (borderColor, bgColor) = _levelColors(currentLv);
    final emoji = _emojiForTopic(topic);
    final iconBg = _iconBgForTopic(topic);

    return GestureDetector(
      onTap: isLocked
          ? () => _showUnlockDialog(context, topic)
          : () => onTopicTap(topic.topicId, topic.topicName),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: tier.colors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isLocked
                ? Colors.grey.withOpacity(0.12)
                : borderColor.withOpacity(0.12),
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                color: isLocked ? Colors.grey.shade100 : iconBg,
                borderRadius: BorderRadius.circular(8),
              ),
              alignment: Alignment.center,
              child: Text(
                isLocked ? '\u{1F512}' : emoji,
                style: const TextStyle(fontSize: 14),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    topic.topicName,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isLocked
                          ? tier.colors.textMuted
                          : tier.colors.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 1),
                  Text(
                    isLocked ? 'Locked' : 'Level $currentLv · $levelName',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w500,
                      color: tier.colors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            if (!isLocked)
              Container(
                width: 26,
                height: 26,
                decoration: BoxDecoration(
                  color: bgColor,
                  shape: BoxShape.circle,
                  border: Border.all(color: borderColor, width: 1.5),
                ),
                alignment: Alignment.center,
                child: Text(
                  '$currentLv',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: borderColor,
                  ),
                ),
              ),
            if (isLocked)
              Icon(
                Icons.lock_rounded,
                size: 18,
                color: Colors.grey.shade400,
              ),
          ],
        ),
      ),
    );
  }

  void _showUnlockDialog(BuildContext context, TopicV2 topic) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Unlock Topic'),
        content: Text(
          'Would you like to unlock "${topic.topicName}"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Not now'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              onTopicUnlock?.call(topic.topicId, topic.topicName);
            },
            child: const Text('Unlock'),
          ),
        ],
      ),
    );
  }
}
