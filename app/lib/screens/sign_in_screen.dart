import 'package:flutter/material.dart';

import '../services/auth_service.dart';
import '../theme/kiwi_theme.dart';

/// Parent-facing sign-in screen — v7.0 Kiwimath orange + cream branding.
///
/// COPPA-compliant parent-first auth flow:
///   1. Parent gate banner ("Parents & teachers sign in here")
///   2. Auth methods: Google / Email / Phone
///   3. Privacy + Terms links required for kids' category
///
/// Kiwi mascot welcomes parents. Kids never self-register.
class SignInScreen extends StatefulWidget {
  const SignInScreen({super.key});

  @override
  State<SignInScreen> createState() => _SignInScreenState();
}

enum _AuthFlow { signIn, signUp }
enum _AuthMethod { email, phone }

class _SignInScreenState extends State<SignInScreen> {
  final AuthService _auth = AuthService();
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _otpCtrl = TextEditingController();

  _AuthFlow _flow = _AuthFlow.signIn;
  _AuthMethod _method = _AuthMethod.email;
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

  // ---------------------------------------------------------------------------
  // Auth actions
  // ---------------------------------------------------------------------------

  Future<void> _submitEmail() async {
    if (_busy) return;
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() { _busy = true; _errorMessage = null; });
    try {
      final email = _emailCtrl.text.trim();
      final password = _passwordCtrl.text;
      if (_flow == _AuthFlow.signIn) {
        await _auth.signInWithEmail(email: email, password: password);
      } else {
        await _auth.signUpWithEmail(email: email, password: password);
      }
    } catch (e) {
      setState(() => _errorMessage = AuthService.humanMessage(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _signInWithGoogle() async {
    if (_busy) return;
    setState(() { _busy = true; _errorMessage = null; });
    try {
      final user = await _auth.signInWithGoogle();
      if (user == null && mounted) setState(() => _busy = false);
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
    final fullPhone = phone.startsWith('+') ? phone : '+91$phone';
    setState(() { _busy = true; _errorMessage = null; });
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
        if (mounted) setState(() => _busy = false);
      },
      onError: (message) {
        if (mounted) {
          setState(() { _errorMessage = message; _busy = false; });
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
    setState(() { _busy = true; _errorMessage = null; });
    try {
      await _auth.verifyOtp(
        verificationId: _verificationId!,
        smsCode: code,
      );
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

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 12),

                  // Kiwi mascot — hero illustration placeholder
                  // TODO: Replace with actual Kiwi character asset
                  Container(
                    alignment: Alignment.center,
                    child: Container(
                      width: 88,
                      height: 88,
                      decoration: const BoxDecoration(
                        color: KiwiColors.kiwiPrimaryLight,
                        shape: BoxShape.circle,
                      ),
                      child: const Center(
                        child: Text('\u{1F95D}', style: TextStyle(fontSize: 44)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // App name
                  const Text(
                    'Kiwimath',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.w800,
                      color: KiwiColors.kiwiPrimaryDark,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Math that grows with your child',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: KiwiColors.textMid,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Parent gate banner
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF8E1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFFFFE082), width: 1),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.shield_outlined, size: 18, color: Colors.amber.shade800),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Parents & teachers sign in here.\nKids play after you set up their profile.',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.amber.shade900,
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Sign-in / Sign-up toggle
                  _buildFlowToggle(),
                  const SizedBox(height: 20),

                  // Google Sign-In
                  _GoogleSignInButton(busy: _busy, onPressed: _signInWithGoogle),
                  const SizedBox(height: 16),

                  // Divider
                  const _DividerWithLabel(label: 'or use'),
                  const SizedBox(height: 16),

                  // Method tabs (Email / Phone)
                  _buildMethodTabs(),
                  const SizedBox(height: 16),

                  // Auth form
                  if (_method == _AuthMethod.phone)
                    _buildPhoneForm()
                  else
                    _buildEmailForm(),

                  // Error display
                  if (_errorMessage != null) ...[
                    const SizedBox(height: 12),
                    _buildErrorBox(),
                  ],

                  const SizedBox(height: 32),

                  // Legal links (required for kids' app category)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _legalLink('Privacy Policy'),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 8),
                        child: Text('\u{2022}', style: TextStyle(color: KiwiColors.textMuted, fontSize: 10)),
                      ),
                      _legalLink('Terms of Service'),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Made with \u{2764}\u{FE0F} for curious kids',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 11, color: KiwiColors.textMuted),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Sub-widgets
  // ---------------------------------------------------------------------------

  Widget _buildFlowToggle() {
    return Container(
      decoration: BoxDecoration(
        color: KiwiColors.kiwiPrimaryLight,
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.all(4),
      child: Row(
        children: [
          Expanded(child: _flowButton(_AuthFlow.signIn, 'Sign in')),
          Expanded(child: _flowButton(_AuthFlow.signUp, 'Create account')),
        ],
      ),
    );
  }

  Widget _flowButton(_AuthFlow target, String label) {
    final selected = _flow == target;
    return GestureDetector(
      onTap: _busy ? null : () => setState(() {
        _flow = target;
        _errorMessage = null;
      }),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: selected ? Colors.white : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          boxShadow: selected
              ? [const BoxShadow(color: Colors.black12, blurRadius: 4, offset: Offset(0, 2))]
              : null,
        ),
        child: Text(
          label,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 13,
            color: selected ? KiwiColors.kiwiPrimaryDark : KiwiColors.textMid,
          ),
        ),
      ),
    );
  }

  Widget _buildMethodTabs() {
    return Row(
      children: [
        _methodTab(_AuthMethod.email, Icons.email_outlined, 'Email'),
        const SizedBox(width: 10),
        _methodTab(_AuthMethod.phone, Icons.phone_outlined, 'Phone'),
      ],
    );
  }

  Widget _methodTab(_AuthMethod target, IconData icon, String label) {
    final selected = _method == target;
    return Expanded(
      child: GestureDetector(
        onTap: _busy ? null : () => setState(() {
          _method = target;
          _errorMessage = null;
          _otpSent = false;
          _verificationId = null;
        }),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: selected ? KiwiColors.kiwiPrimaryLight : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? KiwiColors.kiwiPrimary.withOpacity(0.3) : Colors.black12,
              width: 1,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 16, color: selected ? KiwiColors.kiwiPrimaryDark : KiwiColors.textMuted),
              const SizedBox(width: 6),
              Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: selected ? KiwiColors.kiwiPrimaryDark : KiwiColors.textMid,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmailForm() {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            autofillHints: const [AutofillHints.email],
            decoration: InputDecoration(
              labelText: 'Email',
              prefixIcon: const Icon(Icons.email_outlined),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey.shade300),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: KiwiColors.kiwiPrimary, width: 2),
              ),
            ),
            validator: (v) {
              if (v == null || v.trim().isEmpty) return 'Email is required';
              if (!v.contains('@')) return 'Enter a valid email';
              return null;
            },
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _passwordCtrl,
            obscureText: true,
            textInputAction: TextInputAction.done,
            autofillHints: const [AutofillHints.password],
            onFieldSubmitted: (_) => _submitEmail(),
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outline),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey.shade300),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: KiwiColors.kiwiPrimary, width: 2),
              ),
            ),
            validator: (v) {
              if (v == null || v.isEmpty) return 'Password is required';
              if (_flow == _AuthFlow.signUp && v.length < 6) return 'At least 6 characters';
              return null;
            },
          ),
          if (_flow == _AuthFlow.signIn) ...[
            const SizedBox(height: 6),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: _busy ? null : _resetPassword,
                child: Text(
                  'Forgot password?',
                  style: TextStyle(
                    fontSize: 12,
                    color: KiwiColors.textMuted,
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ),
          ],
          const SizedBox(height: 14),
          ElevatedButton(
            onPressed: _busy ? null : _submitEmail,
            style: ElevatedButton.styleFrom(
              backgroundColor: KiwiColors.kiwiPrimary,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: _busy
                ? const SizedBox(
                    height: 20, width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : Text(
                    _flow == _AuthFlow.signIn ? 'Sign in' : 'Create account',
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                  ),
          ),
        ],
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
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: KiwiColors.kiwiPrimary, width: 2),
            ),
            enabled: !_otpSent,
          ),
        ),
        if (_otpSent) ...[
          const SizedBox(height: 14),
          TextFormField(
            controller: _otpCtrl,
            keyboardType: TextInputType.number,
            textInputAction: TextInputAction.done,
            maxLength: 6,
            onFieldSubmitted: (_) => _verifyOtp(),
            decoration: InputDecoration(
              labelText: 'OTP Code',
              hintText: '123456',
              prefixIcon: const Icon(Icons.sms_outlined),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey.shade300),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: KiwiColors.kiwiPrimary, width: 2),
              ),
              counterText: '',
            ),
          ),
        ],
        const SizedBox(height: 14),
        ElevatedButton(
          onPressed: _busy ? null : (_otpSent ? _verifyOtp : _sendOtp),
          style: ElevatedButton.styleFrom(
            backgroundColor: KiwiColors.kiwiPrimary,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
          child: _busy
              ? const SizedBox(
                  height: 20, width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : Text(
                  _otpSent ? 'Verify OTP' : 'Send OTP',
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                ),
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
            child: const Text('Change number', style: TextStyle(color: KiwiColors.textMid)),
          ),
      ],
    );
  }

  Widget _buildErrorBox() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: KiwiColors.wrongBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: KiwiColors.wrong),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: KiwiColors.wrong, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _errorMessage!,
              style: const TextStyle(color: Color(0xFFBF360C), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _legalLink(String text) {
    return GestureDetector(
      onTap: () {
        // TODO: Open privacy/terms URL
      },
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11,
          color: KiwiColors.textMuted,
          decoration: TextDecoration.underline,
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Google Sign-In button — uses official asset or standard rendering
// ---------------------------------------------------------------------------

class _GoogleSignInButton extends StatelessWidget {
  final bool busy;
  final VoidCallback onPressed;
  const _GoogleSignInButton({required this.busy, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: busy ? null : onPressed,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade300, width: 1),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // TODO: Replace with Image.asset('assets/images/g-logo.png')
              // from Google's official brand guidelines.
              // Using material icon as placeholder until asset is added.
              Icon(Icons.g_mobiledata, size: 24, color: Colors.blue.shade700),
              const SizedBox(width: 10),
              const Text(
                'Continue with Google',
                style: TextStyle(
                  fontSize: 15,
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

// ---------------------------------------------------------------------------
// Divider
// ---------------------------------------------------------------------------

class _DividerWithLabel extends StatelessWidget {
  final String label;
  const _DividerWithLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(child: Divider(color: Colors.black12)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Text(
            label,
            style: const TextStyle(color: KiwiColors.textMuted, fontSize: 12),
          ),
        ),
        const Expanded(child: Divider(color: Colors.black12)),
      ],
    );
  }
}
