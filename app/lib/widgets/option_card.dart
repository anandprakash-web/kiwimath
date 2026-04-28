import 'package:flutter/material.dart';

import '../theme/kiwi_theme.dart';

enum OptionState { idle, selected, selectedCorrect, selectedWrong, disabled }

/// v2 option card — compact, with letter badge (A/B/C/D).
class OptionCard extends StatelessWidget {
  final String text;
  final int index;
  final OptionState state;
  final VoidCallback? onTap;

  const OptionCard({
    super.key,
    required this.text,
    required this.index,
    required this.state,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color borderColor;
    Color fg;
    Color badgeBg;
    Color badgeFg;
    Color badgeBorder;

    // Badge color palette — each option gets a fun color
    const badgeIdleColors = [
      Color(0xFF448AFF), // A: blue
      Color(0xFFFF6D00), // B: orange
      Color(0xFF00C853), // C: green
      Color(0xFFAA00FF), // D: purple
    ];
    final idleBadgeColor = badgeIdleColors[index % badgeIdleColors.length];

    switch (state) {
      case OptionState.selected:
        bg = const Color(0xFFE3F2FD);
        borderColor = const Color(0xFF448AFF);
        fg = KiwiColors.textDark;
        badgeBg = const Color(0xFF448AFF);
        badgeFg = Colors.white;
        badgeBorder = const Color(0xFF448AFF);
        break;
      case OptionState.selectedCorrect:
        bg = const Color(0xFFE8F5E9);
        borderColor = const Color(0xFF00C853);
        fg = KiwiColors.textDark;
        badgeBg = const Color(0xFF00C853);
        badgeFg = Colors.white;
        badgeBorder = const Color(0xFF00C853);
        break;
      case OptionState.selectedWrong:
        bg = const Color(0xFFFFEBEE);
        borderColor = const Color(0xFFFF5252);
        fg = KiwiColors.textDark;
        badgeBg = const Color(0xFFFF5252);
        badgeFg = Colors.white;
        badgeBorder = const Color(0xFFFF5252);
        break;
      case OptionState.disabled:
        bg = Colors.grey.shade50;
        borderColor = Colors.grey.shade200;
        fg = Colors.grey.shade400;
        badgeBg = Colors.grey.shade100;
        badgeFg = Colors.grey.shade400;
        badgeBorder = Colors.grey.shade200;
        break;
      case OptionState.idle:
        bg = KiwiColors.cardBg;
        borderColor = idleBadgeColor.withOpacity(0.2);
        fg = KiwiColors.textDark;
        badgeBg = idleBadgeColor.withOpacity(0.1);
        badgeFg = idleBadgeColor;
        badgeBorder = idleBadgeColor.withOpacity(0.3);
    }

    final letter = String.fromCharCode(65 + index); // A, B, C, D

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        child: Material(
          color: bg,
          borderRadius: BorderRadius.circular(14),
          elevation: state == OptionState.idle ? 2 : 0,
          shadowColor: idleBadgeColor.withOpacity(0.15),
          child: InkWell(
            borderRadius: BorderRadius.circular(12),
            onTap: (state == OptionState.idle || state == OptionState.selected)
                ? onTap
                : null,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              decoration: BoxDecoration(
                border: Border.all(color: borderColor, width: 2),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: badgeBg,
                      shape: BoxShape.circle,
                      border: Border.all(color: badgeBorder, width: 1.5),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      letter,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: badgeFg,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      text,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        color: fg,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
