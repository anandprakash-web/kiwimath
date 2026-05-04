import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/clan.dart';
import '../theme/kiwi_theme.dart';

/// Clan join screen — invite code entry with parent gate.
///
/// Flow:
///   1. Parent gate (math question — same pattern as create screen)
///   2. Invite code input (9-char: "KIWI-XXXX", auto-uppercase, auto-dash)
///   3. Clan preview card (appears when code is fully entered)
///   4. Join button
///   5. Error states: invalid code, clan full, grade mismatch
class ClanJoinScreen extends StatefulWidget {
  final int userGrade;
  final String userUid;
  final void Function(String inviteCode) onJoin;
  final VoidCallback onBack;
  final VoidCallback? onCreateInstead;

  const ClanJoinScreen({
    super.key,
    required this.userGrade,
    required this.userUid,
    required this.onJoin,
    required this.onBack,
    this.onCreateInstead,
  });

  @override
  State<ClanJoinScreen> createState() => _ClanJoinScreenState();
}

enum _JoinPhase { parentGate, codeEntry }

enum _JoinError { none, invalidCode, clanFull, gradeMismatch }

class _ClanJoinScreenState extends State<ClanJoinScreen>
    with SingleTickerProviderStateMixin {
  // ── Parent gate ──────────────────────────────────────────────────────────
  late int _a, _b, _correctAnswer;
  final _gateController = TextEditingController();
  bool _gateWrong = false;

  // ── Code entry ───────────────────────────────────────────────────────────
  final _codeController = TextEditingController();
  final _codeFocus = FocusNode();
  _JoinPhase _phase = _JoinPhase.parentGate;
  _JoinError _error = _JoinError.none;
  bool _showPreview = false;
  bool _joining = false;

  // ── Animation ────────────────────────────────────────────────────────────
  late AnimationController _fadeCtrl;
  late Animation<double> _fadeIn;

  @override
  void initState() {
    super.initState();
    _generateGateQuestion();
    _codeController.addListener(_onCodeChanged);
    _fadeCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _fadeIn = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
    _fadeCtrl.forward();
  }

  @override
  void dispose() {
    _gateController.dispose();
    _codeController.dispose();
    _codeFocus.dispose();
    _fadeCtrl.dispose();
    super.dispose();
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

  void _generateGateQuestion() {
    final rng = Random();
    _a = rng.nextInt(9) + 2; // 2-10
    _b = rng.nextInt(9) + 2;
    _correctAnswer = _a * _b;
  }

  void _checkGate() {
    final input = int.tryParse(_gateController.text.trim());
    if (input == _correctAnswer) {
      setState(() {
        _phase = _JoinPhase.codeEntry;
        _gateWrong = false;
      });
      _fadeCtrl.reset();
      _fadeCtrl.forward();
      Future.delayed(const Duration(milliseconds: 200), () {
        _codeFocus.requestFocus();
      });
    } else {
      setState(() => _gateWrong = true);
      HapticFeedback.mediumImpact();
    }
  }

  void _onCodeChanged() {
    var text = _codeController.text.toUpperCase();

    // Auto-insert dash after "KIWI"
    if (text.length == 4 && !text.contains('-')) {
      text = '$text-';
      _codeController.value = TextEditingValue(
        text: text,
        selection: TextSelection.collapsed(offset: text.length),
      );
    }

    // Remove dash if user deletes back to < 4 chars
    if (text.length < 4 && text.contains('-')) {
      text = text.replaceAll('-', '');
      _codeController.value = TextEditingValue(
        text: text,
        selection: TextSelection.collapsed(offset: text.length),
      );
    }

    setState(() {
      _error = _JoinError.none;
      _showPreview = text.length == 9 && text.contains('-');
    });
  }

  String get _formattedCode => _codeController.text.toUpperCase();

  void _handleJoin() {
    if (_joining) return;
    setState(() => _joining = true);
    widget.onJoin(_formattedCode);
    // Parent handles async result; reset after short delay in case of error.
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) setState(() => _joining = false);
    });
  }

  // ── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: FadeTransition(
          opacity: _fadeIn,
          child: Column(
            children: [
              _buildHeader(),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: _phase == _JoinPhase.parentGate
                      ? _buildParentGate()
                      : _buildCodeEntry(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Header ───────────────────────────────────────────────────────────────

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: widget.onBack,
            icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
          ),
          const Expanded(
            child: Text(
              'Join a Clan',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: Colors.white,
                letterSpacing: 0.5,
              ),
            ),
          ),
          const SizedBox(width: 48), // balance the back button
        ],
      ),
    );
  }

  // ── Parent Gate ──────────────────────────────────────────────────────────

  Widget _buildParentGate() {
    return Padding(
      padding: const EdgeInsets.only(top: 48),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: KiwiColors.cardBg,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: [
                const Icon(Icons.lock_outline_rounded,
                    size: 40, color: KiwiColors.kiwiPrimary),
                const SizedBox(height: 12),
                const Text(
                  'Parent Check',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Ask a parent to answer this before joining a clan.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    color: KiwiColors.textMid,
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'What is $_a × $_b?',
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.textDark,
                  ),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: 120,
                  child: TextField(
                    controller: _gateController,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                    ),
                    decoration: InputDecoration(
                      hintText: '??',
                      hintStyle: TextStyle(
                        color: KiwiColors.textMuted.withOpacity(0.5),
                      ),
                      filled: true,
                      fillColor: KiwiColors.kiwiPrimaryLight,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(14),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onSubmitted: (_) => _checkGate(),
                  ),
                ),
                if (_gateWrong) ...[
                  const SizedBox(height: 12),
                  const Text(
                    'Not quite — try again!',
                    style: TextStyle(
                      color: Colors.redAccent,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _checkGate,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: KiwiColors.kiwiPrimary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      elevation: 0,
                    ),
                    child: const Text(
                      'Verify',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Code Entry ───────────────────────────────────────────────────────────

  Widget _buildCodeEntry() {
    return Padding(
      padding: const EdgeInsets.only(top: 32),
      child: Column(
        children: [
          // Instruction
          const Text(
            'Enter your clan invite code',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Ask your clan leader for the 9-character code',
            style: TextStyle(fontSize: 14, color: KiwiColors.textMid),
          ),
          const SizedBox(height: 24),

          // Code input field
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: KiwiColors.cardBg,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: [
                TextField(
                  controller: _codeController,
                  focusNode: _codeFocus,
                  textAlign: TextAlign.center,
                  textCapitalization: TextCapitalization.characters,
                  maxLength: 9,
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 4,
                    color: KiwiColors.textDark,
                  ),
                  decoration: InputDecoration(
                    hintText: 'KIWI-XXXX',
                    hintStyle: TextStyle(
                      color: KiwiColors.textMuted.withOpacity(0.4),
                      letterSpacing: 4,
                    ),
                    counterText: '',
                    filled: true,
                    fillColor: KiwiColors.kiwiPrimaryLight,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      vertical: 16,
                      horizontal: 12,
                    ),
                  ),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[A-Za-z0-9\-]')),
                    LengthLimitingTextInputFormatter(9),
                  ],
                ),
                // Error message
                if (_error != _JoinError.none) ...[
                  const SizedBox(height: 12),
                  _buildErrorBanner(),
                ],
              ],
            ),
          ),

          // Clan preview card (mock — appears when code is complete)
          if (_showPreview) ...[
            const SizedBox(height: 20),
            _buildClanPreviewCard(),
          ],

          const SizedBox(height: 28),

          // Join button
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton(
              onPressed: _showPreview && !_joining ? _handleJoin : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                disabledBackgroundColor: KiwiColors.kiwiPrimary.withOpacity(0.4),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                elevation: _showPreview ? 4 : 0,
              ),
              child: _joining
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: Colors.white,
                      ),
                    )
                  : const Text(
                      'Join Clan! \u{1F91D}',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
            ),
          ),

          const SizedBox(height: 40),
        ],
      ),
    );
  }

  // ── Clan Preview Card (mock) ─────────────────────────────────────────────

  Widget _buildClanPreviewCard() {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      curve: Curves.easeOut,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: KiwiColors.kiwiPrimary.withOpacity(0.3),
          width: 2,
        ),
        boxShadow: [
          BoxShadow(
            color: KiwiColors.kiwiPrimary.withOpacity(0.1),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          // Mock crest
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Center(
              child: Text('⚡', style: TextStyle(fontSize: 28)),
            ),
          ),
          const SizedBox(width: 14),
          // Clan info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Thunder Squad',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    _infoChip(Icons.people_alt_rounded, '8/15 members'),
                    const SizedBox(width: 10),
                    _infoChip(Icons.school_rounded, 'Grade ${widget.userGrade}'),
                  ],
                ),
              ],
            ),
          ),
          // Checkmark
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: KiwiColors.kiwiGreen.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.check_rounded,
              color: KiwiColors.kiwiGreen,
              size: 20,
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoChip(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: KiwiColors.textMuted),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: KiwiColors.textMid,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  // ── Error Banner ─────────────────────────────────────────────────────────

  Widget _buildErrorBanner() {
    String message;
    IconData icon;
    Color color;
    Widget? action;

    switch (_error) {
      case _JoinError.invalidCode:
        message = 'Invalid code — double check and try again!';
        icon = Icons.error_outline_rounded;
        color = Colors.redAccent;
        break;
      case _JoinError.clanFull:
        message = 'This clan is full (15/15)!';
        icon = Icons.group_off_rounded;
        color = KiwiColors.kiwiPrimaryDark;
        break;
      case _JoinError.gradeMismatch:
        message =
            'Grade mismatch — Start your own Grade ${widget.userGrade} clan!';
        icon = Icons.swap_horiz_rounded;
        color = KiwiColors.xpPurple;
        action = widget.onCreateInstead != null
            ? TextButton(
                onPressed: widget.onCreateInstead,
                child: const Text(
                  'Create Clan',
                  style: TextStyle(
                    color: KiwiColors.xpPurple,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              )
            : null;
        break;
      case _JoinError.none:
        return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ),
          if (action != null) action,
        ],
      ),
    );
  }

  /// Call these from the parent to show specific error states.
  void showError(_JoinError err) {
    setState(() {
      _error = err;
      _showPreview = false;
      _joining = false;
    });
  }
}
