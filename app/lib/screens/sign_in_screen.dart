import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../theme/kiwi_theme.dart';

/// Parent-facing sign-in screen. Supports both sign-in and sign-up modes in
/// the same form, toggled via a tab at the top.
///
/// This is parent auth. Child profile selection happens after sign-in
/// succeeds (separate screen, coming in the next iteration).
class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

enum _Mode { signIn, signUp, phone }

class _SignInScreenState extends State<SignInScreen> {
  final AuthService _auth = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _otpCtrl = TextEditingController();

  _Mode _mode = _Mode.signIn;
  bool _busy = false;
  String? _errorMessage;

  // Phone OTP state
  String? _verificationId;
  bool _otpSent = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _phoneCtrl.dispose();
    _otpCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy) return;
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _busy = true;
      _errorMessage = null;
    });
    try {
      final email = _emailCtrl.text.trim();
      final password = _passwordCtrl.text;
      if (_mode == _Mode.signIn) {
        await _auth.signInWithEmail(email: email, password: password);
      } else {
        await _auth.signUpWithEmail(email: email, password: password);
      }
      // No manual navigation — the root AuthWrapper listens to authStateChanges
      // and swaps to the question screen automatically.
    } catch (e) {
      setState(() => _errorMessage = AuthService.humanMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signInWithGoogle() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _errorMessage = null;
    });
    try {
      final user = await _auth.signInWithGoogle();
      // user == null means the user cancelled — not an error.
      if (user == null && mounted) {
        setState(() => _busy = false);
      }
      // On success, AuthWrapper auto-navigates.
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = AuthService.humanMessage(e);
          _busy = false;
        });
      }
    }
  }

  Future<void> _sendOtp() async {
    if (_busy) return;
    final phone = _phoneCtrl.text.trim();
    if (phone.isEmpty) {
      setState(() => _errorMessage = 'Enter your phone number.');
      return;
    }
    // Auto-add +91 if no country code
    final fullPhone = phone.startsWith('+') ? phone : '+91$phone';
    setState(() {
      _busy = true;
      _errorMessage = null;
    });
    await _auth.sendOtp(
      phoneNumber: fullPhone,
      onCodeSent: (verificationId) {
        if (mounted) {
          setState(() {
            _verificationId = verificationId;
            _otpSent = true;
            _busy = false;
          });
        }
      },
      onAutoVerified: (user) {
        // Auto-verified on Android — AuthWrapper handles navigation.
        if (mounted) setState(() => _busy = false);
      },
      onError: (message) {
        if (mounted) {
          setState(() {
            _errorMessage = message;
            _busy = false;
          });
        }
      },
    );
  }

  Future<void> _verifyOtp() async {
    if (_busy || _verificationId == null) return;
    final code = _otpCtrl.text.trim();
    if (code.length != 6) {
      setState(() => _errorMessage = 'Enter the 6-digit code.');
      return;
    }
    setState(() {
      _busy = true;
      _errorMessage = null;
    });
    try {
      await _auth.verifyOtp(
        verificationId: _verificationId!,
        smsCode: code,
      );
      // AuthWrapper handles navigation.
    } catch (e) {
      if (mounted) setState(() => _errorMessage = AuthService.humanMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _resetPassword() async {
    final email = _emailCtrl.text.trim();
    if (email.isEmpty) {
      setState(() => _errorMessage = 'Enter your email first.');
      return;
    }
    try {
      await _auth.sendPasswordResetEmail(email);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Password reset email sent to $email')),
      );
    } catch (e) {
      setState(() => _errorMessage = AuthService.humanMessage(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 20),
                  const Text(
                    'Kiwimath 🥝',
                    style: TextStyle(
                      fontSize: 42,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.kiwiGreenDark,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _mode == _Mode.signIn
                        ? 'Welcome back'
                        : _mode == _Mode.signUp
                            ? 'Create a parent account'
                            : 'Sign in with phone',
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 18, color: Colors.black54),
                  ),
                  const SizedBox(height: 32),
                  _GoogleButton(busy: _busy, onPressed: _signInWithGoogle),
                  const SizedBox(height: 20),
                  const _DividerWithLabel(label: 'or'),
                  const SizedBox(height: 20),
                  _buildModeToggle(),
                  const SizedBox(height: 24),
                  if (_mode == _Mode.phone)
                    _buildPhoneForm()
                  else
                  Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        TextFormField(
                          controller: _emailCtrl,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                          autofillHints: const [AutofillHints.email],
                          decoration: const InputDecoration(
                            labelText: 'Email',
                            prefixIcon: Icon(Icons.email_outlined),
                            border: OutlineInputBorder(),
                          ),
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) {
                              return 'Email is required';
                            }
                            if (!v.contains('@')) return 'Enter a valid email';
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _passwordCtrl,
                          obscureText: true,
                          textInputAction: TextInputAction.done,
                          autofillHints: const [AutofillHints.password],
                          onFieldSubmitted: (_) => _submit(),
                          decoration: const InputDecoration(
                            labelText: 'Password',
                            prefixIcon: Icon(Icons.lock_outline),
                            border: OutlineInputBorder(),
                          ),
                          validator: (v) {
                            if (v == null || v.isEmpty) {
                              return 'Password is required';
                            }
                            if (_mode == _Mode.signUp && v.length < 6) {
                              return 'At least 6 characters';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 8),
                        if (_mode == _Mode.signIn)
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton(
                              onPressed: _busy ? null : _resetPassword,
                              child: const Text('Forgot password?'),
                            ),
                          ),
                        if (_errorMessage != null) ...[
                          const SizedBox(height: 4),
                          _buildErrorBox(),
                        ],
                        const SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: _busy ? null : _submit,
                          child: _busy
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2, color: Colors.white),
                                )
                              : Text(_mode == _Mode.signIn
                                  ? 'Sign in'
                                  : 'Create account'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Your account unlocks progress tracking,\n'
                    'streak reminders, and parent reports.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 13, color: Colors.black45),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPhoneForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextFormField(
          controller: _phoneCtrl,
          keyboardType: TextInputType.phone,
          textInputAction: _otpSent ? TextInputAction.next : TextInputAction.done,
          decoration: InputDecoration(
            labelText: 'Phone number',
            hintText: '9876543210',
            prefixIcon: const Icon(Icons.phone_outlined),
            prefixText: '+91 ',
            border: const OutlineInputBorder(),
            enabled: !_otpSent,
          ),
        ),
        if (_otpSent) ...[
          const SizedBox(height: 16),
          TextFormField(
            controller: _otpCtrl,
            keyboardType: TextInputType.number,
            textInputAction: TextInputAction.done,
            maxLength: 6,
            onFieldSubmitted: (_) => _verifyOtp(),
            decoration: const InputDecoration(
              labelText: 'OTP Code',
              hintText: '123456',
              prefixIcon: Icon(Icons.sms_outlined),
              border: OutlineInputBorder(),
              counterText: '',
            ),
          ),
        ],
        if (_errorMessage != null) ...[
          const SizedBox(height: 8),
          _buildErrorBox(),
        ],
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: _busy ? null : (_otpSent ? _verifyOtp : _sendOtp),
          child: _busy
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : Text(_otpSent ? 'Verify OTP' : 'Send OTP'),
        ),
        if (_otpSent)
          TextButton(
            onPressed: _busy ? null : () {
              setState(() {
                _otpSent = false;
                _verificationId = null;
                _otpCtrl.clear();
                _errorMessage = null;
              });
            },
            child: const Text('Change number'),
          ),
      ],
    );
  }

  Widget _buildErrorBox() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFEBEE),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: KiwiColors.wrong),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: KiwiColors.wrong),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _errorMessage!,
              style: const TextStyle(color: KiwiColors.wrong),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildModeToggle() {
    return Container(
      decoration: BoxDecoration(
        color: KiwiColors.kiwiGreenLight,
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.all(4),
      child: Row(
        children: [
          Expanded(child: _toggleButton(_Mode.signIn, 'Sign in')),
          Expanded(child: _toggleButton(_Mode.signUp, 'Sign up')),
          Expanded(child: _toggleButton(_Mode.phone, 'Phone')),
        ],
      ),
    );
  }

  // ignored — see classes below
  // ---------------------------------------------------------------------
  Widget _toggleButton(_Mode target, String label) {
    final selected = _mode == target;
    return GestureDetector(
      onTap: _busy
          ? null
          : () => setState(() {
                _mode = target;
                _errorMessage = null;
                _otpSent = false;
                _verificationId = null;
              }),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected ? Colors.white : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          boxShadow: selected
              ? [
                  const BoxShadow(
                      color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))
                ]
              : null,
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: selected ? KiwiColors.kiwiGreenDark : Colors.black54,
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// "Continue with Google" button — matches Google's branding guidelines
// (white bg, light shadow, the G logo, 14pt Roboto-ish text).
// ---------------------------------------------------------------------------

class _GoogleButton extends StatelessWidget {
  final bool busy;
  final VoidCallback onPressed;
  const _GoogleButton({required this.busy, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(12),
      elevation: 2,
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: busy ? null : onPressed,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.black12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Inline G logo — a small SVG so we don't need an asset.
              const SizedBox(
                width: 22,
                height: 22,
                child: CustomPaint(painter: _GoogleGPainter()),
              ),
              const SizedBox(width: 12),
              const Text(
                'Continue with Google',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF3C4043),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Very simple "G" monogram painter — good enough for v0. Replace with the
/// real 4-color Google logo asset before public launch.
class _GoogleGPainter extends CustomPainter {
  const _GoogleGPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final r = size.width / 2;
    final center = Offset(r, r);
    final paint = Paint()
      ..color = const Color(0xFF4285F4)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
    // Simple "G" arc + bar
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: r - 2),
      -0.4,
      5.3,
      false,
      paint,
    );
    canvas.drawLine(Offset(r + 2, r), Offset(r + r - 2, r), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// ---------------------------------------------------------------------------
// Thin "— or with email —" divider
// ---------------------------------------------------------------------------

class _DividerWithLabel extends StatelessWidget {
  final String label;
  const _DividerWithLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(child: Divider(color: Colors.black26)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Text(
            label,
            style: const TextStyle(color: Colors.black45, fontSize: 12),
          ),
        ),
        const Expanded(child: Divider(color: Colors.black26)),
      ],
    );
  }
}
