import 'package:flutter/material.dart';
import '../models/question_v2.dart';
import '../models/student_levels.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';
import '../models/companion.dart';

/// Home Screen v4 — approved redesign.
///
/// Layout (top → bottom):
///   1. Compact top bar: avatar · name · grade · streak badge
///   2. Smart Practice hero (orange gradient, compact row)
///   3. Badge milestone (next badge progress)
///   4. Topic list (all 8, compact rows, colored level badges)
///
/// Removed: grade selector, journey labels, continue card, region names.
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
  final String? curriculum;
  final List<Map<String, dynamic>>? chapters;
  final bool chaptersLoading;

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
    this.curriculum,
    this.chapters,
    this.chaptersLoading = false,
  });

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  /// Vedantu orange gradient.
  static const _orangeStart = Color(0xFFFF6D00);
  static const _orangeEnd = Color(0xFFFF9100);

  /// Level color tiers.
  static const _greenBorder = Color(0xFF43A047);
  static const _greenBg = Color(0xFFE8F5E9);
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

  /// Topic emoji map for the icon squares.
  static const _topicEmojis = <String, String>{
    'count': '🔢',
    'number': '🔢',
    'arithmetic': '➕',
    'add': '➕',
    'subtract': '➕',
    'pattern': '🔄',
    'logic': '🧩',
    'puzzle': '🧩',
    'shape': '📐',
    'geo': '📐',
    'spatial': '🧠',
    '3d': '🧠',
    'word': '📖',
    'story': '📖',
    'data': '📊',
    'graph': '📊',
    'place_value': '🔢',
    'multipli': '✖️',
    'times': '✖️',
    'divis': '➗',
    'fraction': '🥧',
    'decimal': '🔢',
    'time': '🕐',
    'clock': '🕐',
    'money': '💰',
    'measur': '📏',
  };

  /// Topic background colors for the icon squares.
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

  /// Whether the user follows a chapter-based curriculum (not Olympiad).
  bool get _hasCurriculum =>
      curriculum != null &&
      curriculum!.isNotEmpty &&
      curriculum != 'olympiad';

  String _emojiForTopic(TopicV2 topic) {
    final lower = topic.topicName.toLowerCase();
    final cid = topic.topicId.toLowerCase();
    for (final entry in _topicEmojis.entries) {
      if (lower.contains(entry.key) || cid.contains(entry.key)) {
        return entry.value;
      }
    }
    return '📘';
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

  /// Returns (borderColor, bgColor) for the level badge.
  (Color, Color) _levelColors(int level) {
    if (level <= 3) return (_greenBorder, _greenBg);
    if (level <= 6) return (_blueBorder, _blueBg);
    return (_purpleBorder, _purpleBg);
  }

  /// Level name from the 10-level system.
  String _levelName(int level) {
    const names = [
      'Starter',      // 1
      'Beginner',     // 2
      'Explorer',     // 3
      'Adventurer',   // 4
      'Navigator',    // 5
      'Trailblazer',  // 6
      'Champion',     // 7
      'Master',       // 8
      'Legend',        // 9
      'Grandmaster',  // 10
    ];
    return names[(level - 1).clamp(0, 9)];
  }

  /// Compute total questions answered (approximation from XP or daily progress).
  int get _totalQuestionsAnswered {
    // Use XP as proxy: ~10 XP per question on average.
    // This is a rough estimate; the backend should provide an exact count.
    return (xp / 10).round();
  }

  /// Badge progress: (currentCount, targetCount, badgeName).
  (int, int, String) get _badgeProgress {
    final total = _totalQuestionsAnswered;
    // Find next milestone.
    for (final entry in _badgeMilestones.entries) {
      if (total < entry.key) {
        return (total, entry.key, entry.value);
      }
    }
    // Past all milestones.
    final lastKey = _badgeMilestones.keys.last;
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
              const SizedBox(height: 12),
              _buildSmartPracticeHero(tier),
              const SizedBox(height: 10),
              _buildBadgeMilestone(tier),
              const SizedBox(height: 14),
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
  // 1. TOP BAR — avatar + name + grade + streak
  // ---------------------------------------------------------------------------

  Widget _buildTopBar(BuildContext context, KiwiTier tier) {
    final name = studentName.isNotEmpty ? studentName : 'Kiwi Learner';
    return Row(
      children: [
        // Avatar (tappable → opens profile sheet)
        GestureDetector(
          onTap: onAvatarTap,
          child: Container(
            width: 36,
            height: 36,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [_orangeStart, _orangeEnd],
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
        // Name + grade
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
        // Streak badge
        if (streak > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFFFF3E0),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('🔥', style: TextStyle(fontSize: 12)),
                const SizedBox(width: 3),
                Text(
                  '$streak',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFFE65100),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // 2. SMART PRACTICE HERO — compact orange gradient row
  // ---------------------------------------------------------------------------

  Widget _buildSmartPracticeHero(KiwiTier tier) {
    return GestureDetector(
      onTap: onSmartSession,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [_orangeStart, _orangeEnd],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            BoxShadow(
              color: _orangeStart.withOpacity(0.25),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            // Text
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ADAPTIVE',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5,
                      color: Colors.white.withOpacity(0.75),
                    ),
                  ),
                  const SizedBox(height: 2),
                  const Text(
                    'Smart Practice',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Personalized to your level',
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.white.withOpacity(0.7),
                    ),
                  ),
                ],
              ),
            ),
            // Play button
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Padding(
                  padding: EdgeInsets.only(left: 2),
                  child: Icon(
                    Icons.play_arrow_rounded,
                    size: 26,
                    color: _orangeStart,
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
  // 3. BADGE MILESTONE — progress toward next badge
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
          // Star icon
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
              child: Text('⭐', style: TextStyle(fontSize: 12)),
            ),
          ),
          const SizedBox(width: 10),
          // Badge name + progress bar
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
  // 4. TOPIC LIST
  // ---------------------------------------------------------------------------

  Widget _buildTopicSectionHeader(KiwiTier tier) {
    final isLoading = _hasCurriculum ? chaptersLoading : topicsV2Loading;
    final label = _hasCurriculum ? 'CHAPTERS' : 'TOPICS';
    return Row(
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.8,
            color: tier.colors.textMuted,
          ),
        ),
        if (isLoading) ...[
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
    // Curriculum users see chapters; Olympiad users see topics
    if (_hasCurriculum) {
      return _buildChapterList(context, tier);
    }
    return _buildOlympiadTopicList(context, tier);
  }

  Widget _buildChapterList(BuildContext context, KiwiTier tier) {
    if (chaptersLoading && (chapters == null || chapters!.isEmpty)) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (chapters == null || chapters!.isEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: tier.colors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.withOpacity(0.15)),
        ),
        child: Text(
          'No chapters available yet for ${curriculum?.toUpperCase() ?? ""} Grade $selectedGrade.',
          style: TextStyle(fontSize: 12, color: tier.colors.textMuted),
        ),
      );
    }

    final chapterColors = [
      const Color(0xFF2E7D32),
      const Color(0xFF1565C0),
      const Color(0xFF6A1B9A),
      const Color(0xFFFF6D00),
      const Color(0xFFC62828),
      const Color(0xFF00838F),
      const Color(0xFF4527A0),
      const Color(0xFF2E7D32),
      const Color(0xFF1565C0),
      const Color(0xFF6A1B9A),
      const Color(0xFFFF6D00),
      const Color(0xFFC62828),
      const Color(0xFF00838F),
    ];

    return Column(
      children: chapters!.asMap().entries.map((entry) {
        final idx = entry.key;
        final ch = entry.value;
        final name = ch['name'] as String? ?? 'Chapter ${idx + 1}';
        final questionCount = ch['question_count'] as int? ?? 0;
        final accent = chapterColors[idx % chapterColors.length];

        return Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: GestureDetector(
            onTap: () => onTopicTap(ch['id'] as String? ?? '', name),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: tier.colors.cardBg,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: accent.withOpacity(0.12)),
              ),
              child: Row(
                children: [
                  // Chapter number badge
                  Container(
                    width: 30,
                    height: 30,
                    decoration: BoxDecoration(
                      color: accent.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      '${idx + 1}',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        color: accent,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  // Chapter name
                  Expanded(
                    child: Text(
                      name,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: tier.colors.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  // Question count
                  Text(
                    '$questionCount Qs',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: accent.withOpacity(0.7),
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(Icons.chevron_right_rounded,
                      size: 18, color: accent.withOpacity(0.4)),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildOlympiadTopicList(BuildContext context, KiwiTier tier) {
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
            // Topic icon
            Container(
              width: 30,
              height: 30,
              decoration: BoxDecoration(
                color: isLocked ? Colors.grey.shade100 : iconBg,
                borderRadius: BorderRadius.circular(8),
              ),
              alignment: Alignment.center,
              child: Text(
                isLocked ? '🔒' : emoji,
                style: const TextStyle(fontSize: 14),
              ),
            ),
            const SizedBox(width: 10),
            // Topic name + level
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
            // Level badge (colored circle)
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
