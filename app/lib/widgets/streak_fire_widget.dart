import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// Animated streak fire display widget.
///
/// Shows a fire emoji that scales with streak length, the day count in bold,
/// the streak tier name, and an optional streak freeze button.
/// Includes a subtle glow animation.
class StreakFireWidget extends StatefulWidget {
  final int streakCount;
  final String tierName;
  final bool compact;
  final bool showFreezeButton;
  final int freezeCount;
  final VoidCallback? onUseFreeze;

  const StreakFireWidget({
    super.key,
    required this.streakCount,
    required this.tierName,
    this.compact = false,
    this.showFreezeButton = false,
    this.freezeCount = 0,
    this.onUseFreeze,
  });

  @override
  State<StreakFireWidget> createState() => _StreakFireWidgetState();
}

class _StreakFireWidgetState extends State<StreakFireWidget>
    with SingleTickerProviderStateMixin {
  late final AnimationController _glowController;
  late final Animation<double> _glowAnimation;
  late final Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _glowController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _glowAnimation = Tween<double>(begin: 0.3, end: 0.8).animate(
      CurvedAnimation(parent: _glowController, curve: Curves.easeInOut),
    );
    _scaleAnimation = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _glowController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _glowController.dispose();
    super.dispose();
  }

  /// Fire emoji scales with streak length.
  String _fireEmoji() {
    if (widget.streakCount >= 30) return '\u{1F525}\u{1F525}\u{1F525}';
    if (widget.streakCount >= 14) return '\u{1F525}\u{1F525}';
    if (widget.streakCount >= 7) return '\u{1F525}';
    if (widget.streakCount >= 3) return '\u{2728}';
    return '\u{1F31F}';
  }

  /// Fire size scales with streak.
  double _fireSize() {
    if (widget.compact) {
      if (widget.streakCount >= 30) return 28;
      if (widget.streakCount >= 14) return 26;
      return 24;
    }
    if (widget.streakCount >= 30) return 56;
    if (widget.streakCount >= 14) return 48;
    if (widget.streakCount >= 7) return 42;
    return 36;
  }

  /// Glow color intensifies with streak.
  Color _glowColor() {
    if (widget.streakCount >= 30) return const Color(0xFFFF3D00);
    if (widget.streakCount >= 14) return const Color(0xFFFF6D00);
    if (widget.streakCount >= 7) return const Color(0xFFFF9100);
    if (widget.streakCount >= 3) return KiwiColors.streakWarm;
    return KiwiColors.amber;
  }

  String _displayTier() {
    final tier = widget.tierName.toUpperCase();
    if (widget.streakCount >= 30) return 'INFERNO \u{1F525}\u{1F525}\u{1F525}';
    if (widget.streakCount >= 14) return 'BLAZING \u{1F525}\u{1F525}';
    if (widget.streakCount >= 7) return 'ON FIRE \u{1F525}';
    if (widget.streakCount >= 3) return 'WARMING UP \u{2728}';
    if (tier.isNotEmpty) return tier;
    return 'STARTER';
  }

  @override
  Widget build(BuildContext context) {
    if (widget.compact) {
      return _buildCompact();
    }
    return _buildFull();
  }

  Widget _buildCompact() {
    return AnimatedBuilder(
      animation: _glowController,
      builder: (context, child) {
        return Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Transform.scale(
              scale: _scaleAnimation.value,
              child: Text(
                _fireEmoji(),
                style: TextStyle(fontSize: _fireSize()),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              '${widget.streakCount}',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                color: KiwiColors.textDark,
              ),
            ),
            Text(
              'days',
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: KiwiColors.textMuted,
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildFull() {
    return AnimatedBuilder(
      animation: _glowController,
      builder: (context, child) {
        return Container(
          padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 20),
          decoration: BoxDecoration(
            color: KiwiColors.cardBg,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: _glowColor().withOpacity(_glowAnimation.value * 0.3),
                blurRadius: 24,
                spreadRadius: 2,
              ),
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Animated fire
              Transform.scale(
                scale: _scaleAnimation.value,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        _glowColor().withOpacity(_glowAnimation.value * 0.2),
                        Colors.transparent,
                      ],
                    ),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    _fireEmoji(),
                    style: TextStyle(fontSize: _fireSize()),
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Day count
              Text(
                '${widget.streakCount}',
                style: const TextStyle(
                  fontSize: 42,
                  fontWeight: FontWeight.w900,
                  color: KiwiColors.textDark,
                  height: 1.0,
                ),
              ),
              const Text(
                'DAY STREAK',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.textMid,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 8),

              // Tier name
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      _glowColor().withOpacity(0.2),
                      _glowColor().withOpacity(0.1),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _displayTier(),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: _glowColor(),
                    letterSpacing: 0.5,
                  ),
                ),
              ),

              // Streak freeze button
              if (widget.showFreezeButton && widget.freezeCount > 0) ...[
                const SizedBox(height: 16),
                _buildFreezeButton(),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildFreezeButton() {
    return GestureDetector(
      onTap: widget.onUseFreeze,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: KiwiColors.teal.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: KiwiColors.teal.withOpacity(0.3),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              '\u{2744}\u{FE0F}',
              style: TextStyle(fontSize: 18),
            ),
            const SizedBox(width: 8),
            Text(
              'Streak Freeze (${widget.freezeCount})',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: KiwiColors.teal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
