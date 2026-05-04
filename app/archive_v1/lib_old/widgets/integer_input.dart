import 'package:flutter/material.dart';

import '../theme/kiwi_theme.dart';

/// Kid-friendly number input widget with a custom number pad.
///
/// Used for "integer" interaction mode questions where the child
/// types a numeric answer instead of selecting from MCQ options.
class IntegerInput extends StatefulWidget {
  /// Whether to show a negative sign button (for G4+ students).
  final bool allowNegative;

  /// Callback when the child taps "Check".
  final ValueChanged<int> onSubmit;

  const IntegerInput({
    super.key,
    this.allowNegative = false,
    required this.onSubmit,
  });

  @override
  State<IntegerInput> createState() => _IntegerInputState();
}

class _IntegerInputState extends State<IntegerInput> {
  String _input = '';

  void _onDigit(String digit) {
    setState(() {
      if (_input.length < 8) {
        _input += digit;
      }
    });
  }

  void _onBackspace() {
    setState(() {
      if (_input.isNotEmpty) {
        _input = _input.substring(0, _input.length - 1);
      }
    });
  }

  void _onNegative() {
    setState(() {
      if (_input.startsWith('-')) {
        _input = _input.substring(1);
      } else {
        _input = '-$_input';
      }
    });
  }

  void _onCheck() {
    if (_input.isEmpty || _input == '-') return;
    final value = int.tryParse(_input);
    if (value != null) {
      widget.onSubmit(value);
    }
  }

  bool get _canSubmit {
    if (_input.isEmpty || _input == '-') return false;
    return int.tryParse(_input) != null;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Display field
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 20),
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: _input.isNotEmpty
                  ? KiwiColors.kiwiGreen
                  : const Color(0xFFE0E0E0),
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
          child: Text(
            _input.isEmpty ? '?' : _input,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.w800,
              color: _input.isEmpty
                  ? const Color(0xFFBDBDBD)
                  : KiwiColors.textDark,
              letterSpacing: 2,
            ),
          ),
        ),

        // Number pad grid
        _buildNumberPad(),

        const SizedBox(height: 12),

        // Check button
        SizedBox(
          width: double.infinity,
          child: _canSubmit
              ? DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF4CAF50), Color(0xFF2E7D32)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: KiwiColors.kiwiGreen.withOpacity(0.35),
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: ElevatedButton(
                    onPressed: _onCheck,
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
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Check'),
                  ),
                )
              : ElevatedButton(
                  onPressed: null,
                  style: ElevatedButton.styleFrom(
                    disabledBackgroundColor:
                        KiwiColors.kiwiGreen.withOpacity(0.08),
                    disabledForegroundColor:
                        KiwiColors.kiwiGreen.withOpacity(0.35),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    textStyle: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: const Text('Type your answer'),
                ),
        ),
      ],
    );
  }

  Widget _buildNumberPad() {
    // 3-column grid: 1-9, then bottom row varies
    final rows = <List<_PadKey>>[
      [_PadKey('1'), _PadKey('2'), _PadKey('3')],
      [_PadKey('4'), _PadKey('5'), _PadKey('6')],
      [_PadKey('7'), _PadKey('8'), _PadKey('9')],
      [
        widget.allowNegative
            ? _PadKey.icon(Icons.remove, _onNegative)
            : _PadKey.empty(),
        _PadKey('0'),
        _PadKey.icon(Icons.backspace_outlined, _onBackspace),
      ],
    ];

    return Column(
      children: rows.map((row) {
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: row.map((key) {
              return Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: _buildKey(key),
                ),
              );
            }).toList(),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildKey(_PadKey key) {
    if (key.isEmpty) return const SizedBox(height: 52);

    return GestureDetector(
      onTap: key.onTap ?? () => _onDigit(key.label!),
      child: Container(
        height: 52,
        decoration: BoxDecoration(
          color: key.isIcon
              ? const Color(0xFFF5F5F5)
              : KiwiColors.kiwiGreenLight,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: key.isIcon
                ? const Color(0xFFE0E0E0)
                : KiwiColors.kiwiGreen.withOpacity(0.3),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Center(
          child: key.isIcon
              ? Icon(key.icon, size: 22, color: KiwiColors.textDark)
              : Text(
                  key.label!,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
        ),
      ),
    );
  }
}

class _PadKey {
  final String? label;
  final IconData? icon;
  final VoidCallback? onTap;
  final bool isEmpty;

  _PadKey(this.label)
      : icon = null,
        onTap = null,
        isEmpty = false;

  _PadKey.icon(this.icon, this.onTap)
      : label = null,
        isEmpty = false;

  _PadKey.empty()
      : label = null,
        icon = null,
        onTap = null,
        isEmpty = true;

  bool get isIcon => icon != null;
}
