import 'package:flutter/material.dart';
import '../models/companion.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';

class CelebrationScreen extends StatefulWidget {
  final int xpEarned;
  final int coinsEarned;
  final int gemsEarned;
  final int currentStreak;
  final int dailyRemaining;
  final bool fromStepDown;
  final VoidCallback onContinue;
  final int? correctCount;
  final int? totalQuestions;
  // Hero's Formula bonuses
  final int? comebackBonus;
  final int? improvementBonus;
  // Learner persona
  final String? personaName;
  final String? personaEmoji;
  // Companion
  final CompanionService? companionService;

  const CelebrationScreen({
    super.key,
    required this.xpEarned,
    this.coinsEarned = 0,
    required this.gemsEarned,
    required this.currentStreak,
    required this.dailyRemaining,
    this.fromStepDown = false,
    required this.onContinue,
    this.correctCount,
    this.totalQuestions,
    this.comebackBonus,
    this.improvementBonus,
    this.personaName,
    this.personaEmoji,
    this.companionService,
  });

  @override
  State<CelebrationScreen> createState() => _CelebrationScreenState();
}

class _CelebrationScreenState extends State<CelebrationScreen>
    with SingleTickerProviderStateMixin {
  bool _showIcon = false;
  bool _showXP = false;
  bool _showBonuses = false;

  late final AnimationController _iconController;
  late final Animation<double> _iconScale;

  @override
  void initState() {
    super.initState();

    _iconController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _iconScale = CurvedAnimation(
      parent: _iconController,
      curve: Curves.elasticOut,
    );

    Future.microtask(() {
      setState(() => _showIcon = true);
      _iconController.forward();
    });

    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) setState(() => _showXP = true);
    });

    // Show bonuses after the main card
    Future.delayed(const Duration(milliseconds: 700), () {
      if (mounted) setState(() => _showBonuses = true);
    });
  }

  @override
  void dispose() {
    _iconController.dispose();
    super.dispose();
  }

  bool get _hasHeroBonus =>
      (widget.comebackBonus != null && widget.comebackBonus! > 0) ||
      (widget.improvementBonus != null && widget.improvementBonus! > 0);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            stops: [0.0, 0.35, 0.7, 1.0],
            colors: [
              Color(0xFFE8F5E9),
              Color(0xFFB9F6CA),
              Color(0xFF69F0AE),
              Color(0xFF00E676),
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              const Spacer(flex: 2),

              // 1. Animated icon / companion
              ScaleTransition(
                scale: _iconScale,
                child: widget.companionService != null &&
                        widget.companionService!.isLoaded
                    ? CompanionView(
                        surface: CompanionSurface.gradeCeremony,
                        config: widget.companionService!.config!,
                        size: 80,
                      )
                    : Icon(
                        widget.fromStepDown ? Icons.star : Icons.celebration,
                        size: 72,
                        color: KiwiColors.gemGold,
                      ),
              ),

              const SizedBox(height: 20),

              // 2. Title
              Text(
                widget.fromStepDown ? 'You figured it out!' : 'Session complete!',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.kiwiGreenDark,
                ),
              ),

              const SizedBox(height: 10),

              // 3. Subtitle
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 36),
                child: Text(
                  widget.fromStepDown
                      ? 'You broke the problem into steps and solved each one. That\'s real mathematical thinking!'
                      : 'Great effort! Every question makes you stronger.',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Color(0xFF558B2F),
                    height: 1.5,
                  ),
                ),
              ),

              // 3b. Score display
              if (widget.correctCount != null && widget.totalQuestions != null) ...[
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.7),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.emoji_events, size: 20, color: KiwiColors.gemGold),
                      const SizedBox(width: 8),
                      Text(
                        '${widget.correctCount}/${widget.totalQuestions} correct',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: KiwiColors.kiwiGreenDark,
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 20),

              // 4. Rewards Card (animated entrance) — now with dual currency
              AnimatedOpacity(
                opacity: _showXP ? 1.0 : 0.0,
                duration: const Duration(milliseconds: 500),
                curve: Curves.easeOut,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 500),
                  curve: Curves.elasticOut,
                  transform: Matrix4.translationValues(0, _showXP ? 0 : 30, 0),
                  margin: const EdgeInsets.symmetric(horizontal: 28),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 22),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.08),
                        blurRadius: 16,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      // Kiwi Coins
                      Expanded(
                        child: _StatColumn(
                          value: '+${widget.coinsEarned}',
                          valueColor: KiwiColors.gemGold,
                          label: 'Coins',
                          icon: '\u{1FA99}',
                        ),
                      ),
                      _verticalDivider(),
                      // Mastery Gems
                      Expanded(
                        child: _StatColumn(
                          value: '+${widget.gemsEarned}',
                          valueColor: KiwiColors.gemBlue,
                          label: 'Gems',
                          icon: '\u{1F48E}',
                        ),
                      ),
                      _verticalDivider(),
                      // XP
                      Expanded(
                        child: _StatColumn(
                          value: '+${widget.xpEarned}',
                          valueColor: KiwiColors.xpPurple,
                          label: 'XP',
                          icon: '\u26A1',
                        ),
                      ),
                      _verticalDivider(),
                      // Streak
                      Expanded(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  Icons.local_fire_department,
                                  size: 22,
                                  color: KiwiColors.streakOrange,
                                ),
                                const SizedBox(width: 2),
                                Text(
                                  '${widget.currentStreak}',
                                  style: const TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.w800,
                                    color: KiwiColors.streakOrange,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${widget.currentStreak} days!',
                              style: const TextStyle(
                                fontSize: 10,
                                color: KiwiColors.textMuted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // 4b. Hero's Formula bonus callouts
              if (_hasHeroBonus) ...[
                const SizedBox(height: 10),
                AnimatedOpacity(
                  opacity: _showBonuses ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 400),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 28),
                    child: Column(
                      children: [
                        if (widget.comebackBonus != null && widget.comebackBonus! > 0)
                          _bonusPill(
                            '\u{1F9B8}',
                            'Comeback Bonus!',
                            '+${widget.comebackBonus} coins',
                            const Color(0xFFFF6D00),
                          ),
                        if (widget.improvementBonus != null && widget.improvementBonus! > 0)
                          _bonusPill(
                            '\u{1F4C8}',
                            'Improvement Bonus!',
                            '+${widget.improvementBonus} coins',
                            const Color(0xFF00C853),
                          ),
                      ],
                    ),
                  ),
                ),
              ],

              // 4c. Learner persona badge
              if (widget.personaName != null) ...[
                const SizedBox(height: 10),
                AnimatedOpacity(
                  opacity: _showBonuses ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 400),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 28),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFAA00FF), Color(0xFF7C4DFF)],
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFAA00FF).withOpacity(0.3),
                          blurRadius: 8,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          widget.personaEmoji ?? '\u{1F31F}',
                          style: const TextStyle(fontSize: 16),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          widget.personaName!,
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],

              const SizedBox(height: 16),

              // 5. Daily goal nudge
              if (widget.dailyRemaining > 0)
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 28),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.7),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '\u{1F3C6} ${widget.dailyRemaining} more questions to finish today\'s goal!',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF558B2F),
                    ),
                  ),
                ),

              const Spacer(flex: 3),

              // 6. Bottom button
              Padding(
                padding: const EdgeInsets.fromLTRB(28, 0, 28, 16),
                child: GestureDetector(
                  onTap: widget.onContinue,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.08),
                          blurRadius: 12,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: const Text(
                      'Back to home \u2192',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.kiwiGreenDark,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _bonusPill(String emoji, String title, String amount, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3), width: 1),
      ),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 18)),
          const SizedBox(width: 8),
          Text(
            title,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
          const Spacer(),
          Text(
            amount,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _verticalDivider() {
    return Container(
      width: 1,
      height: 40,
      color: Colors.grey.withValues(alpha: 0.2),
    );
  }
}

class _StatColumn extends StatelessWidget {
  final String value;
  final Color valueColor;
  final String label;
  final String? icon;

  const _StatColumn({
    required this.value,
    required this.valueColor,
    required this.label,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null) ...[
          Text(icon!, style: const TextStyle(fontSize: 16)),
          const SizedBox(height: 2),
        ],
        Text(
          value,
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: valueColor,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            color: KiwiColors.textMuted,
          ),
        ),
      ],
    );
  }
}
