import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/pillar_progress.dart';
import '../services/pillar_api.dart';
import '../theme/kiwi_theme.dart';
import 'level_topic_screen.dart';

/// Pillar Detail — shows the 5 levels of a single pillar as a vertical path.
///
/// Each level node shows:
///   - Level number + grade range
///   - Topic list
///   - Lock status (only current level + 1 above are unlocked)
///   - Mastery progress
///
/// Tapping an unlocked level opens LevelTopicScreen.
class PillarDetailScreen extends StatefulWidget {
  final String userId;
  final PillarMeta pillar;
  final int grade;
  final PillarProgress? progress;

  const PillarDetailScreen({
    super.key,
    required this.userId,
    required this.pillar,
    required this.grade,
    this.progress,
  });

  @override
  State<PillarDetailScreen> createState() => _PillarDetailScreenState();
}

class _PillarDetailScreenState extends State<PillarDetailScreen> {
  List<Map<String, dynamic>>? _levels;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadLevels();
  }

  Future<void> _loadLevels() async {
    try {
      final levels = await PillarApi.fetchLevels(
        pillar: widget.pillar.id,
        grade: widget.grade,
      );
      if (mounted) setState(() { _levels = levels; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.grade);
    final colors = tier.colors;
    final typo = tier.typography;
    final pillarColor = Color(int.parse('FF${widget.pillar.colorHex}', radix: 16));

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: colors.background,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_rounded, color: colors.textPrimary, size: 20),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Row(
          children: [
            Text(widget.pillar.emoji, style: const TextStyle(fontSize: 22)),
            SizedBox(width: KiwiSpacing.sm),
            Text(
              widget.pillar.name,
              style: TextStyle(
                fontSize: typo.headlineSize,
                fontWeight: FontWeight.w800,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
                padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.lg, vertical: KiwiSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Pillar tagline
                    Text(
                      widget.pillar.tagline,
                      style: TextStyle(
                        fontSize: typo.bodySize,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    SizedBox(height: KiwiSpacing.lg),

                    // Overall pillar progress
                    if (widget.progress != null && widget.progress!.questionsAttempted > 0)
                      _PillarProgressHeader(
                        progress: widget.progress!,
                        pillarColor: pillarColor,
                        colors: colors,
                        typo: typo,
                        tier: tier,
                      ),

                    SizedBox(height: KiwiSpacing.lg),

                    // Level path
                    ...(_levels ?? []).asMap().entries.map((entry) {
                      final index = entry.key;
                      final level = entry.value;
                      final levelNum = level['level'] as int;
                      final gradeRange = (level['grade_range'] as List<dynamic>?)
                          ?.map((e) => e as int)
                          .toList() ?? [];
                      final topics = (level['topics'] as List<dynamic>?) ?? [];
                      final questionCount = level['question_count'] as int? ?? 0;
                      final locked = level['locked'] as bool? ?? false;
                      final isLast = index == (_levels!.length - 1);
                      final currentLevel = widget.progress?.currentLevel ?? 1;

                      // Level mastery from progress
                      final levelProgress = widget.progress?.levelProgress[levelNum];
                      final mastery = levelProgress?.mastery ?? 0;

                      return _LevelNode(
                        levelNum: levelNum,
                        gradeRange: gradeRange,
                        topics: topics.cast<Map<String, dynamic>>(),
                        questionCount: questionCount,
                        locked: locked,
                        isActive: levelNum == currentLevel,
                        isCompleted: mastery >= 60 && levelNum < currentLevel,
                        mastery: mastery,
                        isLast: isLast,
                        pillarColor: pillarColor,
                        colors: colors,
                        typo: typo,
                        tier: tier,
                        onTap: locked
                            ? null
                            : () => _openLevel(levelNum, topics.cast<Map<String, dynamic>>()),
                      );
                    }),
                  ],
                ),
              ),
            ),
    );
  }

  void _openLevel(int level, List<Map<String, dynamic>> topics) {
    HapticFeedback.lightImpact();
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => LevelTopicScreen(
          userId: widget.userId,
          pillar: widget.pillar,
          level: level,
          grade: widget.grade,
          topics: topics,
        ),
      ),
    );
  }
}

// =============================================================================
// Pillar progress header
// =============================================================================
class _PillarProgressHeader extends StatelessWidget {
  final PillarProgress progress;
  final Color pillarColor;
  final KiwiTierColors colors;
  final KiwiTierTypography typo;
  final KiwiTier tier;

  const _PillarProgressHeader({
    required this.progress,
    required this.pillarColor,
    required this.colors,
    required this.typo,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(KiwiSpacing.md),
      decoration: BoxDecoration(
        color: pillarColor.withOpacity(0.06),
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        border: Border.all(color: pillarColor.withOpacity(0.15)),
      ),
      child: Row(
        children: [
          // Mastery ring
          SizedBox(
            width: 48,
            height: 48,
            child: Stack(
              children: [
                CircularProgressIndicator(
                  value: progress.masteryPercent / 100,
                  strokeWidth: 4,
                  backgroundColor: KiwiColors.pathLocked,
                  valueColor: AlwaysStoppedAnimation(pillarColor),
                ),
                Center(
                  child: Text(
                    '${progress.masteryPercent.toStringAsFixed(0)}%',
                    style: TextStyle(
                      fontSize: typo.chipSize - 2,
                      fontWeight: FontWeight.w800,
                      color: pillarColor,
                    ),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(width: KiwiSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Level ${progress.currentLevel} • ${progress.questionsCorrect}/${progress.questionsAttempted} correct',
                  style: TextStyle(
                    fontSize: typo.chipSize - 1,
                    fontWeight: FontWeight.w600,
                    color: colors.textPrimary,
                  ),
                ),
                SizedBox(height: KiwiSpacing.xs - 2),
                Text(
                  progress.canAdvance
                      ? 'Ready to advance!'
                      : 'Keep practicing to level up',
                  style: TextStyle(
                    fontSize: typo.chipSize - 2,
                    color: progress.canAdvance ? KiwiColors.kiwiGreenDark : colors.textMuted,
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

// =============================================================================
// Level node — vertical path item
// =============================================================================
class _LevelNode extends StatelessWidget {
  final int levelNum;
  final List<int> gradeRange;
  final List<Map<String, dynamic>> topics;
  final int questionCount;
  final bool locked;
  final bool isActive;
  final bool isCompleted;
  final double mastery;
  final bool isLast;
  final Color pillarColor;
  final KiwiTierColors colors;
  final KiwiTierTypography typo;
  final KiwiTier tier;
  final VoidCallback? onTap;

  const _LevelNode({
    required this.levelNum,
    required this.gradeRange,
    required this.topics,
    required this.questionCount,
    required this.locked,
    required this.isActive,
    required this.isCompleted,
    required this.mastery,
    required this.isLast,
    required this.pillarColor,
    required this.colors,
    required this.typo,
    required this.tier,
    this.onTap,
  });

  static const _levelNames = ['', 'Foundation', 'Explorer', 'Challenger', 'Advanced', 'Olympiad'];

  @override
  Widget build(BuildContext context) {
    final gradeLabel = gradeRange.isNotEmpty
        ? 'G${gradeRange.first}–${gradeRange.last}'
        : '';
    final levelName = levelNum < _levelNames.length ? _levelNames[levelNum] : 'Level $levelNum';

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Vertical line + dot ─────────────────────────────────
          SizedBox(
            width: 32,
            child: Column(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: locked
                        ? KiwiColors.pathLocked
                        : isCompleted
                            ? KiwiColors.kiwiGreen
                            : isActive
                                ? pillarColor
                                : pillarColor.withOpacity(0.3),
                    shape: BoxShape.circle,
                    border: isActive
                        ? Border.all(color: pillarColor, width: 3)
                        : null,
                  ),
                  child: Center(
                    child: locked
                        ? const Icon(Icons.lock, size: 12, color: Colors.white)
                        : isCompleted
                            ? const Icon(Icons.check, size: 14, color: Colors.white)
                            : Text(
                                '$levelNum',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                  color: Colors.white,
                                ),
                              ),
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: locked
                          ? KiwiColors.pathLocked
                          : pillarColor.withOpacity(0.3),
                    ),
                  ),
              ],
            ),
          ),
          SizedBox(width: KiwiSpacing.sm),

          // ── Card content ────────────────────────────────────────
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: isLast ? 0 : KiwiSpacing.md),
              child: Material(
                color: locked ? colors.cardBg.withOpacity(0.6) : colors.cardBg,
                borderRadius: BorderRadius.circular(tier.shape.cardRadius),
                child: InkWell(
                  onTap: onTap,
                  borderRadius: BorderRadius.circular(tier.shape.cardRadius),
                  child: Container(
                    padding: EdgeInsets.all(KiwiSpacing.md),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(tier.shape.cardRadius),
                      border: Border.all(
                        color: isActive
                            ? pillarColor
                            : locked
                                ? KiwiColors.pathLocked
                                : colors.topicCardBorder,
                        width: isActive ? 2 : 1,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Level name + grade badge
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                levelName,
                                style: TextStyle(
                                  fontSize: typo.topicNameSize,
                                  fontWeight: FontWeight.w700,
                                  color: locked ? colors.textMuted : colors.textPrimary,
                                  fontFamily: typo.fontFamily,
                                ),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: locked
                                    ? KiwiColors.pathLocked
                                    : pillarColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                gradeLabel,
                                style: TextStyle(
                                  fontSize: typo.chipSize - 3,
                                  fontWeight: FontWeight.w700,
                                  color: locked ? colors.textMuted : pillarColor,
                                ),
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: KiwiSpacing.sm),

                        // Topics
                        if (locked)
                          Text(
                            'Complete earlier levels to unlock',
                            style: TextStyle(
                              fontSize: typo.chipSize - 1,
                              color: colors.textMuted.withOpacity(0.7),
                              fontFamily: typo.fontFamily,
                            ),
                          )
                        else
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: topics.map((t) {
                              return Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: pillarColor.withOpacity(0.08),
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Text(
                                  t['name'] as String? ?? '',
                                  style: TextStyle(
                                    fontSize: typo.chipSize - 2,
                                    fontWeight: FontWeight.w500,
                                    color: colors.textPrimary,
                                    fontFamily: typo.fontFamily,
                                  ),
                                ),
                              );
                            }).toList(),
                          ),

                        // Progress bar (if attempted)
                        if (!locked && mastery > 0) ...[
                          SizedBox(height: KiwiSpacing.sm),
                          Row(
                            children: [
                              Expanded(
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(3),
                                  child: SizedBox(
                                    height: 4,
                                    child: LinearProgressIndicator(
                                      value: mastery / 100,
                                      backgroundColor: KiwiColors.pathLocked,
                                      valueColor: AlwaysStoppedAnimation(pillarColor),
                                    ),
                                  ),
                                ),
                              ),
                              SizedBox(width: KiwiSpacing.sm),
                              Text(
                                '${mastery.toStringAsFixed(0)}%',
                                style: TextStyle(
                                  fontSize: typo.chipSize - 3,
                                  fontWeight: FontWeight.w700,
                                  color: pillarColor,
                                ),
                              ),
                            ],
                          ),
                        ],

                        // Question count
                        if (!locked) ...[
                          SizedBox(height: KiwiSpacing.xs),
                          Text(
                            '$questionCount questions',
                            style: TextStyle(
                              fontSize: typo.chipSize - 3,
                              color: colors.textMuted,
                              fontFamily: typo.fontFamily,
                            ),
                          ),
                        ],
                      ],
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
}
