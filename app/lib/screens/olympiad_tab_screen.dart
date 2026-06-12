import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';
import 'olympiad_screen.dart';
import 'pillar_home_screen.dart';
import 'worksheet_list_screen.dart';
import 'saved_questions_screen.dart';
import 'wavebook_screen.dart';

/// Combined Olympiad tab — top shelf with sub-tabs:
///   Practice | DPP | Worksheet | Saved
///
/// - Practice: Smart adaptive practice with topic unlocking
/// - DPP: Daily Practice Problems — olympiad worksheets
/// - Worksheet: Wavebook MCQs (L3 for G3-4, L4 for G5-6, defaults to L3 for G1-2)
/// - Saved: Downloads / offline management
class OlympiadTabScreen extends StatefulWidget {
  final String userId;
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;
  final void Function(String topicId, String topicName) onStartPractice;
  final VoidCallback? onSmartSession;
  final Map<String, int> topicMastery;

  // Greeting & stats (from _AppShell)
  final String studentName;
  final int streak;
  final int kiwiCoins;
  final int dailyProgress;
  final int dailyGoal;
  final VoidCallback? onAvatarTap;

  const OlympiadTabScreen({
    super.key,
    required this.userId,
    required this.selectedGrade,
    required this.onGradeChanged,
    required this.onStartPractice,
    this.onSmartSession,
    this.topicMastery = const {},
    this.studentName = '',
    this.streak = 0,
    this.kiwiCoins = 0,
    this.dailyProgress = 0,
    this.dailyGoal = 5,
    this.onAvatarTap,
  });

  @override
  State<OlympiadTabScreen> createState() => _OlympiadTabScreenState();
}

class _OlympiadTabScreenState extends State<OlympiadTabScreen> {
  int _subTab = 0; // 0=Practice, 1=DPP, 2=Worksheet, 3=Saved

  /// All grades show the same 4 sub-tabs for a consistent layout.
  int get _logicalTab => _subTab;

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;

    // Same 4 tabs for all grades — consistent layout
    final tabs = <_TabDef>[
      const _TabDef('Practice', Icons.psychology_rounded),
      const _TabDef('Daily', Icons.calendar_today_rounded),
      const _TabDef('Worksheets', Icons.assignment_rounded),
      const _TabDef('Saved', Icons.bookmark_rounded),
    ];

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          children: [
            // ── Greeting bar with name, streak, coins ─────────
            Padding(
              padding: EdgeInsets.fromLTRB(KiwiSpacing.lg, KiwiSpacing.sm + 2, KiwiSpacing.lg, 0),
              child: Row(
                children: [
                  // Avatar circle with initial
                  GestureDetector(
                    onTap: widget.onAvatarTap,
                    child: Container(
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [colors.primary, colors.primaryDark],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          widget.studentName.isNotEmpty
                              ? widget.studentName[0].toUpperCase()
                              : 'K',
                          style: TextStyle(
                            fontSize: typo.chipSize,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: KiwiSpacing.sm + 2),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.studentName.isNotEmpty
                              ? 'Hi, ${widget.studentName}!'
                              : 'Kiwimath',
                          style: TextStyle(
                            fontSize: typo.topicNameSize,
                            fontWeight: FontWeight.w700,
                            color: colors.textPrimary,
                          ),
                        ),
                        Text(
                          'Grade ${widget.selectedGrade}',
                          style: TextStyle(
                            fontSize: typo.chipSize - 3,
                            color: colors.textMuted,
                          ),
                        ),
                      ],
                    ),
                  ),
                  // Coins chip
                  if (widget.kiwiCoins > 0)
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: KiwiSpacing.xs),
                      decoration: BoxDecoration(
                        color: colors.cardBg,
                        borderRadius: BorderRadius.circular(tier.shape.chipRadius - 8),
                        border: Border.all(color: KiwiColors.textMuted.withOpacity(0.12)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('\u{1FA99}', style: TextStyle(fontSize: typo.chipSize - 3)),
                          SizedBox(width: KiwiSpacing.xs - 1),
                          Text(
                            '${widget.kiwiCoins}',
                            style: TextStyle(
                              fontSize: typo.chipSize - 3,
                              fontWeight: FontWeight.w700,
                              color: colors.textPrimary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  SizedBox(width: KiwiSpacing.xs + 2),
                  // Streak chip
                  if (widget.streak > 0)
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: KiwiSpacing.xs),
                      decoration: BoxDecoration(
                        color: KiwiColors.wrongBg,
                        borderRadius: BorderRadius.circular(tier.shape.chipRadius - 8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('\u{1F525}', style: TextStyle(fontSize: typo.chipSize - 2)),
                          SizedBox(width: KiwiSpacing.xs - 1),
                          Text(
                            '${widget.streak}',
                            style: TextStyle(
                              fontSize: typo.chipSize - 2,
                              fontWeight: FontWeight.w800,
                              color: colors.primaryDark,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            // ── Daily progress bar ────────────────────────────
            if (widget.dailyGoal > 0)
              Padding(
                padding: EdgeInsets.fromLTRB(KiwiSpacing.lg, KiwiSpacing.sm, KiwiSpacing.lg, 0),
                child: _DailyProgressBar(
                  progress: widget.dailyProgress,
                  goal: widget.dailyGoal,
                  colors: colors,
                ),
              ),
            // ── Top shelf segmented toggle ─────────────────────
            Padding(
              padding: EdgeInsets.fromLTRB(KiwiSpacing.lg, KiwiSpacing.sm + 2, KiwiSpacing.lg, 0),
              child: Container(
                height: 40,
                decoration: BoxDecoration(
                  color: colors.cardBg,
                  borderRadius: BorderRadius.circular(tier.shape.chipRadius - 8),
                  border: Border.all(color: colors.topicCardBorder),
                ),
                child: Row(
                  children: tabs.map((tab) {
                    final visualIndex = tabs.indexOf(tab);
                    return _tabButton(
                      visualIndex,
                      tab.label,
                      tab.icon,
                      colors,
                      typo,
                    );
                  }).toList(),
                ),
              ),
            ),

            // ── Content ─────────────────────────────────────────
            Expanded(
              child: _buildContent(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    switch (_logicalTab) {
      case 0: // Practice
        return _buildPracticeTab();
      case 1: // DPP (was Worksheets)
        return WorksheetListScreen(
          grade: widget.selectedGrade,
          onGradeChanged: widget.onGradeChanged,
        );
      case 2: // Worksheet (wavebook MCQs)
        return WavebookScreen(
          selectedGrade: widget.selectedGrade,
          onGradeChanged: widget.onGradeChanged,
        );
      case 3: // Saved (Bookmarked questions)
        return SavedQuestionsScreen(
          userId: widget.userId,
          grade: widget.selectedGrade,
        );
      default:
        return const SizedBox.shrink();
    }
  }

  /// Practice tab — now shows the 4-Pillar grid (Olympiad v2).
  Widget _buildPracticeTab() {
    return PillarHomeScreen(
      userId: widget.userId,
      selectedGrade: widget.selectedGrade,
      onGradeChanged: widget.onGradeChanged,
    );
  }

  Widget _tabButton(
    int index,
    String label,
    IconData icon,
    KiwiTierColors colors,
    KiwiTierTypography typo,
  ) {
    final selected = _subTab == index;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          setState(() => _subTab = index);
        },
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Spacer(),
            Text(
              label,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: typo.chipSize - 2,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w400,
                color: selected ? colors.primary : colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
            ),
            const Spacer(),
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              height: 2,
              decoration: BoxDecoration(
                color: selected ? colors.primary : Colors.transparent,
                borderRadius: BorderRadius.circular(1),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TabDef {
  final String label;
  final IconData icon;
  const _TabDef(this.label, this.icon);
}

/// Compact daily progress bar — shows "X/Y questions today"
class _DailyProgressBar extends StatelessWidget {
  final int progress;
  final int goal;
  final KiwiTierColors colors;
  const _DailyProgressBar({
    required this.progress,
    required this.goal,
    required this.colors,
  });

  @override
  Widget build(BuildContext context) {
    final fraction = goal > 0 ? (progress / goal).clamp(0.0, 1.0) : 0.0;
    final remaining = (goal - progress).clamp(0, goal);
    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(3),
            child: LinearProgressIndicator(
              value: fraction,
              minHeight: 4,
              backgroundColor: KiwiColors.pathLocked,
              valueColor: AlwaysStoppedAnimation<Color>(colors.primary),
            ),
          ),
        ),
        SizedBox(width: KiwiSpacing.sm),
        Text(
          remaining > 0 ? '$progress/$goal today' : 'Goal done!',
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
            color: colors.textMuted,
          ),
        ),
      ],
    );
  }
}
