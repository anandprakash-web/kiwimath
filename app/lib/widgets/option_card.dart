import 'package:flutter/material.dart';

import '../theme/kiwi_theme.dart';

enum OptionState { idle, selectedCorrect, selectedWrong, disabled }

/// A big, tap-friendly multiple-choice option card.
/// State transitions are driven by the parent screen.
class OptionCard extends StatelessWidget {
  final String text;
  final OptionState state;
  final VoidCallback? onTap;

  const OptionCard({
    super.key,
    required this.text,
    required this.state,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color border;
    Color fg;

    switch (state) {
      case OptionState.selectedCorrect:
        bg = KiwiColors.correct;
        border = KiwiColors.correct;
        fg = Colors.white;
        break;
      case OptionState.selectedWrong:
        bg = KiwiColors.wrong;
        border = KiwiColors.wrong;
        fg = Colors.white;
        break;
      case OptionState.disabled:
        bg = Colors.grey.shade100;
        border = Colors.grey.shade300;
        fg = Colors.grey.shade500;
        break;
      case OptionState.idle:
        bg = KiwiColors.cardBg;
        border = KiwiColors.kiwiGreenLight;
        fg = KiwiColors.textDark;
    }

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: Material(
        color: bg,
        borderRadius: BorderRadius.circular(16),
        elevation: state == OptionState.idle ? 2 : 0,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: state == OptionState.idle ? onTap : null,
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 24),
            decoration: BoxDecoration(
              border: Border.all(color: border, width: 2),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Center(
              child: Text(
                text,
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                  color: fg,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
