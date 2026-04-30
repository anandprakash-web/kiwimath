import 'package:flutter/material.dart';

import '../models/question_v2.dart';
import '../theme/kiwi_theme.dart';

/// Premium 3-level Socratic hint system.
///
///   Level 1: Gentle nudge — re-read, look again
///   Level 2: Think deeper — Socratic question, scaffold
///   Level 3: Almost the answer — guided reveal, teach
///
/// "Hint = Ask better question, NOT give answer."
class HintLadderBar extends StatefulWidget {
  final HintLadder hintLadder;

  /// Called when the user reveals a new hint level (0-2).
  final ValueChanged<int>? onHintRevealed;

  /// Start with this level already revealed (-1 = none, 0-2).
  final int initialLevel;

  const HintLadderBar({
    super.key,
    required this.hintLadder,
    this.onHintRevealed,
    this.initialLevel = -1,
  });

  @override
  State<HintLadderBar> createState() => _HintLadderBarState();
}

class _HintLadderBarState extends State<HintLadderBar>
    with TickerProviderStateMixin {
  /// -1 = no hint shown yet, 0-2 = current level revealed
  int _currentLevel = -1;

  late AnimationController _pulseController;
  late AnimationController _revealController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _revealAnimation;

  // 3-level colors
  static const _levelColors = [
    [Color(0xFF81D4FA), Color(0xFF039BE5)], // L1: sky blue
    [Color(0xFFFFCC80), Color(0xFFFF9800)], // L2: warm amber
    [Color(0xFFCE93D8), Color(0xFFAB47BC)], // L3: purple
  ];

  static const _levelEmoji = [
    '\u{1F33F}', // L1: seedling — gentle nudge
    '\u{1F914}', // L2: thinking — deeper thought
    '\u{1F4A1}', // L3: lightbulb — guided reveal
  ];

  static const _levelLabels = [
    'Take a breath',
    'Think about this',
    'Here\'s a big clue',
  ];

  @override
  void initState() {
    super.initState();
    _currentLevel = widget.initialLevel;

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.9, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _revealController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );

    _revealAnimation = CurvedAnimation(
      parent: _revealController,
      curve: Curves.easeOutBack,
    );

    // If resuming from a previously revealed level, show it immediately
    if (_currentLevel >= 0) {
      _revealController.value = 1.0;
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _revealController.dispose();
    super.dispose();
  }

  void _revealNextHint() {
    if (_currentLevel >= 2) return; // max 3 levels (0, 1, 2)

    setState(() {
      _currentLevel++;
    });

    _revealController.reset();
    _revealController.forward();

    widget.onHintRevealed?.call(_currentLevel);
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Progress dots — 3 dots
        _buildProgressDots(),
        const SizedBox(height: 10),

        // Current hint card (or "need a hint?" button)
        if (_currentLevel < 0)
          _buildNeedHintButton()
        else
          _buildHintCard(),

        // "Next hint" button (if more hints available)
        if (_currentLevel >= 0 && _currentLevel < 2) ...[
          const SizedBox(height: 8),
          _buildNextHintButton(),
        ],
      ],
    );
  }

  Widget _buildProgressDots() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (i) {
        final isRevealed = i <= _currentLevel;
        final isCurrent = i == _currentLevel;
        final colors = _levelColors[i];

        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          width: isCurrent ? 28 : 12,
          height: 12,
          decoration: BoxDecoration(
            gradient: isRevealed
                ? LinearGradient(colors: colors)
                : null,
            color: isRevealed ? null : const Color(0xFFE0E0E0),
            borderRadius: BorderRadius.circular(6),
            boxShadow: isCurrent
                ? [
                    BoxShadow(
                      color: colors[0].withOpacity(0.5),
                      blurRadius: 6,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : null,
          ),
        );
      }),
    );
  }

  Widget _buildNeedHintButton() {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: _pulseAnimation.value,
          child: child,
        );
      },
      child: GestureDetector(
        onTap: _revealNextHint,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF81D4FA), Color(0xFF039BE5)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF039BE5).withOpacity(0.3),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('\u{1F95D}', style: TextStyle(fontSize: 20)),
              SizedBox(width: 8),
              Text(
                'Need a hint?',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                ),
              ),
              SizedBox(width: 4),
              Icon(Icons.arrow_forward_ios, size: 14, color: Colors.white70),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHintCard() {
    final level = _currentLevel.clamp(0, 2);
    final colors = _levelColors[level];
    final hintText = widget.hintLadder.forLevel3(level);
    final emoji = _levelEmoji[level];
    final label = _levelLabels[level];

    return AnimatedBuilder(
      animation: _revealAnimation,
      builder: (context, child) {
        return FadeTransition(
          opacity: _revealAnimation,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.2),
              end: Offset.zero,
            ).animate(_revealAnimation),
            child: child,
          ),
        );
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              colors[0].withOpacity(0.15),
              colors[1].withOpacity(0.08),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: colors[0].withOpacity(0.4),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: colors[0].withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 3),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row: emoji + label + level badge
            Row(
              children: [
                Text(emoji, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    label,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: colors[1],
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 3,
                  ),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(colors: colors),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    'Hint ${level + 1}/3',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Hint text
            Text(
              hintText,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: KiwiColors.textDark,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNextHintButton() {
    final nextLevel = (_currentLevel + 1).clamp(0, 2);
    final nextColors = _levelColors[nextLevel];
    final remaining = 2 - _currentLevel;

    return GestureDetector(
      onTap: _revealNextHint,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: nextColors[0].withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: nextColors[0].withOpacity(0.25),
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.add_circle_outline,
              size: 16,
              color: nextColors[1],
            ),
            const SizedBox(width: 6),
            Text(
              remaining > 1 ? 'More help ($remaining left)' : 'One more hint',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: nextColors[1],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Compact hint button to place near the question stem.
/// Tapping opens the full hint ladder in a bottom sheet.
class HintButton extends StatefulWidget {
  final HintLadder hintLadder;
  final ValueChanged<int>? onHintRevealed;

  const HintButton({
    super.key,
    required this.hintLadder,
    this.onHintRevealed,
  });

  @override
  State<HintButton> createState() => _HintButtonState();
}

class _HintButtonState extends State<HintButton> {
  /// Track max revealed level across bottom sheet open/close cycles
  int _maxRevealedLevel = -1;

  @override
  Widget build(BuildContext context) {
    final hasRevealed = _maxRevealedLevel >= 0;

    return GestureDetector(
      onTap: () => _showHintSheet(context),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: hasRevealed
                ? [const Color(0xFFE1F5FE), const Color(0xFFB3E5FC)]
                : [const Color(0xFFB3E5FC), const Color(0xFF81D4FA)],
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF039BE5).withOpacity(0.2),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('\u{1F95D}', style: TextStyle(fontSize: 14)),
            const SizedBox(width: 4),
            Text(
              hasRevealed
                  ? 'Hint ${_maxRevealedLevel + 1}/3'
                  : 'Hint',
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0277BD),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showHintSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _HintBottomSheet(
        hintLadder: widget.hintLadder,
        initialLevel: _maxRevealedLevel,
        onHintRevealed: (level) {
          if (level > _maxRevealedLevel) {
            setState(() {
              _maxRevealedLevel = level;
            });
          }
          widget.onHintRevealed?.call(level);
        },
      ),
    );
  }
}

class _HintBottomSheet extends StatelessWidget {
  final HintLadder hintLadder;
  final int initialLevel;
  final ValueChanged<int>? onHintRevealed;

  const _HintBottomSheet({
    required this.hintLadder,
    required this.initialLevel,
    this.onHintRevealed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.55,
      ),
      decoration: const BoxDecoration(
        color: Color(0xFFFAFCFF),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle bar
          const SizedBox(height: 10),
          Container(
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: const Color(0xFFBDBDBD),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 14),

          // Title
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                Text('\u{1F95D}', style: TextStyle(fontSize: 24)),
                SizedBox(width: 8),
                Text(
                  'Kiwi Hints',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.textDark,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Hint ladder — preserves state from previous opens
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: HintLadderBar(
                hintLadder: hintLadder,
                initialLevel: initialLevel,
                onHintRevealed: onHintRevealed,
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
