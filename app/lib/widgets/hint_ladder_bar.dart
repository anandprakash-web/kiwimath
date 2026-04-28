import 'package:flutter/material.dart';

import '../models/question_v2.dart';
import '../theme/kiwi_theme.dart';

/// Premium Socratic hint ladder bar — cheerful, colorful, hi-fi.
///
/// Progressively reveals 6 levels of Socratic hints:
///   L0: Pause prompt (gentle nudge)
///   L1: Attention direction (where to look)
///   L2: Thinking question (Socratic prompt)
///   L3: Scaffolded step (break it down)
///   L4: Guided reveal (almost there)
///   L5: Teach + retry (explain the concept)
///
/// Philosophy: "Hint = Ask better question, NOT give answer."
/// Every child should feel: I can think, I can solve, I am improving.
class HintLadderBar extends StatefulWidget {
  final HintLadder hintLadder;

  /// Called when the user reveals a new hint level.
  /// Returns the highest level revealed (0-5).
  final ValueChanged<int>? onHintRevealed;

  /// Start with this level already revealed (for retry scenarios).
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
  /// -1 = no hint shown yet, 0-5 = current level revealed
  int _currentLevel = -1;

  late AnimationController _pulseController;
  late AnimationController _revealController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _revealAnimation;

  // Cheerful gradient colors for each hint level
  static const _levelColors = [
    [Color(0xFF81D4FA), Color(0xFF4FC3F7)], // L0: sky blue
    [Color(0xFF80DEEA), Color(0xFF26C6DA)], // L1: teal
    [Color(0xFFA5D6A7), Color(0xFF66BB6A)], // L2: fresh green
    [Color(0xFFFFCC80), Color(0xFFFF9800)], // L3: warm amber
    [Color(0xFFFFAB91), Color(0xFFFF7043)], // L4: coral
    [Color(0xFFCE93D8), Color(0xFFAB47BC)], // L5: purple
  ];

  static const _levelIcons = [
    Icons.pause_circle_outline,   // L0: pause
    Icons.visibility,             // L1: look
    Icons.psychology,             // L2: think
    Icons.stairs,                 // L3: steps
    Icons.lightbulb,              // L4: reveal
    Icons.school,                 // L5: teach
  ];

  static const _levelLabels = [
    'Take a breath',
    'Look here',
    'Think about this',
    'Break it down',
    'Almost there',
    'Learn the trick',
  ];

  static const _levelEmoji = [
    '\u{1F33F}',  // L0: seedling
    '\u{1F50D}',  // L1: magnifying glass
    '\u{1F914}',  // L2: thinking
    '\u{1F9E9}',  // L3: puzzle piece
    '\u{1F4A1}',  // L4: lightbulb
    '\u{2B50}',   // L5: star
  ];

  @override
  void initState() {
    super.initState();
    _currentLevel = widget.initialLevel;

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
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
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _revealController.dispose();
    super.dispose();
  }

  void _revealNextHint() {
    if (_currentLevel >= 5) return;

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
        // Progress dots showing hint level
        _buildProgressDots(),
        const SizedBox(height: 8),

        // Current hint card (or "need a hint?" button)
        if (_currentLevel < 0)
          _buildNeedHintButton()
        else
          _buildHintCard(),

        // "Next hint" button (if more hints available)
        if (_currentLevel >= 0 && _currentLevel < 5) ...[
          const SizedBox(height: 6),
          _buildNextHintButton(),
        ],
      ],
    );
  }

  Widget _buildProgressDots() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(6, (i) {
        final isRevealed = i <= _currentLevel;
        final isCurrent = i == _currentLevel;
        final colors = _levelColors[i];

        return AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          margin: const EdgeInsets.symmetric(horizontal: 3),
          width: isCurrent ? 24 : 10,
          height: 10,
          decoration: BoxDecoration(
            gradient: isRevealed
                ? LinearGradient(colors: colors)
                : null,
            color: isRevealed ? null : const Color(0xFFE0E0E0),
            borderRadius: BorderRadius.circular(5),
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
              colors: [Color(0xFF81D4FA), Color(0xFF4FC3F7)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF4FC3F7).withOpacity(0.3),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('\u{1F95D}', style: TextStyle(fontSize: 20)), // kiwi
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
    final level = _currentLevel.clamp(0, 5);
    final colors = _levelColors[level];
    final hintText = widget.hintLadder.forLevel(level);
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
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: colors[1],
                    ),
                  ),
                ),
                // Level badge
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
                    'Hint ${level + 1}/6',
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
              style: TextStyle(
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
    final nextLevel = (_currentLevel + 1).clamp(0, 5);
    final nextColors = _levelColors[nextLevel];
    final remaining = 5 - _currentLevel;

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
class HintButton extends StatelessWidget {
  final HintLadder hintLadder;
  final ValueChanged<int>? onHintRevealed;

  const HintButton({
    super.key,
    required this.hintLadder,
    this.onHintRevealed,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => _showHintSheet(context),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFB3E5FC), Color(0xFF81D4FA)],
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF4FC3F7).withOpacity(0.2),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('\u{1F95D}', style: TextStyle(fontSize: 14)),
            SizedBox(width: 4),
            Text(
              'Hint',
              style: TextStyle(
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
        hintLadder: hintLadder,
        onHintRevealed: onHintRevealed,
      ),
    );
  }
}

class _HintBottomSheet extends StatefulWidget {
  final HintLadder hintLadder;
  final ValueChanged<int>? onHintRevealed;

  const _HintBottomSheet({
    required this.hintLadder,
    this.onHintRevealed,
  });

  @override
  State<_HintBottomSheet> createState() => _HintBottomSheetState();
}

class _HintBottomSheetState extends State<_HintBottomSheet> {
  int _maxRevealedLevel = -1;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.65,
      ),
      decoration: const BoxDecoration(
        color: Color(0xFFFAFCFF),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Handle
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

          // Hint ladder
          Flexible(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: HintLadderBar(
                hintLadder: widget.hintLadder,
                initialLevel: _maxRevealedLevel,
                onHintRevealed: (level) {
                  setState(() {
                    if (level > _maxRevealedLevel) {
                      _maxRevealedLevel = level;
                    }
                  });
                  widget.onHintRevealed?.call(level);
                },
              ),
            ),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
