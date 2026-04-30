import 'dart:math';

import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// COPPA-style parental gate — presents a multiplication problem that a
/// Grade 1-2 child can't solve (e.g. "What is 14 × 7?").
///
/// On correct answer, calls [onVerified]. On wrong answer, shows a gentle
/// "Ask your parents" message. Designed to prevent kids from accidentally
/// accessing the Parent Dashboard or settings.
class ParentalGate {
  /// Show the parental gate dialog. Returns `true` if the parent answered
  /// correctly, `false` otherwise.
  static Future<bool> show(BuildContext context) async {
    final rng = Random();
    // Generate a problem a 6-year-old can't solve: two-digit × single-digit.
    final a = rng.nextInt(9) + 12; // 12-20
    final b = rng.nextInt(7) + 3; // 3-9
    final correctAnswer = a * b;

    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => _ParentalGateDialog(
        a: a,
        b: b,
        correctAnswer: correctAnswer,
      ),
    );
    return result ?? false;
  }
}

class _ParentalGateDialog extends StatefulWidget {
  final int a;
  final int b;
  final int correctAnswer;

  const _ParentalGateDialog({
    required this.a,
    required this.b,
    required this.correctAnswer,
  });

  @override
  State<_ParentalGateDialog> createState() => _ParentalGateDialogState();
}

class _ParentalGateDialogState extends State<_ParentalGateDialog> {
  final _controller = TextEditingController();
  bool _showError = false;
  int _attempts = 0;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final input = int.tryParse(_controller.text.trim());
    if (input == widget.correctAnswer) {
      Navigator.of(context).pop(true);
    } else {
      setState(() {
        _showError = true;
        _attempts++;
        _controller.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      backgroundColor: Colors.white,
      contentPadding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Lock icon
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: const Color(0xFFE8F5E9),
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFFA5D6A7), width: 2),
            ),
            child: const Center(
              child: Icon(
                Icons.family_restroom_rounded,
                size: 28,
                color: Color(0xFF2E7D32),
              ),
            ),
          ),
          const SizedBox(height: 14),
          const Text(
            'Parent verification',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Solve this to continue:',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: KiwiColors.textMuted,
            ),
          ),
          const SizedBox(height: 16),
          // Math problem
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 16),
            decoration: BoxDecoration(
              color: const Color(0xFFF3F1EC),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: const Color(0xFFE0DDD6), width: 1.5),
            ),
            child: Center(
              child: Text(
                '${widget.a} × ${widget.b} = ?',
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.textDark,
                  letterSpacing: 2,
                ),
              ),
            ),
          ),
          const SizedBox(height: 14),
          // Answer input
          TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            textAlign: TextAlign.center,
            autofocus: true,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textDark,
            ),
            decoration: InputDecoration(
              hintText: 'Your answer',
              hintStyle: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
                color: Colors.grey.shade400,
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: _showError
                      ? const Color(0xFFEF5350)
                      : const Color(0xFFE0E0E0),
                  width: 2,
                ),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: _showError
                      ? const Color(0xFFEF5350)
                      : const Color(0xFFE0E0E0),
                  width: 2,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(
                  color: _showError
                      ? const Color(0xFFEF5350)
                      : KiwiColors.kiwiGreen,
                  width: 2,
                ),
              ),
            ),
            onSubmitted: (_) => _submit(),
          ),
          if (_showError) ...[
            const SizedBox(height: 8),
            Text(
              _attempts >= 2
                  ? 'Ask a grown-up for help!'
                  : 'That\'s not right. Try again!',
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Color(0xFFEF5350),
              ),
            ),
          ],
          const SizedBox(height: 16),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(
            'Cancel',
            style: TextStyle(
              color: KiwiColors.textMuted,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        ElevatedButton(
          onPressed: _submit,
          style: ElevatedButton.styleFrom(
            backgroundColor: KiwiColors.kiwiGreen,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          ),
          child: const Text(
            'Verify',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
        ),
      ],
    );
  }
}
