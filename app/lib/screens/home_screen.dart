import 'package:flutter/material.dart';
import '../models/companion.dart';
import '../models/question_v2.dart';
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
  });

  /// Grade-adaptive tier tokens.
  KiwiTier get _tier => KiwiTier.forGrade(selectedGrade);

  @override
  Widget build(BuildContext context) {
    final tier = _tier;
    return Scaffold(
      backgroundColor: tier.colors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 10),
              _buildTopBar(),
              const SizedBox(height: 14),
              // Companion greeting on home screen
              if (companionService != null && companionService!.isLoaded)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    children: [
                      CompanionView(
                        surface: CompanionSurface.homeAdventure,
                        config: companionService!.config!,
                        size: 48,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          streak == 0
                              ? "Hey! Let's start today's adventure!"
                              : streak < 3
                                  ? 'Welcome back! Keep going!'
                                  : 'Wow, $streak days! You rock!',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: tier.colors.primaryDark,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              _buildStreakCard(),
              const SizedBox(height: 18),
              _buildGradeSelector(),
              const SizedBox(height: 12),
              _buildTopicsSection(),
              const SizedBox(height: 18),
              _buildLeagueTeaser(),
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
  Widget _buildTopBar() {
    final tier = _tier;
    return Row(
      children: [
        GestureDetector(
          onLongPress: onSignOut,
          child: Text(
            tier.isJunior ? '\u{1F95D}' : '\u{1F9E0}',
            style: TextStyle(fontSize: tier.isJunior ? 22 : 18),
          ),
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
        _chip('\u{1FA99}', '$kiwiCoins', KiwiColors.gemGold),
        const SizedBox(width: 5),
        _chip('\u{1F48E}', '$masteryGems', KiwiColors.gemBlue),
        const SizedBox(width: 5),
        _chip('\u26A1', '$xp', KiwiColors.xpPurple),
      ],
    );
  }

  Widget _chip(String icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withOpacity(0.15), color.withOpacity(0.08)],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.2), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(icon, style: const TextStyle(fontSize: 13)),
          const SizedBox(width: 3),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // 2. STREAK CARD
  // ---------------------------------------------------------------------------
  Widget _buildStreakCard() {
    final tier = _tier;
    final bool goalDone = dailyProgress >= dailyGoal && dailyGoal > 0;

    // Streak milestone messaging
    String streakMessage;
    if (streak == 0) {
      streakMessage = "Start today's practice!";
    } else if (streak == 1) {
      streakMessage = 'Great start! Come back tomorrow.';
    } else if (streak < 7) {
      streakMessage = '${7 - streak} more days to a weekly streak!';
    } else if (streak == 7) {
      streakMessage = 'One full week! Amazing!';
    } else if (streak < 30) {
      streakMessage = '${30 - streak} days to a monthly streak!';
    } else {
      streakMessage = 'Incredible dedication!';
    }

    return Container(
      width: double.infinity,
      padding: tier.shape.cardPadding,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [tier.colors.streakGradientStart, tier.colors.streakGradientEnd],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
      ),
      child: Column(
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // Streak number with fire
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.18),
                  borderRadius: BorderRadius.circular(16),
                ),
                alignment: Alignment.center,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      streak > 0 ? '\u{1F525}' : '\u{1F331}',
                      style: const TextStyle(fontSize: 18),
                    ),
                    Text(
                      '$streak',
                      style: TextStyle(
                        fontSize: _tier.typography.streakNumberSize * 0.7,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                        height: 1.0,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              // Streak info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      streak == 0 ? 'Start your streak' : 'Day $streak streak',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      streakMessage,
                      style: const TextStyle(fontSize: 11, color: Colors.white70),
                    ),
                  ],
                ),
              ),
              // Coins + gems compact display
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('\u{1FA99}', style: TextStyle(fontSize: 12)),
                      const SizedBox(width: 3),
                      Text(
                        '$kiwiCoins',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text('\u{1F48E}', style: TextStyle(fontSize: 12)),
                      const SizedBox(width: 3),
                      Text(
                        '$masteryGems',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Daily goal progress
          Row(
            children: [
              Text(
                goalDone ? "Today's goal complete!" : "Today's goal",
                style: const TextStyle(fontSize: 11, color: Colors.white70),
              ),
              const Spacer(),
              if (goalDone)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.check_circle, size: 14, color: Colors.white),
                    const SizedBox(width: 4),
                    Text(
                      '$dailyGoal/$dailyGoal done${dailyProgress > dailyGoal ? ' +${dailyProgress - dailyGoal} extra!' : ''}',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                  ],
                )
              else
                Text(
                  '$dailyProgress/$dailyGoal questions',
                  style: const TextStyle(fontSize: 11, color: Colors.white70),
                ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: dailyGoal > 0
                  ? (dailyProgress / dailyGoal).clamp(0.0, 1.0)
                  : 0,
              minHeight: 6,
              backgroundColor: Colors.white.withOpacity(0.15),
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // GRADE SELECTOR
  // ---------------------------------------------------------------------------
  Widget _buildGradeSelector() {
    final tier = _tier;
    // Only Grade 1 and Grade 2 for now
    const gradeGradients = [
      [Color(0xFF00E676), Color(0xFF00C853)],  // G1: emerald
      [Color(0xFF448AFF), Color(0xFF2962FF)],  // G2: electric blue
    ];
    const gradeLabels = ['Grade 1', 'Grade 2'];
    const gradeSubtitles = ['Foundations', 'Challenge'];
    return Row(
      children: List.generate(2, (i) {
        final grade = i + 1;
        final isSelected = grade == selectedGrade;
        final colors = gradeGradients[i];
        return Expanded(
          child: GestureDetector(
            onTap: () => onGradeChanged?.call(grade),
            child: Container(
              margin: EdgeInsets.only(right: i < 1 ? 8 : 0),
              padding: EdgeInsets.symmetric(vertical: tier.isJunior ? 12 : 10),
              decoration: BoxDecoration(
                gradient: isSelected
                    ? LinearGradient(colors: colors)
                    : null,
                color: isSelected ? null : tier.colors.cardBg,
                borderRadius: BorderRadius.circular(tier.shape.chipRadius),
                border: Border.all(
                  color: isSelected
                      ? colors[1]
                      : colors[0].withOpacity(0.2),
                  width: isSelected ? 2 : 1,
                ),
                boxShadow: isSelected
                    ? [BoxShadow(
                        color: colors[0].withOpacity(0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      )]
                    : null,
              ),
              alignment: Alignment.center,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    gradeLabels[i],
                    style: TextStyle(
                      fontSize: tier.typography.chipSize + 1,
                      fontWeight: FontWeight.w800,
                      color: isSelected ? Colors.white : colors[0],
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    gradeSubtitles[i],
                    style: TextStyle(
                      fontSize: tier.typography.chipSize - 2,
                      fontWeight: FontWeight.w500,
                      color: isSelected
                          ? Colors.white.withOpacity(0.85)
                          : colors[0].withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }),
    );
  }

  // ---------------------------------------------------------------------------
  // TOPICS SECTION — unified v2 topics grid
  // ---------------------------------------------------------------------------

  /// Emoji for a topic based on its display name or id.
  static String _emojiForTopic(String name, String topicId) {
    final lower = name.toLowerCase();
    final cid = topicId.toLowerCase();
    if (lower.contains('count') || cid.contains('count')) return '\u{1F522}';
    if (lower.contains('add') || cid.contains('add')) return '\u2795';
    if (lower.contains('subtract') || cid.contains('subtract')) return '\u2796';
    if (lower.contains('shape') || cid.contains('shape') || cid.contains('geo')) return '\u{1F537}';
    if (lower.contains('pattern') || cid.contains('pattern')) return '\u{1F501}';
    if (lower.contains('measur') || cid.contains('measur') || cid.contains('length')) return '\u{1F4CF}';
    if (lower.contains('place value') || cid.contains('place_value')) return '\u{1F3E0}';
    if (lower.contains('multipli') || cid.contains('multipli') || cid.contains('times')) return '\u2716';
    if (lower.contains('divis') || cid.contains('divis')) return '\u2797';
    if (lower.contains('fraction') || cid.contains('fraction')) return '\u{1F967}';
    if (lower.contains('decimal') || cid.contains('decimal')) return '\u{1F4B2}';
    if (lower.contains('time') || cid.contains('time') || cid.contains('clock')) return '\u{1F552}';
    if (lower.contains('money') || cid.contains('money')) return '\u{1F4B0}';
    if (lower.contains('data') || cid.contains('data') || cid.contains('graph')) return '\u{1F4CA}';
    if (lower.contains('logic') || cid.contains('logic') || cid.contains('puzzle')) return '\u{1F9E9}';
    if (lower.contains('spatial') || cid.contains('spatial') || lower.contains('3d')) return '\u{1F4E6}';
    if (lower.contains('word') || cid.contains('word') || lower.contains('story') || lower.contains('stories')) return '\u{1F4D6}';
    if (lower.contains('number') || cid.contains('number')) return '\u{1F523}';
    if (lower.contains('area') || cid.contains('area') || cid.contains('perim')) return '\u{1F4D0}';
    if (lower.contains('angle') || cid.contains('angle')) return '\u{1F4D0}';
    if (lower.contains('algebra') || cid.contains('algebra') || cid.contains('variable')) return '\u{1F170}';
    if (lower.contains('percent') || cid.contains('percent') || cid.contains('ratio')) return '\u{1F4C8}';
    return '\u{1F4D6}'; // fallback: book
  }

  static const _topicColors = [
    Color(0xFF00C853), Color(0xFF2962FF), Color(0xFFFF6D00), Color(0xFF7C4DFF),
    Color(0xFFF50057), Color(0xFF00B8D4), Color(0xFFFFD600), Color(0xFF64DD17),
    Color(0xFFFF3D00), Color(0xFF304FFE), Color(0xFFFF4081), Color(0xFF00BFA5),
  ];

  Widget _buildTopicsSection() {
    final tier = _tier;
    final hasTopics = topicsV2 != null && topicsV2!.isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              '\u{1F3C6}',
              style: TextStyle(fontSize: 16),
            ),
            const SizedBox(width: 6),
            const Text(
              'PRACTICE',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 1,
                color: KiwiColors.textMuted,
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
        const SizedBox(height: 8),
        if (topicsV2Loading && !hasTopics)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(20),
              child: CircularProgressIndicator(),
            ),
          )
        else if (!hasTopics)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: tier.colors.cardBg,
              borderRadius: BorderRadius.circular(tier.shape.cardRadius),
              border: Border.all(color: Colors.grey.withOpacity(0.15)),
            ),
            child: const Text(
              'No topics available yet. Check your connection.',
              style: TextStyle(
                fontSize: 12,
                color: KiwiColors.textMuted,
              ),
            ),
          )
        else
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: topicsV2!.length,
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: tier.shape.topicCardAspect,
            ),
            itemBuilder: (context, i) {
              final topic = topicsV2![i];
              final color = _topicColors[i % _topicColors.length];
              return _buildTopicCard(topic, color);
            },
          ),
      ],
    );
  }

  /// Pick a gradient color pair for a topic card by index.
  List<Color> _topicGradientStart(int idx) {
    final gradients = KiwiColors.topicGradients;
    return gradients[idx % gradients.length];
  }

  Widget _buildTopicCard(TopicV2 topic, Color color) {
    final tier = _tier;
    final easy = topic.difficultyDistribution['easy'] ?? 0;
    final medium = topic.difficultyDistribution['medium'] ?? 0;
    final hard = topic.difficultyDistribution['hard'] ?? 0;
    final idx = topicsV2!.indexOf(topic);
    final gradientColors = _topicGradientStart(idx);

    return GestureDetector(
      onTap: () => onTopicTap(topic.topicId, topic.topicName),
      child: Container(
        padding: tier.shape.cardPadding,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              gradientColors[0].withOpacity(0.12),
              gradientColors[1].withOpacity(0.06),
            ],
          ),
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          border: Border.all(
            color: gradientColors[0].withOpacity(0.3),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: gradientColors[0].withOpacity(0.15),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Emoji in a colored circle
                Container(
                  width: tier.isJunior ? 44 : 38,
                  height: tier.isJunior ? 44 : 38,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: gradientColors,
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: gradientColors[0].withOpacity(0.3),
                        blurRadius: 6,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    _emojiForTopic(topic.topicName, topic.topicId),
                    style: TextStyle(fontSize: tier.isJunior ? 22 : 18),
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: gradientColors[0].withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '${topic.totalQuestions}',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: gradientColors[1],
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              topic.topicName,
              style: TextStyle(
                fontSize: tier.typography.topicNameSize,
                fontWeight: FontWeight.w700,
                color: tier.colors.textPrimary,
              ),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const Spacer(),
            // Difficulty distribution mini-bar — thicker and more vivid
            ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: Row(
                children: [
                  if (easy > 0)
                    Expanded(
                      flex: easy,
                      child: Container(height: 4, color: const Color(0xFF00E676)),
                    ),
                  if (medium > 0)
                    Expanded(
                      flex: medium,
                      child: Container(height: 4, color: const Color(0xFFFFD600)),
                    ),
                  if (hard > 0)
                    Expanded(
                      flex: hard,
                      child: Container(height: 4, color: const Color(0xFFFF5252)),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 4),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // LEAGUE TEASER
  // ---------------------------------------------------------------------------
  Widget _buildLeagueTeaser() {
    final tier = _tier;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: tier.isJunior
              ? [const Color(0xFFFFD600), const Color(0xFFFFAB00)]
              : [const Color(0xFF536DFE), const Color(0xFF304FFE)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        boxShadow: [
          BoxShadow(
            color: tier.isJunior
                ? const Color(0xFFFFD600).withOpacity(0.3)
                : const Color(0xFF536DFE).withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          const Text('\u{1F3C6}', style: TextStyle(fontSize: 32)),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Kiwi League',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: tier.isJunior ? const Color(0xFF3E2723) : Colors.white,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Coming soon \u2014 compete with friends!',
                  style: TextStyle(
                    fontSize: 11,
                    color: tier.isJunior
                        ? const Color(0xFF5D4037)
                        : Colors.white70,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(tier.isJunior ? 0.6 : 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              'Soon',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: tier.isJunior ? const Color(0xFFE65100) : Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
