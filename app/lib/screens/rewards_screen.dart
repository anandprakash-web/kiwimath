import 'dart:math' as math;

import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';
import '../models/engagement.dart';

/// Rewards screen — sticker album, badges, mystery box.
///
/// Three tabs: Stickers | Badges | Mystery Box.
/// Age-tiered: G1-2 sees stickers prominently, G5-6 sees badges prominently.
class RewardsScreen extends StatefulWidget {
  final int grade;
  final List<Map<String, dynamic>> stickers;
  final double stickerProgress;
  final List<Map<String, dynamic>> badges;
  final int mysteryBoxesAvailable;
  final int puzzlesCompleted;
  final int puzzlesRequiredForBox;
  final VoidCallback? onOpenMysteryBox;
  final VoidCallback? onClose;

  const RewardsScreen({
    super.key,
    required this.grade,
    this.stickers = const [],
    this.stickerProgress = 0.0,
    this.badges = const [],
    this.mysteryBoxesAvailable = 0,
    this.puzzlesCompleted = 0,
    this.puzzlesRequiredForBox = 5,
    this.onOpenMysteryBox,
    this.onClose,
  });

  @override
  State<RewardsScreen> createState() => _RewardsScreenState();
}

class _RewardsScreenState extends State<RewardsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    // Default tab depends on grade: G1-2 starts on Stickers, G5-6 on Badges
    final initialIndex = widget.grade <= 2 ? 0 : 1;
    _tabController = TabController(
      length: 3,
      vsync: this,
      initialIndex: initialIndex,
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      appBar: AppBar(
        backgroundColor: KiwiColors.cardBg,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: KiwiColors.textDark),
          onPressed: widget.onClose ?? () => Navigator.of(context).pop(),
        ),
        title: const Text(
          '\u{1F3C6} Rewards',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        centerTitle: true,
        bottom: TabBar(
          controller: _tabController,
          labelColor: KiwiColors.kiwiPrimary,
          unselectedLabelColor: KiwiColors.textMuted,
          labelStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
          ),
          unselectedLabelStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
          indicatorColor: KiwiColors.kiwiPrimary,
          indicatorWeight: 3,
          tabs: const [
            Tab(text: '\u{1F4D6} Stickers'),
            Tab(text: '\u{1F3C5} Badges'),
            Tab(text: '\u{1F381} Mystery Box'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildStickersTab(),
          _buildBadgesTab(),
          _buildMysteryBoxTab(),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Stickers Tab
  // ---------------------------------------------------------------------------

  Widget _buildStickersTab() {
    final totalSlots = 30;
    final collected = widget.stickers.where((s) => s['collected'] == true).length;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Progress header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFFFF8E1), Color(0xFFFFF3E0)],
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                const Text(
                  '\u{1F4D6}',
                  style: TextStyle(fontSize: 40),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Sticker Album',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: KiwiColors.textDark,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '$collected / $totalSlots collected',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textMid,
                  ),
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: LinearProgressIndicator(
                    value: widget.stickerProgress.clamp(0.0, 1.0),
                    minHeight: 12,
                    backgroundColor: Colors.white.withOpacity(0.5),
                    valueColor:
                        const AlwaysStoppedAnimation<Color>(KiwiColors.xpPurple),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Sticker grid
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 5,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: 1.0,
            ),
            itemCount: totalSlots,
            itemBuilder: (context, index) {
              final hasSticker =
                  index < widget.stickers.length && widget.stickers[index]['collected'] == true;
              final emoji = hasSticker
                  ? (widget.stickers[index]['emoji'] as String? ?? '\u{2B50}')
                  : null;

              return Container(
                decoration: BoxDecoration(
                  color: hasSticker
                      ? KiwiColors.kiwiPrimaryLight
                      : KiwiColors.creamDark,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: hasSticker
                        ? KiwiColors.kiwiPrimary.withOpacity(0.3)
                        : Colors.grey.shade300,
                    width: 1.5,
                  ),
                  boxShadow: hasSticker
                      ? [
                          BoxShadow(
                            color: KiwiColors.kiwiPrimary.withOpacity(0.1),
                            blurRadius: 8,
                          ),
                        ]
                      : [],
                ),
                alignment: Alignment.center,
                child: hasSticker
                    ? Text(emoji!, style: const TextStyle(fontSize: 26))
                    : Icon(
                        Icons.help_outline_rounded,
                        size: 24,
                        color: Colors.grey.shade400,
                      ),
              );
            },
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Badges Tab
  // ---------------------------------------------------------------------------

  Widget _buildBadgesTab() {
    if (widget.badges.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('\u{1F3C5}', style: TextStyle(fontSize: 56)),
            const SizedBox(height: 16),
            const Text(
              'No badges yet',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Keep solving puzzles to earn badges!',
              style: TextStyle(
                fontSize: 14,
                color: KiwiColors.textMid,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(20),
      itemCount: widget.badges.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final badge = widget.badges[index];
        final earned = badge['earned'] == true;
        final emoji = badge['emoji'] as String? ?? '\u{1F3C5}';
        final name = badge['name'] as String? ?? 'Badge';
        final description = badge['description'] as String? ?? '';

        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: earned ? KiwiColors.cardBg : KiwiColors.creamDark,
            borderRadius: BorderRadius.circular(14),
            border: earned
                ? Border.all(color: KiwiColors.gemGold.withOpacity(0.4))
                : null,
            boxShadow: earned
                ? [
                    BoxShadow(
                      color: KiwiColors.gemGold.withOpacity(0.1),
                      blurRadius: 10,
                      offset: const Offset(0, 3),
                    ),
                  ]
                : [],
          ),
          child: Row(
            children: [
              // Badge icon
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: earned
                      ? KiwiColors.gemGold.withOpacity(0.15)
                      : Colors.grey.shade200,
                ),
                alignment: Alignment.center,
                child: Opacity(
                  opacity: earned ? 1.0 : 0.3,
                  child: Text(emoji, style: const TextStyle(fontSize: 26)),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: earned ? KiwiColors.textDark : KiwiColors.textMuted,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      description,
                      style: TextStyle(
                        fontSize: 13,
                        color: earned ? KiwiColors.textMid : KiwiColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
              if (earned)
                const Icon(
                  Icons.check_circle_rounded,
                  color: KiwiColors.gemGold,
                  size: 24,
                ),
              if (!earned)
                Icon(
                  Icons.lock_rounded,
                  color: Colors.grey.shade400,
                  size: 22,
                ),
            ],
          ),
        );
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Mystery Box Tab
  // ---------------------------------------------------------------------------

  Widget _buildMysteryBoxTab() {
    final available = widget.mysteryBoxesAvailable;
    final progress = widget.puzzlesRequiredForBox > 0
        ? (widget.puzzlesCompleted / widget.puzzlesRequiredForBox).clamp(0.0, 1.0)
        : 0.0;
    final isReady = available > 0;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: [
          const SizedBox(height: 20),

          // Mystery box visual
          _MysteryBoxVisual(
            isReady: isReady,
            onTap: isReady ? widget.onOpenMysteryBox : null,
          ),
          const SizedBox(height: 24),

          // Status text
          Text(
            isReady ? 'Your mystery box is ready!' : 'Keep solving puzzles!',
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 8),

          if (isReady)
            Text(
              '$available box${available != 1 ? 'es' : ''} available',
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: KiwiColors.xpPurple,
              ),
            )
          else ...[
            Text(
              '${widget.puzzlesCompleted} / ${widget.puzzlesRequiredForBox} puzzles done',
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: KiwiColors.textMid,
              ),
            ),
            const SizedBox(height: 14),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 40),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: LinearProgressIndicator(
                  value: progress,
                  minHeight: 12,
                  backgroundColor: KiwiColors.creamDark,
                  valueColor:
                      const AlwaysStoppedAnimation<Color>(KiwiColors.xpPurple),
                ),
              ),
            ),
          ],
          const SizedBox(height: 24),

          if (isReady)
            GestureDetector(
              onTap: widget.onOpenMysteryBox,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 16,
                ),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [KiwiColors.xpPurple, Color(0xFF6200EA)],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: KiwiColors.xpPurple.withOpacity(0.3),
                      blurRadius: 16,
                      offset: const Offset(0, 6),
                    ),
                  ],
                ),
                child: const Text(
                  'Open Mystery Box  \u{1F381}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
              ),
            ),

          const SizedBox(height: 30),

          // Info section
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: KiwiColors.cardBg,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'How Mystery Boxes Work',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
                const SizedBox(height: 10),
                _infoRow('\u{1F9E9}', 'Solve ${widget.puzzlesRequiredForBox} daily puzzles to earn a box'),
                const SizedBox(height: 6),
                _infoRow('\u{1F381}', 'Tap to shake and open your box'),
                const SizedBox(height: 6),
                _infoRow('\u{2728}', 'Win gems, stickers, or rare badges'),
                const SizedBox(height: 6),
                _infoRow('\u{1F48E}', 'Rarer rewards come from longer streaks'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String emoji, String text) {
    return Row(
      children: [
        Text(emoji, style: const TextStyle(fontSize: 16)),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 13,
              color: KiwiColors.textMid,
              height: 1.3,
            ),
          ),
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// Mystery Box Animated Visual
// ---------------------------------------------------------------------------

class _MysteryBoxVisual extends StatefulWidget {
  final bool isReady;
  final VoidCallback? onTap;

  const _MysteryBoxVisual({required this.isReady, this.onTap});

  @override
  State<_MysteryBoxVisual> createState() => _MysteryBoxVisualState();
}

class _MysteryBoxVisualState extends State<_MysteryBoxVisual>
    with SingleTickerProviderStateMixin {
  late final AnimationController _shakeController;
  late final Animation<double> _shakeAnimation;

  @override
  void initState() {
    super.initState();
    _shakeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _shakeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _shakeController, curve: Curves.elasticIn),
    );

    if (widget.isReady) {
      _startIdleShake();
    }
  }

  @override
  void dispose() {
    _shakeController.dispose();
    super.dispose();
  }

  void _startIdleShake() {
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted && widget.isReady) {
        _shakeController.forward().then((_) {
          _shakeController.reverse().then((_) {
            _startIdleShake();
          });
        });
      }
    });
  }

  void _triggerShake() {
    _shakeController.forward().then((_) {
      _shakeController.reverse();
    });
    widget.onTap?.call();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.isReady ? _triggerShake : null,
      child: AnimatedBuilder(
        animation: _shakeController,
        builder: (context, child) {
          final shakeOffset =
              math.sin(_shakeAnimation.value * math.pi * 4) * 6;
          return Transform.translate(
            offset: Offset(shakeOffset, 0),
            child: Transform.rotate(
              angle: math.sin(_shakeAnimation.value * math.pi * 3) * 0.05,
              child: child,
            ),
          );
        },
        child: Container(
          width: 140,
          height: 140,
          decoration: BoxDecoration(
            gradient: widget.isReady
                ? const RadialGradient(
                    colors: [Color(0xFFE1BEE7), Color(0xFFCE93D8)],
                  )
                : RadialGradient(
                    colors: [Colors.grey.shade200, Colors.grey.shade300],
                  ),
            shape: BoxShape.circle,
            boxShadow: widget.isReady
                ? [
                    BoxShadow(
                      color: KiwiColors.xpPurple.withOpacity(0.2),
                      blurRadius: 24,
                      spreadRadius: 4,
                    ),
                  ]
                : [],
          ),
          alignment: Alignment.center,
          child: Text(
            '\u{1F381}',
            style: TextStyle(
              fontSize: widget.isReady ? 64 : 48,
            ),
          ),
        ),
      ),
    );
  }
}
