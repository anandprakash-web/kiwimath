import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';

enum OptionState { idle, selected, selectedCorrect, selectedWrong, disabled }

/// v3 option card — designed for 2x2 grid layout.
///
/// Compact, centered text, no letter badge clutter.
/// Inspired by competitor's clean card-per-option style.
/// Tap gives a selection-click haptic + a quick 0.96 press-scale squish.
class OptionCard extends StatefulWidget {
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
  State<OptionCard> createState() => _OptionCardState();
}

class _OptionCardState extends State<OptionCard> {
  bool _pressed = false;

  bool get _tappable =>
      (widget.state == OptionState.idle ||
          widget.state == OptionState.selected) &&
      widget.onTap != null;

  void _setPressed(bool value) {
    if (_pressed == value) return;
    setState(() => _pressed = value);
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    final text = widget.text;
    Color bg;
    Color borderColor;
    Color fg;
    double borderWidth;
    IconData? trailingIcon;
    Color? iconColor;

    switch (state) {
      case OptionState.selected:
        bg = KiwiColors.visualBlueBg;
        borderColor = KiwiColors.gemBlue;
        fg = KiwiColors.textDark;
        borderWidth = 2.5;
        break;
      case OptionState.selectedCorrect:
        bg = KiwiColors.correctBg;
        borderColor = KiwiColors.correct;
        fg = KiwiColors.textDark;
        borderWidth = 2.5;
        trailingIcon = Icons.check_circle;
        iconColor = KiwiColors.correct;
        break;
      case OptionState.selectedWrong:
        bg = KiwiColors.wrongBg;
        borderColor = KiwiColors.coral;
        fg = KiwiColors.textDark;
        borderWidth = 2.5;
        trailingIcon = Icons.cancel;
        iconColor = KiwiColors.coral;
        break;
      case OptionState.disabled:
        bg = KiwiColors.creamDark;
        borderColor = KiwiColors.pathLocked;
        fg = KiwiColors.textMuted;
        borderWidth = 1.5;
        break;
      case OptionState.idle:
        bg = KiwiColors.cardBg;
        borderColor = KiwiColors.pathLocked;
        fg = KiwiColors.textDark;
        borderWidth = 1.5;
    }

    return GestureDetector(
      onTapDown: _tappable ? (_) => _setPressed(true) : null,
      onTapUp: _tappable ? (_) => _setPressed(false) : null,
      onTapCancel: _tappable ? () => _setPressed(false) : null,
      onTap: _tappable
          ? () {
              HapticFeedback.selectionClick();
              widget.onTap?.call();
            }
          : null,
      child: AnimatedScale(
        scale: _pressed ? 0.96 : 1.0,
        duration: const Duration(milliseconds: 90),
        curve: Curves.easeOut,
        child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
        padding: const EdgeInsets.symmetric(vertical: KiwiSpacing.md + 2, horizontal: KiwiSpacing.md),
        decoration: BoxDecoration(
          color: bg,
          border: Border.all(color: borderColor, width: borderWidth),
          borderRadius: BorderRadius.circular(KiwiSpacing.lg),
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
      ),
    );
  }
}
