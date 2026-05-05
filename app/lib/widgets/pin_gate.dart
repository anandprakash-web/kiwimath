import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/kiwi_theme.dart';

/// PIN-based parental gate — 4-digit numeric PIN stored locally.
///
/// First time: user sets a PIN. Subsequent times: user enters PIN to unlock.
/// PIN is stored in SharedPreferences. No math question needed.
class PinGate {
  static const _pinKey = 'kiwimath_parent_pin';

  /// Check if a PIN has been set.
  static Future<bool> hasPinSet() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_pinKey) != null;
  }

  /// Show the PIN gate dialog. Returns `true` if verified, `false` otherwise.
  static Future<bool> show(BuildContext context) async {
    final prefs = await SharedPreferences.getInstance();
    final savedPin = prefs.getString(_pinKey);

    if (savedPin == null) {
      // First time — set a new PIN
      return await _showSetPinDialog(context, prefs);
    } else {
      // Verify existing PIN
      return await _showEnterPinDialog(context, savedPin);
    }
  }

  static Future<bool> _showSetPinDialog(
      BuildContext context, SharedPreferences prefs) async {
    final result = await showDialog<String>(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => const _SetPinDialog(),
    );
    if (result != null && result.length == 4) {
      await prefs.setString(_pinKey, result);
      return true;
    }
    return false;
  }

  static Future<bool> _showEnterPinDialog(
      BuildContext context, String savedPin) async {
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => _EnterPinDialog(savedPin: savedPin),
    );
    return result ?? false;
  }
}

// ---------------------------------------------------------------------------
// Set PIN dialog (first time)
// ---------------------------------------------------------------------------
class _SetPinDialog extends StatefulWidget {
  const _SetPinDialog();

  @override
  State<_SetPinDialog> createState() => _SetPinDialogState();
}

class _SetPinDialogState extends State<_SetPinDialog> {
  String _pin = '';
  String _confirmPin = '';
  bool _isConfirming = false;
  bool _showError = false;

  void _onDigitTap(String digit) {
    setState(() {
      _showError = false;
      if (!_isConfirming) {
        if (_pin.length < 4) _pin += digit;
        if (_pin.length == 4) {
          // Auto-advance to confirm
          Future.delayed(const Duration(milliseconds: 300), () {
            if (mounted) setState(() => _isConfirming = true);
          });
        }
      } else {
        if (_confirmPin.length < 4) _confirmPin += digit;
        if (_confirmPin.length == 4) {
          // Check match
          Future.delayed(const Duration(milliseconds: 300), () {
            if (!mounted) return;
            if (_pin == _confirmPin) {
              Navigator.of(context).pop(_pin);
            } else {
              setState(() {
                _showError = true;
                _confirmPin = '';
              });
            }
          });
        }
      }
    });
  }

  void _onBackspace() {
    setState(() {
      _showError = false;
      if (_isConfirming) {
        if (_confirmPin.isNotEmpty) {
          _confirmPin = _confirmPin.substring(0, _confirmPin.length - 1);
        } else {
          _isConfirming = false;
          _pin = '';
        }
      } else {
        if (_pin.isNotEmpty) {
          _pin = _pin.substring(0, _pin.length - 1);
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final currentPin = _isConfirming ? _confirmPin : _pin;
    final title = _isConfirming ? 'Confirm your PIN' : 'Set a 4-digit PIN';
    final subtitle = _isConfirming
        ? 'Enter the same PIN again'
        : 'This keeps the Parent section private';

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 28, 24, 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Lock icon
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimaryLight,
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Icon(Icons.lock_outline_rounded,
                    size: 28, color: KiwiColors.kiwiPrimary),
              ),
            ),
            const SizedBox(height: 14),
            Text(title,
                style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.textDark)),
            const SizedBox(height: 4),
            Text(subtitle,
                style: TextStyle(
                    fontSize: 13,
                    color: KiwiColors.textMuted,
                    fontWeight: FontWeight.w500)),
            const SizedBox(height: 20),
            // PIN dots
            _buildPinDots(currentPin),
            if (_showError) ...[
              const SizedBox(height: 10),
              const Text("PINs don't match. Try again.",
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFEF5350))),
            ],
            const SizedBox(height: 20),
            // Numpad
            _buildNumpad(),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).pop(null),
              child: Text('Cancel',
                  style: TextStyle(
                      color: KiwiColors.textMuted,
                      fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPinDots(String pin) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(4, (i) {
        final filled = i < pin.length;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          margin: const EdgeInsets.symmetric(horizontal: 8),
          width: filled ? 18 : 16,
          height: filled ? 18 : 16,
          decoration: BoxDecoration(
            color: filled ? KiwiColors.kiwiPrimary : Colors.transparent,
            shape: BoxShape.circle,
            border: Border.all(
              color: filled
                  ? KiwiColors.kiwiPrimary
                  : KiwiColors.textMuted.withOpacity(0.3),
              width: 2,
            ),
          ),
        );
      }),
    );
  }

  Widget _buildNumpad() {
    const digits = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['', '0', '⌫'],
    ];
    return Column(
      children: digits.map((row) {
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: row.map((d) {
              if (d.isEmpty) return const SizedBox(width: 64);
              if (d == '⌫') {
                return _numpadButton(
                  child: const Icon(Icons.backspace_outlined,
                      size: 20, color: KiwiColors.textDark),
                  onTap: _onBackspace,
                );
              }
              return _numpadButton(
                child: Text(d,
                    style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.textDark)),
                onTap: () => _onDigitTap(d),
              );
            }).toList(),
          ),
        );
      }).toList(),
    );
  }

  Widget _numpadButton({required Widget child, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 64,
        height: 52,
        margin: const EdgeInsets.symmetric(horizontal: 6),
        decoration: BoxDecoration(
          color: const Color(0xFFF5F5F5),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Center(child: child),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Enter PIN dialog (returning user)
// ---------------------------------------------------------------------------
class _EnterPinDialog extends StatefulWidget {
  final String savedPin;
  const _EnterPinDialog({required this.savedPin});

  @override
  State<_EnterPinDialog> createState() => _EnterPinDialogState();
}

class _EnterPinDialogState extends State<_EnterPinDialog> {
  String _pin = '';
  bool _showError = false;
  int _attempts = 0;

  void _onDigitTap(String digit) {
    if (_pin.length >= 4) return;
    setState(() {
      _showError = false;
      _pin += digit;
    });
    if (_pin.length == 4) {
      Future.delayed(const Duration(milliseconds: 250), () {
        if (!mounted) return;
        if (_pin == widget.savedPin) {
          Navigator.of(context).pop(true);
        } else {
          setState(() {
            _showError = true;
            _attempts++;
            _pin = '';
          });
        }
      });
    }
  }

  void _onBackspace() {
    setState(() {
      _showError = false;
      if (_pin.isNotEmpty) {
        _pin = _pin.substring(0, _pin.length - 1);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 28, 24, 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimaryLight,
                shape: BoxShape.circle,
              ),
              child: const Center(
                child: Icon(Icons.lock_outline_rounded,
                    size: 28, color: KiwiColors.kiwiPrimary),
              ),
            ),
            const SizedBox(height: 14),
            const Text('Enter Parent PIN',
                style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.textDark)),
            const SizedBox(height: 4),
            Text('4-digit PIN to access Parent section',
                style: TextStyle(
                    fontSize: 13,
                    color: KiwiColors.textMuted,
                    fontWeight: FontWeight.w500)),
            const SizedBox(height: 20),
            // PIN dots
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(4, (i) {
                final filled = i < _pin.length;
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  margin: const EdgeInsets.symmetric(horizontal: 8),
                  width: filled ? 18 : 16,
                  height: filled ? 18 : 16,
                  decoration: BoxDecoration(
                    color: filled
                        ? (_showError
                            ? const Color(0xFFEF5350)
                            : KiwiColors.kiwiPrimary)
                        : Colors.transparent,
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: _showError
                          ? const Color(0xFFEF5350)
                          : (filled
                              ? KiwiColors.kiwiPrimary
                              : KiwiColors.textMuted.withOpacity(0.3)),
                      width: 2,
                    ),
                  ),
                );
              }),
            ),
            if (_showError) ...[
              const SizedBox(height: 10),
              Text(
                _attempts >= 3
                    ? 'Too many attempts. Ask a parent!'
                    : 'Wrong PIN. Try again.',
                style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFFEF5350)),
              ),
            ],
            const SizedBox(height: 20),
            // Numpad
            _buildNumpad(),
            const SizedBox(height: 8),
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text('Cancel',
                  style: TextStyle(
                      color: KiwiColors.textMuted,
                      fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNumpad() {
    const digits = [
      ['1', '2', '3'],
      ['4', '5', '6'],
      ['7', '8', '9'],
      ['', '0', '⌫'],
    ];
    return Column(
      children: digits.map((row) {
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: row.map((d) {
              if (d.isEmpty) return const SizedBox(width: 64);
              if (d == '⌫') {
                return _numpadBtn(
                  child: const Icon(Icons.backspace_outlined,
                      size: 20, color: KiwiColors.textDark),
                  onTap: _onBackspace,
                );
              }
              return _numpadBtn(
                child: Text(d,
                    style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.textDark)),
                onTap: () => _onDigitTap(d),
              );
            }).toList(),
          ),
        );
      }).toList(),
    );
  }

  Widget _numpadBtn({required Widget child, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 64,
        height: 52,
        margin: const EdgeInsets.symmetric(horizontal: 6),
        decoration: BoxDecoration(
          color: const Color(0xFFF5F5F5),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Center(child: child),
      ),
    );
  }
}
