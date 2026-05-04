import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// Picture Unravel puzzle grid.
///
/// Displays a grid of [gridRows] x [gridCols] blocks. The first
/// [blocksRevealed] entries in [blockOrder] are shown as revealed; the
/// rest display a hidden gradient tile. When [puzzleImageUrl] is provided the
/// revealed area shows the image; otherwise a placeholder colour is used.
class PixelGridWidget extends StatelessWidget {
  final int gridRows;
  final int gridCols;
  final int blocksRevealed;
  final List<int> blockOrder;
  final String? puzzleImageUrl;

  const PixelGridWidget({
    super.key,
    required this.gridRows,
    required this.gridCols,
    required this.blocksRevealed,
    required this.blockOrder,
    this.puzzleImageUrl,
  });

  int get _totalBlocks => gridRows * gridCols;

  double get _revealPercent =>
      _totalBlocks == 0 ? 0 : (blocksRevealed / _totalBlocks * 100);

  @override
  Widget build(BuildContext context) {
    // Build a set of revealed block indices for O(1) lookup.
    final revealedSet = <int>{};
    for (var i = 0; i < blocksRevealed && i < blockOrder.length; i++) {
      revealedSet.add(blockOrder[i]);
    }

    // Track the most recently revealed block for the fade animation.
    final int? newestBlock =
        blocksRevealed > 0 && blocksRevealed <= blockOrder.length
            ? blockOrder[blocksRevealed - 1]
            : null;

    return Container(
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
        mainAxisSize: MainAxisSize.min,
        children: [
          // --- Grid area ---
          ClipRRect(
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(14),
            ),
            child: AspectRatio(
              aspectRatio: gridCols / gridRows,
              child: Stack(
                children: [
                  // Puzzle image layer (or placeholder)
                  Positioned.fill(
                    child: puzzleImageUrl != null
                        ? Image.network(
                            puzzleImageUrl!,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) =>
                                _placeholderBackground(),
                          )
                        : _placeholderBackground(),
                  ),

                  // Block overlay grid
                  Positioned.fill(
                    child: LayoutBuilder(
                      builder: (context, constraints) {
                        final blockW = constraints.maxWidth / gridCols;
                        final blockH = constraints.maxHeight / gridRows;

                        return Stack(
                          children: List.generate(_totalBlocks, (index) {
                            final row = index ~/ gridCols;
                            final col = index % gridCols;
                            final isRevealed = revealedSet.contains(index);
                            final isNewest = index == newestBlock;

                            return Positioned(
                              left: col * blockW,
                              top: row * blockH,
                              width: blockW,
                              height: blockH,
                              child: _BlockTile(
                                isRevealed: isRevealed,
                                isNewest: isNewest,
                                row: row,
                                col: col,
                                totalRows: gridRows,
                                totalCols: gridCols,
                              ),
                            );
                          }),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),

          // --- Reveal percentage footer ---
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: const BoxDecoration(
              color: KiwiColors.cream,
              borderRadius: BorderRadius.vertical(
                bottom: Radius.circular(14),
              ),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.visibility_rounded,
                  size: 16,
                  color: KiwiColors.kiwiPrimary,
                ),
                const SizedBox(width: 6),
                Text(
                  '${_revealPercent.toStringAsFixed(1)}% revealed',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textDark,
                  ),
                ),
                const Spacer(),
                Text(
                  '$blocksRevealed / $_totalBlocks blocks',
                  style: const TextStyle(
                    fontSize: 12,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholderBackground() {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFFFFF3E0),
            Color(0xFFFFE0B2),
            Color(0xFFFFF8E1),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Individual block tile — animates from hidden to revealed.
// ---------------------------------------------------------------------------

class _BlockTile extends StatefulWidget {
  final bool isRevealed;
  final bool isNewest;
  final int row;
  final int col;
  final int totalRows;
  final int totalCols;

  const _BlockTile({
    required this.isRevealed,
    required this.isNewest,
    required this.row,
    required this.col,
    required this.totalRows,
    required this.totalCols,
  });

  @override
  State<_BlockTile> createState() => _BlockTileState();
}

class _BlockTileState extends State<_BlockTile>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _opacity = CurvedAnimation(parent: _controller, curve: Curves.easeOut);

    if (widget.isRevealed && widget.isNewest) {
      // Animate the newest reveal.
      _controller.forward();
    } else if (widget.isRevealed) {
      _controller.value = 1.0;
    }
  }

  @override
  void didUpdateWidget(covariant _BlockTile oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!oldWidget.isRevealed && widget.isRevealed) {
      _controller.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.isRevealed) {
      // Fade out the hidden tile to reveal the image beneath.
      return FadeTransition(
        opacity: ReverseAnimation(_opacity),
        child: _hiddenTile(),
      );
    }
    return _hiddenTile();
  }

  Widget _hiddenTile() {
    // Gradient varies slightly by position for a mosaic effect.
    final tRow = widget.row / widget.totalRows;
    final tCol = widget.col / widget.totalCols;

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color.lerp(
              KiwiColors.kiwiPrimary,
              KiwiColors.kiwiPrimaryDark,
              tRow,
            )!,
            Color.lerp(
              KiwiColors.kiwiPrimary,
              const Color(0xFFFF8F00),
              tCol,
            )!,
          ],
        ),
        border: Border.all(
          color: Colors.white.withOpacity(0.12),
          width: 0.5,
        ),
      ),
    );
  }
}
