import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';
import 'olympiad_screen.dart';
import 'worksheet_list_screen.dart';
import 'downloads_screen.dart';
import 'wavebook_screen.dart';

/// Combined Olympiad tab — top shelf with sub-tabs:
///   Practice | DPP | Worksheet (G3+ only) | Saved
///
/// - Practice: Smart adaptive practice with topic unlocking
/// - DPP: Daily Practice Problems (previously "Worksheets") — olympiad worksheets
/// - Worksheet: Live class wavebook MCQs (G3-6 only, L3 for G3-4, L4 for G5-6)
/// - Saved: Downloads / offline management
class OlympiadTabScreen extends StatefulWidget {
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;
  final void Function(String topicId, String topicName) onStartPractice;
  final Map<String, int> topicMastery;

  const OlympiadTabScreen({
    super.key,
    required this.selectedGrade,
    required this.onGradeChanged,
    required this.onStartPractice,
    this.topicMastery = const {},
  });

  @override
  State<OlympiadTabScreen> createState() => _OlympiadTabScreenState();
}

class _OlympiadTabScreenState extends State<OlympiadTabScreen> {
  int _subTab = 0; // 0=Practice, 1=DPP, 2=Worksheet, 3=Saved

  bool get _showWorksheetTab => widget.selectedGrade >= 3;

  /// Map visible tab index to logical tab index.
  /// For G1-2: 0=Practice, 1=DPP, 2=Saved (no Worksheet)
  /// For G3+:  0=Practice, 1=DPP, 2=Worksheet, 3=Saved
  int get _logicalTab {
    if (_showWorksheetTab) return _subTab;
    // G1-2: skip Worksheet tab
    if (_subTab >= 2) return _subTab + 1; // 2→3 (Saved)
    return _subTab;
  }

  @override
  void didUpdateWidget(covariant OlympiadTabScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedGrade != widget.selectedGrade) {
      // Reset to Practice if currently on Worksheet and grade drops below 3
      if (!_showWorksheetTab && _subTab == 2) {
        setState(() => _subTab = 0);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;

    // Build tab list based on grade
    final tabs = <_TabDef>[
      const _TabDef('Practice', Icons.psychology_rounded),
      const _TabDef('DPP', Icons.calendar_today_rounded),
      if (_showWorksheetTab)
        const _TabDef('Worksheet', Icons.assignment_rounded),
      const _TabDef('Saved', Icons.download_rounded),
    ];

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          children: [
            // ── Top shelf segmented toggle ─────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Container(
                height: 44,
                decoration: BoxDecoration(
                  color: colors.cardBg,
                  borderRadius: BorderRadius.circular(12),
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
        return OlympiadScreen(
          selectedGrade: widget.selectedGrade,
          onGradeChanged: widget.onGradeChanged,
          onStartPractice: widget.onStartPractice,
          topicMastery: widget.topicMastery,
        );
      case 1: // DPP (was Worksheets)
        return WorksheetListScreen(
          grade: widget.selectedGrade,
          onGradeChanged: widget.onGradeChanged,
        );
      case 2: // Worksheet (wavebook, G3+ only)
        return WavebookScreen(
          selectedGrade: widget.selectedGrade,
          onGradeChanged: widget.onGradeChanged,
        );
      case 3: // Saved (Downloads)
        return DownloadsScreen(
          selectedGrade: widget.selectedGrade,
          onGradeChanged: widget.onGradeChanged,
        );
      default:
        return const SizedBox.shrink();
    }
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
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.all(3),
          decoration: BoxDecoration(
            color: selected ? colors.primary : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: colors.primary.withOpacity(0.2),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : [],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 14,
                color: selected ? Colors.white : colors.textMuted,
              ),
              const SizedBox(width: 4),
              Flexible(
                child: Text(
                  label,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: selected ? Colors.white : colors.textMuted,
                    fontFamily: typo.fontFamily,
                  ),
                ),
              ),
            ],
          ),
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
