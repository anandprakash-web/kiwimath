import 'package:flutter/material.dart';

import '../theme/kiwi_theme.dart';

enum OptionState { idle, selected, selectedCorrect, selectedWrong, disabled }

/// v3 option card — designed for 2x2 grid layout.
///
/// Compact, centered text, no letter badge clutter.
/// Inspired by competitor's clean card-per-option style.
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
    double borderWidth;
    IconData? trailingIcon;
    Color? iconColor;

    switch (state) {
      case OptionState.selected:
        bg = const Color(0xFFE3F2FD);
        borderColor = const Color(0xFF448AFF);
        fg = KiwiColors.textDark;
        borderWidth = 2.5;
        break;
      case OptionState.selectedCorrect:
        bg = const Color(0xFFE8F5E9);
        borderColor = const Color(0xFF00C853);
        fg = KiwiColors.textDark;
        borderWidth = 2.5;
        trailingIcon = Icons.check_circle;
        iconColor = const Color(0xFF00C853);
        break;
      case OptionState.selectedWrong:
        bg = const Color(0xFFFFEBEE);
        borderColor = const Color(0xFFFF5252);
        fg = KiwiColors.textDark;
        borderWidth = 2.5;
        trailingIcon = Icons.cancel;
        iconColor = const Color(0xFFFF5252);
        break;
      case OptionState.disabled:
        bg = Colors.grey.shade50;
        borderColor = Colors.grey.shade200;
        fg = Colors.grey.shade400;
        borderWidth = 1.5;
        break;
      case OptionState.idle:
        bg = KiwiColors.cardBg;
        borderColor = const Color(0xFFE0E0E0);
        fg = KiwiColors.textDark;
        borderWidth = 1.5;
    }

    return GestureDetector(
      onTap: (state == OptionState.idle || state == OptionState.selected)
          ? onTap
          : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
        decoration: BoxDecoration(
          color: bg,
          border: Border.all(color: borderColor, width: borderWidth),
          borderRadius: BorderRadius.circular(16),
          boxShadow: state == OptionState.idle
              ? [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.04),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Center(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Flexible(
                child: Text(
                  text,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: fg,
                    height: 1.3,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (trailingIcon != null) ...[
                const SizedBox(width: 6),
                Icon(trailingIcon, size: 20, color: iconColor),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
