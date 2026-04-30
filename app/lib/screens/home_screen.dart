import 'dart:ui';

import 'package:flutter/material.dart';
import '../models/companion.dart';
import '../models/question_v2.dart';
import '../models/student_levels.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';

class HomeScreen extends StatelessWidget {
  final int streak;
  final int kiwiCoins;
  final int masteryGems;
  final int xp;
  final int dailyProgress;
  final int dailyGoal;
  final void Function(String topicId, String topicName) onTopicTap;
  final VoidCallback onSignOut;
  /// Currently selected grade (1-2). Defaults to 1.
  final int selectedGrade;
  /// Callback when user taps a grade tab.
  final void Function(int grade)? onGradeChanged;

  /// v2 topics loaded from the backend.
  final List<TopicV2>? topicsV2;
  /// Whether v2 topics are currently loading.
  final bool topicsV2Loading;
  /// Companion service for showing the companion on home screen.
  final CompanionService? companionService;

  /// Student level progression (10 levels per topic).
  final StudentLevels? studentLevels;

  /// Optional: opens the personalised Learning Path screen.
  final VoidCallback? onOpenLearningPath;

  /// Optional: opens the Parent Dashboard.
  final VoidCallback? onOpenParentDashboard;

  /// Optional: re-runs the onboarding diagnostic (for kids who want to retry,
  /// or for parents who want to recalibrate).
  final VoidCallback? onRestartOnboarding;

  /// Mastery overview data from /v2/mastery/overview for showing per-topic mastery badges.
  final Map<String, dynamic>? masteryOverview;

  /// Set of topic IDs that are currently locked for this user.
  final Set<String> lockedTopics;

  /// Callback when user confirms unlocking a locked topic.
  final void Function(String topicId, String topicName)? onTopicUnlock;

  /// Callback for starting a smart (cross-topic) practice session.
  final VoidCallback? onSmartSession;

  /// Student's display name for personalized greeting.
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
    this.studentName = 'Chikoo',
  });

  /// Grade-adaptive tier tokens.
  KiwiTier get _tier => KiwiTier.forGrade(selectedGrade);

  // ---------------------------------------------------------------------------
  // Region mapping — friendly world names for topic categories
  // ---------------------------------------------------------------------------
  static const _regionMap = <String, _Region>{
    'count':     _Region('Number Island',    '\u{1F3DD}', Color(0xFF42A5F5), Color(0xFF1E88E5)),
    'number':    _Region('Number Island',    '\u{1F3DD}', Color(0xFF42A5F5), Color(0xFF1E88E5)),
    'add':       _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'subtract':  _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'measur':    _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'arithmetic':_Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'pattern':   _Region('Pattern Cave',     '\u{1F48E}', Color(0xFFAB47BC), Color(0xFF8E24AA)),
    'logic':     _Region('Puzzle Park',      '\u{1F9E9}', Color(0xFF66BB6A), Color(0xFF2E7D32)),
    'puzzle':    _Region('Brain Beach',      '\u{1F3D6}', Color(0xFFEF5350), Color(0xFFE53935)),
    'spatial':   _Region('Space Station',    '\u{1F680}', Color(0xFF5C6BC0), Color(0xFF3949AB)),
    '3d':        _Region('Space Station',    '\u{1F680}', Color(0xFF5C6BC0), Color(0xFF3949AB)),
    'shape':     _Region('Shape Forest',     '\u{1F332}', Color(0xFF43A047), Color(0xFF2E7D32)),
    'geo':       _Region('Shape Forest',     '\u{1F332}', Color(0xFF43A047), Color(0xFF2E7D32)),
    'word':      _Region('Story Land',       '\u{1F4D6}', Color(0xFFFFCA28), Color(0xFFF9A825)),
    'story':     _Region('Story Land',       '\u{1F4D6}', Color(0xFFFFCA28), Color(0xFFF9A825)),
    'place_value':_Region('Number Island',   '\u{1F3DD}', Color(0xFF42A5F5), Color(0xFF1E88E5)),
    'multipli':  _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'times':     _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'divis':     _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'fraction':  _Region('Number Island',    '\u{1F3DD}', Color(0xFF42A5F5), Color(0xFF1E88E5)),
    'decimal':   _Region('Number Island',    '\u{1F3DD}', Color(0xFF42A5F5), Color(0xFF1E88E5)),
    'time':      _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'clock':     _Region('Measure Mountain', '\u{26F0}',  Color(0xFFFF8A65), Color(0xFFFF5722)),
    'money':     _Region('Story Land',       '\u{1F4D6}', Color(0xFFFFCA28), Color(0xFFF9A825)),
    'data':      _Region('Puzzle Park',      '\u{1F9E9}', Color(0xFF66BB6A), Color(0xFF2E7D32)),
    'graph':     _Region('Puzzle Park',      '\u{1F9E9}', Color(0xFF66BB6A), Color(0xFF2E7D32)),
  };

  static _Region _regionForTopic(TopicV2 topic) {
    final lower = topic.topicName.toLowerCase();
    final cid = topic.topicId.toLowerCase();
    for (final entry in _regionMap.entries) {
      if (lower.contains(entry.key) || cid.contains(entry.key)) {
        return entry.value;
      }
    }
    // Fallback
    return const _Region('Explore Land', '\u{1F30D}', Color(0xFF78909C), Color(0xFF546E7A));
  }

  // ---------------------------------------------------------------------------
  // Journey theme name for the selected grade
  // ---------------------------------------------------------------------------
  String get _journeyTheme {
    switch (selectedGrade) {
      case 1:
        return 'Ocean Voyage';
      case 2:
        return 'Sky Quest';
      default:
        return 'Galaxy Trek';
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = _tier;
    return Scaffold(
      backgroundColor: tier.colors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 10),
              _buildTopBar(context),
              const SizedBox(height: 16),
              _buildGreetingCard(),
              const SizedBox(height: 14),
              _buildContinueCard(),
              const SizedBox(height: 10),
              _buildSmartPracticeCard(),
              const SizedBox(height: 14),
              _buildGradeSelector(),
              const SizedBox(height: 14),
              _buildRegionChips(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 1. TOP BAR — logo + sound toggle only, profile avatar for menu
  // ---------------------------------------------------------------------------
  Widget _buildTopBar(BuildContext context) {
    final tier = _tier;
    return Row(
      children: [
        // Profile avatar — opens menu
        _buildProfileAvatar(context),
        const SizedBox(width: 10),
        // Kiwimath logo
        Text(
          tier.isJunior ? '\u{1F95D}' : '\u{1F9E0}',
          style: TextStyle(fontSize: tier.isJunior ? 22 : 18),
        ),
        const SizedBox(width: 4),
        Text(
          'Kiwimath',
          style: TextStyle(
            fontSize: tier.typography.headlineSize - 2,
            fontWeight: tier.typography.headlineWeight,
            color: tier.colors.primaryDark,
          ),
        ),
        const Spacer(),
        // Sound toggle
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: tier.colors.cardBg,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.06),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Icon(
            Icons.volume_up_rounded,
            size: 20,
            color: tier.colors.primaryDark,
          ),
        ),
      ],
    );
  }

  Widget _buildProfileAvatar(BuildContext context) {
    final tier = _tier;
    return PopupMenuButton<String>(
      tooltip: 'Profile',
      offset: const Offset(0, 44),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      onSelected: (key) {
        switch (key) {
          case 'path':
            onOpenLearningPath?.call();
            break;
          case 'parent':
            onOpenParentDashboard?.call();
            break;
          case 'redo':
            onRestartOnboarding?.call();
            break;
          case 'signout':
            onSignOut();
            break;
        }
      },
      itemBuilder: (context) => [
        if (onOpenLearningPath != null)
          PopupMenuItem(
            value: 'path',
            child: ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.alt_route_rounded, size: 20, color: tier.colors.primary),
              title: Text('Learning Path',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: tier.colors.textPrimary)),
            ),
          ),
        if (onOpenParentDashboard != null)
          PopupMenuItem(
            value: 'parent',
            child: ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.family_restroom_rounded, size: 20, color: tier.colors.primary),
              title: Text('Parent Dashboard',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: tier.colors.textPrimary)),
            ),
          ),
        if (onRestartOnboarding != null)
          PopupMenuItem(
            value: 'redo',
            child: ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.refresh_rounded, size: 20, color: tier.colors.primary),
              title: Text('Retake Test',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: tier.colors.textPrimary)),
            ),
          ),
        PopupMenuItem(
          value: 'signout',
          child: ListTile(
            dense: true,
            contentPadding: EdgeInsets.zero,
            leading: Icon(Icons.logout_rounded, size: 20, color: Colors.red.shade400),
            title: Text('Sign Out',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14, color: Colors.red.shade400)),
          ),
        ),
      ],
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [tier.colors.primary, tier.colors.primaryDark],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: tier.colors.primary.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: companionService != null && companionService!.isLoaded
            ? ClipOval(
                child: CompanionView(
                  surface: CompanionSurface.homeAdventure,
                  config: companionService!.config!,
                  size: 40,
                ),
              )
            : Center(
                child: Text(
                  studentName.isNotEmpty ? studentName[0].toUpperCase() : 'C',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 2. GREETING CARD — avatar + name + grade + streak + collectibles
  // ---------------------------------------------------------------------------
  Widget _buildGreetingCard() {
    final tier = _tier;
    return Container(
      width: double.infinity,
      padding: tier.shape.cardPadding,
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        border: Border.all(color: tier.colors.primary.withOpacity(0.12), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          // Avatar circle
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  tier.colors.primary.withOpacity(0.15),
                  tier.colors.accent.withOpacity(0.15),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              shape: BoxShape.circle,
              border: Border.all(
                color: tier.colors.primary.withOpacity(0.25),
                width: 2,
              ),
            ),
            child: companionService != null && companionService!.isLoaded
                ? ClipOval(
                    child: CompanionView(
                      surface: CompanionSurface.homeAdventure,
                      config: companionService!.config!,
                      size: 48,
                    ),
                  )
                : Center(
                    child: Text(
                      '\u{1F95D}',
                      style: const TextStyle(fontSize: 26),
                    ),
                  ),
          ),
          const SizedBox(width: 12),
          // Name + grade + journey
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Hi, $studentName! \u{1F44B}',
                  style: TextStyle(
                    fontSize: tier.typography.headlineSize,
                    fontWeight: FontWeight.w800,
                    color: tier.colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Grade $selectedGrade \u{00B7} $_journeyTheme',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: tier.colors.textMuted,
                  ),
                ),
              ],
            ),
          ),
          // Streak + daily collectibles
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Tiny streak badge
              if (streak > 0)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: KiwiColors.streakOrange.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
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
                          color: KiwiColors.streakOrange,
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 4),
              // Daily progress as collectibles
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: tier.colors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('\u{2B50}', style: TextStyle(fontSize: 11)),
                    const SizedBox(width: 3),
                    Text(
                      '$dailyProgress done today',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: tier.colors.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 3. CONTINUE CARD — shows the topic the student should pick up next
  // ---------------------------------------------------------------------------
  Widget _buildContinueCard() {
    final tier = _tier;
    final continueTopic = studentLevels?.continueWithTopic;
    final topicName = continueTopic?.topicName ?? 'Start Learning';
    final levelName = continueTopic?.currentLevelName ?? 'Starter';
    final currentLv = continueTopic?.currentLevel ?? 1;
    final region = continueTopic != null
        ? _regionForTopic(TopicV2(
            topicId: continueTopic.topicId,
            topicName: continueTopic.topicName,
            totalQuestions: 0,
            difficultyDistribution: const {},
          ))
        : const _Region('Explore Land', '\u{1F30D}', Color(0xFF42A5F5), Color(0xFF1E88E5));

    return GestureDetector(
      onTap: continueTopic != null
          ? () => onTopicTap(continueTopic.topicId, continueTopic.topicName)
          : null,
      child: Container(
        width: double.infinity,
        padding: tier.shape.cardPadding,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [tier.colors.buttonGradientStart, tier.colors.buttonGradientEnd],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          boxShadow: [
            BoxShadow(
              color: tier.colors.primary.withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              children: [
                Text(region.emoji, style: const TextStyle(fontSize: 22)),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Continue',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.8),
                          letterSpacing: 0.5,
                        ),
                      ),
                      Text(
                        topicName,
                        style: TextStyle(
                          fontSize: tier.typography.headlineSize - 2,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                // Level badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'Lv $currentLv',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          color: tier.colors.primaryDark,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(Icons.play_arrow_rounded,
                          size: 16, color: tier.colors.primaryDark),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // Level progress dots — 10 levels as small dots
            Row(
              children: List.generate(10, (i) {
                final lv = i + 1;
                final isDone = lv < currentLv;
                final isCurrent = lv == currentLv;
                return Expanded(
                  child: Container(
                    height: isCurrent ? 6 : 4,
                    margin: EdgeInsets.only(right: i < 9 ? 3 : 0),
                    decoration: BoxDecoration(
                      color: isDone
                          ? Colors.white
                          : isCurrent
                              ? Colors.white.withOpacity(0.7)
                              : Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                );
              }),
            ),
            const SizedBox(height: 4),
            // Level name subtitle
            Text(
              levelName,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: Colors.white.withOpacity(0.75),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // SMART PRACTICE CARD — cross-topic adaptive session
  // ---------------------------------------------------------------------------
  Widget _buildSmartPracticeCard() {
    final tier = _tier;
    final mastered = masteryOverview?['total_mastered'] as int? ?? 0;
    final total = masteryOverview?['total_clusters'] as int? ?? 0;

    return GestureDetector(
      onTap: onSmartSession,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF7C4DFF), Color(0xFF536DFE)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF7C4DFF).withOpacity(0.3),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            const Text('\u{1F9E0}', style: TextStyle(fontSize: 24)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Smart Practice',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    total > 0
                        ? '$mastered/$total skills mastered • Mixed topics'
                        : 'Practice across all topics',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: Colors.white.withOpacity(0.8),
                    ),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'GO',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF7C4DFF),
                    ),
                  ),
                  SizedBox(width: 2),
                  Icon(Icons.bolt_rounded, size: 14, color: Color(0xFF7C4DFF)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // GRADE SELECTOR — compact version
  // ---------------------------------------------------------------------------
  Widget _buildGradeSelector() {
    final tier = _tier;
    const gradeGradients = [
      [Color(0xFF00E676), Color(0xFF00C853)],
      [Color(0xFF448AFF), Color(0xFF2962FF)],
      [Color(0xFFFF9100), Color(0xFFFF6D00)],
      [Color(0xFFE040FB), Color(0xFFAA00FF)],
      [Color(0xFFFF5252), Color(0xFFD50000)],
      [Color(0xFF00BCD4), Color(0xFF0097A7)],
    ];
    const gradeLabels = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6'];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: List.generate(6, (i) {
          final grade = i + 1;
          final isSelected = grade == selectedGrade;
          final colors = gradeGradients[i];
          return GestureDetector(
            onTap: () => onGradeChanged?.call(grade),
            child: Container(
              margin: EdgeInsets.only(right: i < 5 ? 8 : 0),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                gradient: isSelected ? LinearGradient(colors: colors) : null,
                color: isSelected ? null : tier.colors.cardBg,
                borderRadius: BorderRadius.circular(tier.shape.chipRadius),
                border: Border.all(
                  color: isSelected ? colors[1] : colors[0].withOpacity(0.2),
                  width: isSelected ? 2 : 1,
                ),
                boxShadow: isSelected
                    ? [BoxShadow(
                        color: colors[0].withOpacity(0.25),
                        blurRadius: 6,
                        offset: const Offset(0, 2),
                      )]
                    : null,
              ),
              alignment: Alignment.center,
              child: Text(
                gradeLabels[i],
                style: TextStyle(
                  fontSize: tier.typography.chipSize,
                  fontWeight: FontWeight.w800,
                  color: isSelected ? Colors.white : colors[0],
                ),
              ),
            ),
          );
        }),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // REGION CHIPS — horizontal scrollable list of topic regions
  // ---------------------------------------------------------------------------
  Widget _buildRegionChips() {
    final tier = _tier;
    final hasTopics = topicsV2 != null && topicsV2!.isNotEmpty;

    if (topicsV2Loading && !hasTopics) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(20),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (!hasTopics) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: tier.colors.cardBg,
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          border: Border.all(color: Colors.grey.withOpacity(0.15)),
        ),
        child: const Text(
          'No topics available yet. Check your connection.',
          style: TextStyle(fontSize: 12, color: KiwiColors.textMuted),
        ),
      );
    }

    // Section header
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text('\u{1F30E}', style: TextStyle(fontSize: 16)),
            const SizedBox(width: 6),
            Text(
              'EXPLORE',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 1,
                color: tier.colors.textMuted,
              ),
            ),
            if (topicsV2Loading) ...[
              const SizedBox(width: 8),
              const SizedBox(
                width: 12, height: 12,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ],
          ],
        ),
        const SizedBox(height: 10),
        // Region chips as a vertical list of compact cards
        ...topicsV2!.asMap().entries.map((entry) {
          final i = entry.key;
          final topic = entry.value;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: _buildRegionCard(topic, i),
          );
        }),
      ],
    );
  }

  Widget _buildRegionCard(TopicV2 topic, int index) {
    final tier = _tier;
    final region = _regionForTopic(topic);
    final isLocked = lockedTopics.contains(topic.topicId);

    // Real level progress from the student levels API
    final topicLevels = studentLevels?.forTopic(topic.topicId);
    final currentLv = topicLevels?.currentLevel ?? 1;
    final progressFraction = topicLevels?.progressFraction ?? 0.0;
    final levelName = topicLevels?.currentLevelName ?? 'Starter';

    return Builder(
      builder: (context) => GestureDetector(
        onTap: isLocked
            ? () => _showUnlockDialog(context, topic)
            : () => onTopicTap(topic.topicId, topic.topicName),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          decoration: BoxDecoration(
            color: tier.colors.cardBg,
            borderRadius: BorderRadius.circular(tier.shape.cardRadius),
            border: Border.all(
              color: isLocked
                  ? Colors.grey.withOpacity(0.15)
                  : region.color.withOpacity(0.2),
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.03),
                blurRadius: 6,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Stack(
            children: [
              Row(
                children: [
                  // Region icon circle
                  Container(
                    width: tier.isJunior ? 44 : 38,
                    height: tier.isJunior ? 44 : 38,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [region.color, region.colorDark],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: region.color.withOpacity(0.25),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      region.emoji,
                      style: TextStyle(fontSize: tier.isJunior ? 20 : 17),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // Region name + topic name
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          topic.topicName,
                          style: TextStyle(
                            fontSize: tier.typography.topicNameSize,
                            fontWeight: FontWeight.w700,
                            color: tier.colors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Lv $currentLv \u{00B7} $levelName',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                            color: tier.colors.textMuted,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        // Mastery badge from masteryOverview
                        if (masteryOverview != null &&
                            masteryOverview!['topic_mastery'] != null &&
                            (masteryOverview!['topic_mastery'] as Map<String, dynamic>).containsKey(topic.topicId))
                          Builder(builder: (_) {
                            final tm = (masteryOverview!['topic_mastery'] as Map<String, dynamic>)[topic.topicId] as Map<String, dynamic>;
                            final mastered = tm['mastered'] as int? ?? 0;
                            final total = tm['total'] as int? ?? 0;
                            return Padding(
                              padding: const EdgeInsets.only(top: 2),
                              child: Text(
                                '$mastered/$total mastered',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  color: tier.colors.primary,
                                ),
                              ),
                            );
                          }),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Level badge with circular progress
                  SizedBox(
                    width: 36,
                    height: 36,
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        CircularProgressIndicator(
                          value: progressFraction,
                          strokeWidth: 3,
                          backgroundColor: region.color.withOpacity(0.12),
                          valueColor: AlwaysStoppedAnimation<Color>(region.color),
                        ),
                        Text(
                          '$currentLv',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: region.color,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 6),
                  Icon(
                    Icons.chevron_right_rounded,
                    size: 20,
                    color: region.color.withOpacity(0.5),
                  ),
                ],
              ),
              // Lock overlay
              if (isLocked)
                Positioned.fill(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(tier.shape.cardRadius - 2),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 2, sigmaY: 2),
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.45),
                          borderRadius: BorderRadius.circular(tier.shape.cardRadius - 2),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.lock_rounded, color: Colors.white, size: 18),
                            const SizedBox(width: 6),
                            const Text(
                              '\u{1FA99}',
                              style: TextStyle(fontSize: 12),
                            ),
                            const SizedBox(width: 3),
                            const Text(
                              '500',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                                color: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // UNLOCK DIALOG — kept from original
  // ---------------------------------------------------------------------------
  void _showUnlockDialog(BuildContext context, TopicV2 topic) {
    final tier = _tier;
    final hasEnoughCoins = kiwiCoins >= 500;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        ),
        backgroundColor: tier.colors.cardBg,
        title: Row(
          children: [
            const Icon(Icons.lock_open_rounded, size: 22),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                topic.topicName,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: tier.colors.textPrimary,
                ),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Unlock for 500 Kiwi Coins?',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: hasEnoughCoins
                    ? KiwiColors.gemGold.withOpacity(0.1)
                    : Colors.red.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: hasEnoughCoins
                      ? KiwiColors.gemGold.withOpacity(0.3)
                      : Colors.red.withOpacity(0.2),
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('\u{1FA99}', style: TextStyle(fontSize: 16)),
                  const SizedBox(width: 6),
                  Text(
                    'You have $kiwiCoins coins',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: hasEnoughCoins ? KiwiColors.gemGold : Colors.red,
                    ),
                  ),
                ],
              ),
            ),
            if (!hasEnoughCoins) ...[
              const SizedBox(height: 8),
              Text(
                'Keep practising to earn more coins!',
                style: TextStyle(
                  fontSize: 11,
                  color: tier.colors.textMuted,
                ),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(
              'Cancel',
              style: TextStyle(
                color: tier.colors.textMuted,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          ElevatedButton(
            onPressed: hasEnoughCoins
                ? () {
                    Navigator.of(ctx).pop();
                    onTopicUnlock?.call(topic.topicId, topic.topicName);
                  }
                : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: KiwiColors.gemGold,
              disabledBackgroundColor: Colors.grey.withOpacity(0.3),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('\u{1FA99}', style: TextStyle(fontSize: 12)),
                const SizedBox(width: 4),
                Text(
                  'Unlock',
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: hasEnoughCoins ? Colors.white : Colors.grey,
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

// ---------------------------------------------------------------------------
// Helper data class for region metadata
// ---------------------------------------------------------------------------
class _Region {
  final String name;
  final String emoji;
  final Color color;
  final Color colorDark;

  const _Region(this.name, this.emoji, this.color, this.colorDark);
}
