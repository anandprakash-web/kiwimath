import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// Olympiad tab — smart practice with progressive topic unlocking.
/// Starts with 2 topics unlocked (Counting & Observation, Patterns &
/// Sequences); the rest unlock when >=60 % mastery is reached.
/// Covers Kangaroo, IOQM, and other olympiad-style questions.
class OlympiadScreen extends StatelessWidget {
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;
  final void Function(String topicId, String topicName) onStartPractice;

  /// Per-topic mastery percentages (0–100).  Supplied by the parent
  /// (fetched from the backend student summary).  Keys are topic IDs.
  final Map<String, int> topicMastery;

  const OlympiadScreen({
    super.key,
    required this.selectedGrade,
    required this.onGradeChanged,
    required this.onStartPractice,
    this.topicMastery = const {},
  });

  // ── Topic definitions — order matters for progressive unlocking ──────────
  static const List<_TopicDef> _topics = [
    _TopicDef(
      id: 'counting_observation',
      name: 'Counting & Observation',
      emoji: '\u{1F50D}', // 🔍
      tagline: 'See what others miss',
      unlockOrder: 0, // Always unlocked
    ),
    _TopicDef(
      id: 'patterns_sequences',
      name: 'Patterns & Sequences',
      emoji: '\u{1F3B5}', // 🎵
      tagline: 'Find the hidden rhythm',
      unlockOrder: 0, // Always unlocked
    ),
    _TopicDef(
      id: 'arithmetic_missing_numbers',
      name: 'Number Mysteries',
      emoji: '\u{1F3AD}', // 🎭
      tagline: 'Fill in the blanks',
      unlockOrder: 1,
    ),
    _TopicDef(
      id: 'logic_ordering',
      name: 'Logic & Ordering',
      emoji: '\u{1F9E9}', // 🧩
      tagline: 'Think step by step',
      unlockOrder: 2,
    ),
    _TopicDef(
      id: 'spatial_reasoning_3d',
      name: 'Spatial Reasoning',
      emoji: '\u{1F4D0}', // 📐
      tagline: 'See in 3D',
      unlockOrder: 3,
    ),
    _TopicDef(
      id: 'shapes_folding_symmetry',
      name: 'Shapes & Symmetry',
      emoji: '\u{1FA9E}', // 🪞  (mirror)
      tagline: 'Fold, flip, discover',
      unlockOrder: 4,
    ),
    _TopicDef(
      id: 'word_problems_stories',
      name: 'Story Problems',
      emoji: '\u{1F4D6}', // 📖
      tagline: 'Math in the real world',
      unlockOrder: 5,
    ),
    _TopicDef(
      id: 'number_puzzles_games',
      name: 'Number Puzzles',
      emoji: '\u{1F3B2}', // 🎲
      tagline: 'Play with numbers',
      unlockOrder: 6,
    ),
  ];

  // ── Unlock logic ─────────────────────────────────────────────────────────
  /// Returns true if a topic is unlocked.  Order-0 topics are always open.
  /// Higher-order topics require that ALL topics of the previous order
  /// have >= 60 % mastery.
  bool _isUnlocked(_TopicDef topic) {
    if (topic.unlockOrder == 0) return true;
    // All topics of the previous order must be >= 60 %
    final prevTopics =
        _topics.where((t) => t.unlockOrder == topic.unlockOrder - 1);
    return prevTopics
        .every((t) => (topicMastery[t.id] ?? 0) >= 60);
  }

  static const List<IconData> _gradeIcons = [
    Icons.emoji_events_outlined,
    Icons.military_tech_outlined,
    Icons.workspace_premium_outlined,
    Icons.emoji_events,
    Icons.military_tech,
    Icons.workspace_premium,
  ];

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Header ─────────────────────────────────────────────────
              Text(
                'Olympiad Practice',
                style: TextStyle(
                  fontSize: typo.headlineSize + 2,
                  fontWeight: FontWeight.w800,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Sharpen your problem-solving skills',
                style: TextStyle(
                  fontSize: typo.bodySize,
                  color: colors.textSecondary,
                  fontFamily: typo.fontFamily,
                ),
              ),
              const SizedBox(height: 16),

              // ── Grade picker ───────────────────────────────────────────
              SizedBox(
                height: 100,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: 6,
                  separatorBuilder: (_, __) => const SizedBox(width: 10),
                  itemBuilder: (context, index) {
                    final grade = index + 1;
                    final isSelected = grade == selectedGrade;
                    return _GradeCard(
                      grade: grade,
                      icon: _gradeIcons[index],
                      isSelected: isSelected,
                      tier: KiwiTier.forGrade(grade),
                      onTap: () => onGradeChanged(grade),
                    );
                  },
                ),
              ),
              const SizedBox(height: 20),

              // ── Smart Practice header ──────────────────────────────────
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: colors.primary.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      'SMART PRACTICE',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.2,
                        color: colors.primary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Grade $selectedGrade',
                    style: TextStyle(
                      fontSize: typo.chipSize,
                      color: colors.textMuted,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Master each topic to unlock the next',
                style: TextStyle(
                  fontSize: typo.chipSize,
                  color: colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
              ),
              const SizedBox(height: 14),

              // ── Topic cards ────────────────────────────────────────────
              ..._topics.map((topic) {
                final unlocked = _isUnlocked(topic);
                final mastery = topicMastery[topic.id] ?? 0;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _TopicCard(
                    topic: topic,
                    unlocked: unlocked,
                    mastery: mastery,
                    tier: tier,
                    onTap: unlocked
                        ? () => onStartPractice(
                              'olympiad-kangaroo-g$selectedGrade',
                              topic.name,
                            )
                        : null,
                  ),
                );
              }),

              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

// =============================================================================
// Topic definition
// =============================================================================
class _TopicDef {
  final String id;
  final String name;
  final String emoji;
  final String tagline;
  final int unlockOrder; // 0 = always unlocked

  const _TopicDef({
    required this.id,
    required this.name,
    required this.emoji,
    required this.tagline,
    required this.unlockOrder,
  });
}

// =============================================================================
// Grade card (horizontal picker)
// =============================================================================
class _GradeCard extends StatelessWidget {
  final int grade;
  final IconData icon;
  final bool isSelected;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _GradeCard({
    required this.grade,
    required this.icon,
    required this.isSelected,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final shape = tier.shape;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 76,
        decoration: BoxDecoration(
          color: isSelected ? colors.primary : colors.cardBg,
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(
            color: isSelected ? colors.primaryDark : colors.topicCardBorder,
            width: isSelected ? 2 : 1,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: colors.primary.withOpacity(0.25),
                    blurRadius: 8,
                    offset: const Offset(0, 3),
                  )
                ]
              : [],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 28,
              color: isSelected ? Colors.white : KiwiColors.gemGold,
            ),
            const SizedBox(height: 6),
            Text(
              'G$grade',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: isSelected ? Colors.white : colors.textPrimary,
                fontFamily: tier.typography.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Topic card — unlocked or locked
// =============================================================================
class _TopicCard extends StatelessWidget {
  final _TopicDef topic;
  final bool unlocked;
  final int mastery; // 0–100
  final KiwiTier tier;
  final VoidCallback? onTap;

  const _TopicCard({
    required this.topic,
    required this.unlocked,
    required this.mastery,
    required this.tier,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;
    final fraction = mastery / 100.0;

    if (!unlocked) {
      // ── Locked card ──────────────────────────────────────────────
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: colors.cardBg.withOpacity(0.6),
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(color: KiwiColors.pathLocked, width: 1),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: KiwiColors.pathLocked.withOpacity(0.3),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Center(
                child: Icon(Icons.lock_rounded, size: 22, color: Colors.grey),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    topic.name,
                    style: TextStyle(
                      fontSize: typo.bodySize,
                      fontWeight: FontWeight.w600,
                      color: colors.textMuted,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Complete earlier topics to unlock',
                    style: TextStyle(
                      fontSize: typo.chipSize - 1,
                      color: colors.textMuted.withOpacity(0.7),
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    // ── Unlocked card ────────────────────────────────────────────────────
    // Pick a gradient based on topic index
    final gradientIndex =
        _topics.indexOf(topic) % KiwiColors.topicGradients.length;
    final gradient = KiwiColors.topicGradients[gradientIndex];

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(shape.cardRadius),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(shape.cardRadius),
            border: Border.all(color: colors.topicCardBorder, width: 1),
            boxShadow: [
              BoxShadow(
                color: gradient[0].withOpacity(0.08),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              // Emoji avatar
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      gradient[0].withOpacity(0.18),
                      gradient[1].withOpacity(0.10),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(topic.emoji, style: const TextStyle(fontSize: 22)),
                ),
              ),
              const SizedBox(width: 14),
              // Title + tagline + progress
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      topic.name,
                      style: TextStyle(
                        fontSize: typo.bodySize,
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      topic.tagline,
                      style: TextStyle(
                        fontSize: typo.chipSize - 1,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    if (mastery > 0) ...[
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: SizedBox(
                          height: 5,
                          child: LinearProgressIndicator(
                            value: fraction,
                            backgroundColor: KiwiColors.backgroundDark,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(gradient[0]),
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              // Arrow or mastery badge
              if (mastery >= 60)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: KiwiColors.kiwiGreenLight,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    '$mastery%',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.kiwiGreenDark,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                )
              else
                Icon(
                  Icons.arrow_forward_ios_rounded,
                  size: 16,
                  color: colors.textMuted,
                ),
            ],
          ),
        ),
      ),
    );
  }

  // Need access to full topic list for gradient index
  static const List<_TopicDef> _topics = OlympiadScreen._topics;
}
