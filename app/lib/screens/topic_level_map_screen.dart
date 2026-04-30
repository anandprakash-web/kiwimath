import 'package:flutter/material.dart';
import '../models/student_levels.dart';
import '../theme/kiwi_theme.dart';

/// Vertical 10-level map for a single topic.
///
/// Shows each of the 10 micro-levels as nodes on a vertical path,
/// with status indicators (locked/current/completed), star ratings,
/// and a "Play" button on the current level.
class TopicLevelMapScreen extends StatelessWidget {
  final String topicName;
  final TopicLevels topicLevels;
  final void Function(int level) onPlayLevel;
  final VoidCallback? onBack;
  final int grade;

  const TopicLevelMapScreen({
    super.key,
    required this.topicName,
    required this.topicLevels,
    required this.onPlayLevel,
    this.onBack,
    this.grade = 1,
  });

  KiwiTier get _tier => KiwiTier.forGrade(grade);

  @override
  Widget build(BuildContext context) {
    final tier = _tier;
    return Scaffold(
      backgroundColor: tier.colors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(context, tier),
            _buildProgressSummary(tier),
            Expanded(
              child: _buildLevelPath(tier),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, KiwiTier tier) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          GestureDetector(
            onTap: onBack ?? () => Navigator.of(context).pop(),
            child: Container(
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
                Icons.arrow_back_rounded,
                size: 20,
                color: tier.colors.primaryDark,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  topicName,
                  style: TextStyle(
                    fontSize: tier.typography.headlineSize,
                    fontWeight: FontWeight.w800,
                    color: tier.colors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  'Grade ${topicLevels.grade} \u{00B7} ${topicLevels.levels.length} Levels',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
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

  Widget _buildProgressSummary(KiwiTier tier) {
    final completed = topicLevels.levels.where((l) => l.isCompleted).length;
    final total = topicLevels.levels.length;
    final totalStars = topicLevels.levels.fold<int>(0, (sum, l) => sum + l.stars);
    final maxStars = total * 3;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        border: Border.all(color: tier.colors.primary.withOpacity(0.12), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        children: [
          // Circular progress
          SizedBox(
            width: 48,
            height: 48,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: topicLevels.progressFraction,
                  strokeWidth: 4,
                  backgroundColor: tier.colors.primary.withOpacity(0.12),
                  valueColor: AlwaysStoppedAnimation<Color>(tier.colors.primary),
                ),
                Text(
                  '$completed/$total',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    color: tier.colors.primaryDark,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$completed of $total levels completed',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: tier.colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    const Text('\u{2B50}', style: TextStyle(fontSize: 12)),
                    const SizedBox(width: 4),
                    Text(
                      '$totalStars / $maxStars stars',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: tier.colors.textMuted,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          if (topicLevels.allMastered)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [tier.colors.buttonGradientStart, tier.colors.buttonGradientEnd],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('\u{1F3C6}', style: TextStyle(fontSize: 14)),
                  SizedBox(width: 4),
                  Text(
                    'Mastered',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildLevelPath(KiwiTier tier) {
    // Show levels bottom-to-top (level 1 at bottom, 10 at top).
    final reversedLevels = topicLevels.levels.reversed.toList();

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      itemCount: reversedLevels.length,
      itemBuilder: (context, index) {
        final level = reversedLevels[index];
        final isLast = index == reversedLevels.length - 1;
        return _buildLevelNode(level, tier, isLast);
      },
    );
  }

  Widget _buildLevelNode(LevelInfo level, KiwiTier tier, bool isLast) {
    // Colors based on status.
    final Color nodeColor;
    final Color nodeBorderColor;
    final Color textColor;
    final IconData statusIcon;

    if (level.isCompleted) {
      nodeColor = tier.colors.primary.withOpacity(0.15);
      nodeBorderColor = tier.colors.primary;
      textColor = tier.colors.primaryDark;
      statusIcon = Icons.check_circle_rounded;
    } else if (level.isCurrent) {
      nodeColor = tier.colors.accent.withOpacity(0.15);
      nodeBorderColor = tier.colors.accent;
      textColor = tier.colors.textPrimary;
      statusIcon = Icons.play_circle_rounded;
    } else {
      nodeColor = Colors.grey.withOpacity(0.08);
      nodeBorderColor = Colors.grey.withOpacity(0.2);
      textColor = tier.colors.textMuted;
      statusIcon = Icons.lock_rounded;
    }

    return Column(
      children: [
        // Connection line (above node, except for top node).
        if (!isLast || true) // Always show for visual consistency
          Container(
            width: 3,
            height: isLast ? 0 : 24,
            decoration: BoxDecoration(
              color: level.isCompleted || level.isCurrent
                  ? tier.colors.primary.withOpacity(0.3)
                  : Colors.grey.withOpacity(0.15),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        // Level node
        GestureDetector(
          onTap: level.isCurrent ? () => onPlayLevel(level.level) : null,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: tier.colors.cardBg,
              borderRadius: BorderRadius.circular(tier.shape.cardRadius),
              border: Border.all(color: nodeBorderColor, width: level.isCurrent ? 2.5 : 1.5),
              boxShadow: level.isCurrent
                  ? [
                      BoxShadow(
                        color: tier.colors.accent.withOpacity(0.2),
                        blurRadius: 10,
                        offset: const Offset(0, 3),
                      ),
                    ]
                  : [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.03),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
            ),
            child: Row(
              children: [
                // Level number circle
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: nodeColor,
                    shape: BoxShape.circle,
                    border: Border.all(color: nodeBorderColor, width: 2),
                  ),
                  child: Center(
                    child: level.isLocked
                        ? Icon(Icons.lock_rounded, size: 16, color: textColor)
                        : Text(
                            '${level.level}',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: textColor,
                            ),
                          ),
                  ),
                ),
                const SizedBox(width: 12),
                // Level info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        level.name,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: textColor,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        level.isCompleted
                            ? '${level.questionsDone}/${level.questionsTotal} questions · ${(level.accuracy * 100).toInt()}%'
                            : level.isCurrent
                                ? '${level.questionsDone}/${level.questionsTotal} questions'
                                : 'Difficulty ${level.difficultyMin}-${level.difficultyMax}',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          color: tier.colors.textMuted,
                        ),
                      ),
                    ],
                  ),
                ),
                // Stars (for completed) or Play button (for current)
                if (level.isCompleted)
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: List.generate(3, (i) {
                      return Padding(
                        padding: const EdgeInsets.only(left: 2),
                        child: Icon(
                          i < level.stars ? Icons.star_rounded : Icons.star_border_rounded,
                          size: 18,
                          color: i < level.stars
                              ? KiwiColors.gemGold
                              : Colors.grey.withOpacity(0.3),
                        ),
                      );
                    }),
                  )
                else if (level.isCurrent)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [tier.colors.buttonGradientStart, tier.colors.buttonGradientEnd],
                      ),
                      borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
                      boxShadow: [
                        BoxShadow(
                          color: tier.colors.accent.withOpacity(0.25),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.play_arrow_rounded, size: 16, color: Colors.white),
                        SizedBox(width: 4),
                        Text(
                          'Play',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  Icon(statusIcon, size: 20, color: textColor),
              ],
            ),
          ),
        ),
        // Connection line below
        if (level.level > 1)
          Container(
            width: 3,
            height: 24,
            decoration: BoxDecoration(
              color: level.isCompleted
                  ? tier.colors.primary.withOpacity(0.3)
                  : Colors.grey.withOpacity(0.15),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
      ],
    );
  }
}
