import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';

/// Fill-in-the-blank input widget.
///
/// Shows a styled text field for typing the answer to a fill-up question.
/// Supports both numeric answers (e.g., "32") and symbol answers (e.g., ">", "<", "=").
class FillUpInput extends StatefulWidget {
  /// Hint text shown in the input field.
  final String hintText;

  /// Whether to show symbol buttons (<, >, =) instead of free text.
  final bool showSymbolButtons;

  /// Callback when the child taps "Check".
  final ValueChanged<String> onSubmit;

  const FillUpInput({
    super.key,
    this.hintText = 'Type your answer',
    this.showSymbolButtons = false,
    required this.onSubmit,
  });

  @override
  State<FillUpInput> createState() => _FillUpInputState();
}

class _FillUpInputState extends State<FillUpInput> {
  final _controller = TextEditingController();
  String _selectedSymbol = '';

  bool get _canSubmit {
    if (widget.showSymbolButtons) return _selectedSymbol.isNotEmpty;
    return _controller.text.trim().isNotEmpty;
  }

  String get _answer {
    if (widget.showSymbolButtons) return _selectedSymbol;
    return _controller.text.trim();
  }

  void _onCheck() {
    if (!_canSubmit) return;
    HapticFeedback.mediumImpact();
    widget.onSubmit(_answer);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Instruction banner
        Container(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [KiwiColors.visualBlueBg, KiwiColors.visualBlueBg],
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: KiwiColors.visualBlueBorder, width: 1.5),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('\u{270F}\u{FE0F}', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 8),
              Text(
                'Fill in the blank!',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.sky,
                ),
              ),
            ],
          ),
        ),

        if (widget.showSymbolButtons)
          _buildSymbolButtons()
        else
          _buildTextInput(),

        const SizedBox(height: 16),

        // Check button
        SizedBox(
          width: double.infinity,
          child: _canSubmit
              ? DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [KiwiColors.sky, KiwiColors.sky],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: KiwiColors.sky.withOpacity(0.4),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: ElevatedButton.icon(
                    onPressed: _onCheck,
                    icon: const Icon(Icons.check_circle_outline, size: 22),
                    label: const Text('Check My Answer!'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      foregroundColor: Colors.white,
                      shadowColor: Colors.transparent,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      textStyle: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                )
              : ElevatedButton(
                  onPressed: null,
                  style: ElevatedButton.styleFrom(
                    disabledBackgroundColor: KiwiColors.sky.withOpacity(0.08),
                    disabledForegroundColor: KiwiColors.sky.withOpacity(0.35),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    textStyle: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: Text(widget.hintText),
                ),
        ),
      ],
    );
  }

  Widget _buildTextInput() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: _controller.text.isNotEmpty
              ? KiwiColors.sky
              : KiwiColors.pathLocked,
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: TextField(
        controller: _controller,
        textAlign: TextAlign.center,
        style: const TextStyle(
          fontSize: 28,
          fontWeight: FontWeight.w800,
          color: KiwiColors.textDark,
          letterSpacing: 2,
        ),
        decoration: InputDecoration(
          hintText: '?',
          hintStyle: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textMuted,
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 18, horizontal: 20),
        ),
        keyboardType: TextInputType.text,
        textInputAction: TextInputAction.done,
        onChanged: (_) => setState(() {}),
        onSubmitted: (_) => _onCheck(),
      ),
    );
  }

  Widget _buildSymbolButtons() {
    const symbols = ['<', '=', '>'];
    const labels = ['Less than', 'Equal to', 'Greater than'];
    const icons = [Icons.chevron_left, Icons.drag_handle, Icons.chevron_right];

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (i) {
        final selected = _selectedSymbol == symbols[i];
        return Expanded(
          child: Padding(
            padding: EdgeInsets.only(
              left: i == 0 ? 0 : 6,
              right: i == 2 ? 0 : 6,
            ),
            child: GestureDetector(
              onTap: () {
                HapticFeedback.lightImpact();
                setState(() => _selectedSymbol = symbols[i]);
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 20),
                decoration: BoxDecoration(
                  color: selected
                      ? KiwiColors.sky.withOpacity(0.15)
                      : Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: selected
                        ? KiwiColors.sky
                        : KiwiColors.pathLocked,
                    width: selected ? 2.5 : 1.5,
                  ),
                  boxShadow: selected
                      ? [
                          BoxShadow(
                            color: KiwiColors.sky.withOpacity(0.2),
                            blurRadius: 8,
                            offset: const Offset(0, 3),
                          ),
                        ]
                      : [],
                ),
                child: Column(
                  children: [
                    Text(
                      symbols[i],
                      style: TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.w900,
                        color: selected
                            ? KiwiColors.sky
                            : KiwiColors.textMid,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      labels[i],
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: selected
                            ? KiwiColors.sky
                            : KiwiColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }),
    );
  }
}
