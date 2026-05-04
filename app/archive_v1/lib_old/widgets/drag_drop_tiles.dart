import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';

/// Fun, interactive drag-and-drop ordering widget for kids.
///
/// Features:
/// - Colorful numbered drop zones with gradient backgrounds
/// - Bouncy drag animations with scale + rotation
/// - Haptic feedback on pick-up, drop, and check
/// - Confetti-like color burst on correct placement
/// - Smooth reorder transitions
/// - "Shake" animation on wrong positions after check
class DragDropTiles extends StatefulWidget {
  /// The items to arrange (in their correct order from the backend).
  final List<String> items;

  /// Callback when the child taps "Check".
  /// Returns the current ordering: order[i] = original index of item now at position i.
  final ValueChanged<List<int>> onSubmit;

  const DragDropTiles({
    super.key,
    required this.items,
    required this.onSubmit,
  });

  @override
  State<DragDropTiles> createState() => _DragDropTilesState();
}

class _DragDropTilesState extends State<DragDropTiles>
    with TickerProviderStateMixin {
  /// Current ordering — stores original indices in display order.
  late List<int> _order;
  bool _checked = false;
  List<bool>? _correctPositions;

  // Animation controllers for wrong tiles shake
  late List<AnimationController> _shakeControllers;
  late List<Animation<double>> _shakeAnimations;

  // Tile colors — each position gets a distinct pastel color
  static const _tileColors = [
    Color(0xFFFFF3E0), // warm peach
    Color(0xFFE3F2FD), // sky blue
    Color(0xFFE8F5E9), // mint green
    Color(0xFFF3E5F5), // lavender
    Color(0xFFFFFDE7), // sunshine yellow
    Color(0xFFE0F7FA), // aqua
  ];

  static const _tileBorderColors = [
    Color(0xFFFF9800), // orange
    Color(0xFF2196F3), // blue
    Color(0xFF4CAF50), // green
    Color(0xFF9C27B0), // purple
    Color(0xFFFFC107), // amber
    Color(0xFF00BCD4), // cyan
  ];

  @override
  void initState() {
    super.initState();
    _order = List.generate(widget.items.length, (i) => i);
    _shuffle();

    // Set up shake animations for each tile
    _shakeControllers = List.generate(
      widget.items.length,
      (_) => AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 500),
      ),
    );
    _shakeAnimations = _shakeControllers.map((c) {
      return Tween<double>(begin: 0, end: 1).animate(
        CurvedAnimation(parent: c, curve: Curves.elasticIn),
      );
    }).toList();
  }

  @override
  void dispose() {
    for (final c in _shakeControllers) {
      c.dispose();
    }
    super.dispose();
  }

  void _shuffle() {
    final rng = Random();
    do {
      for (int i = _order.length - 1; i > 0; i--) {
        final j = rng.nextInt(i + 1);
        final tmp = _order[i];
        _order[i] = _order[j];
        _order[j] = tmp;
      }
    } while (_isCorrectOrder() && widget.items.length > 1);
  }

  bool _isCorrectOrder() {
    for (int i = 0; i < _order.length; i++) {
      if (_order[i] != i) return false;
    }
    return true;
  }

  void _onReorder(int oldIndex, int newIndex) {
    if (_checked) return;
    HapticFeedback.lightImpact();
    setState(() {
      if (newIndex > oldIndex) newIndex--;
      final item = _order.removeAt(oldIndex);
      _order.insert(newIndex, item);
    });
  }

  void _onCheck() {
    HapticFeedback.mediumImpact();
    setState(() {
      _checked = true;
      _correctPositions = List.generate(
        _order.length,
        (i) => _order[i] == i,
      );
    });

    // Shake wrong tiles
    for (int i = 0; i < _order.length; i++) {
      if (_correctPositions![i] == false) {
        _shakeControllers[i].forward(from: 0);
      }
    }

    widget.onSubmit(List<int>.from(_order));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Playful instruction banner
        Container(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                const Color(0xFFFFF8E1),
                const Color(0xFFFFECB3),
              ],
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFFFD54F), width: 1.5),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('🎯', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 8),
              Text(
                'Drag tiles to put them in order!',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFF5D4037),
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                Icons.swap_vert_rounded,
                size: 20,
                color: const Color(0xFFFF6D00),
              ),
            ],
          ),
        ),

        // Reorderable tile list — wraps in a constrained box for ReorderableListView
        ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: widget.items.length * 72.0, // ~64px tile + 8px margin
          ),
          child: ReorderableListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            buildDefaultDragHandles: false, // We use custom drag handles
            itemCount: widget.items.length,
            onReorder: _onReorder,
            proxyDecorator: (child, index, animation) {
              return AnimatedBuilder(
                animation: animation,
                builder: (context, child) {
                  final scale = 1.0 + 0.05 * animation.value;
                  final elevation = 8.0 * animation.value;
                  return Transform.scale(
                    scale: scale,
                    child: Material(
                      elevation: elevation,
                      color: Colors.transparent,
                      borderRadius: BorderRadius.circular(14),
                      child: child,
                    ),
                  );
                },
                child: child,
              );
            },
            itemBuilder: (context, displayIndex) {
              final originalIndex = _order[displayIndex];
              final text = widget.items[originalIndex];
              final isCorrect = _correctPositions?[displayIndex];
              final colorIdx = displayIndex % _tileColors.length;

              return AnimatedBuilder(
                key: ValueKey(originalIndex),
                animation: _shakeAnimations[displayIndex],
                builder: (context, child) {
                  final shake = _checked && isCorrect == false
                      ? sin(_shakeAnimations[displayIndex].value * 3 * pi) * 8
                      : 0.0;
                  return Transform.translate(
                    offset: Offset(shake, 0),
                    child: child,
                  );
                },
                child: _buildTile(displayIndex, originalIndex, text, isCorrect, colorIdx),
              );
            },
          ),
        ),

        const SizedBox(height: 14),

        // Check button with fun styling
        if (!_checked)
          SizedBox(
            width: double.infinity,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFFF6D00), Color(0xFFFF8F00)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFFFF6D00).withOpacity(0.4),
                    blurRadius: 10,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: ElevatedButton.icon(
                onPressed: _onCheck,
                icon: const Icon(Icons.check_circle_outline, size: 22),
                label: const Text('Check My Order!'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  shadowColor: Colors.transparent,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  textStyle: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.3,
                  ),
                ),
              ),
            ),
          ),

        // Score feedback after check
        if (_checked && _correctPositions != null)
          Padding(
            padding: const EdgeInsets.only(top: 10),
            child: _buildScoreFeedback(),
          ),
      ],
    );
  }

  Widget _buildTile(int displayIndex, int originalIndex, String text, bool? isCorrect, int colorIdx) {
    Color bg;
    Color borderColor;
    Widget? statusIcon;

    if (_checked && isCorrect == true) {
      bg = const Color(0xFFE8F5E9);
      borderColor = const Color(0xFF4CAF50);
      statusIcon = Container(
        width: 26,
        height: 26,
        decoration: const BoxDecoration(
          color: Color(0xFF4CAF50),
          shape: BoxShape.circle,
        ),
        child: const Icon(Icons.check, size: 16, color: Colors.white),
      );
    } else if (_checked && isCorrect == false) {
      bg = const Color(0xFFFFEBEE);
      borderColor = const Color(0xFFE53935);
      statusIcon = Container(
        width: 26,
        height: 26,
        decoration: const BoxDecoration(
          color: Color(0xFFE53935),
          shape: BoxShape.circle,
        ),
        child: const Icon(Icons.close, size: 16, color: Colors.white),
      );
    } else {
      bg = _tileColors[colorIdx];
      borderColor = _tileBorderColors[colorIdx].withOpacity(0.6);
      statusIcon = null;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: borderColor, width: 2.2),
        boxShadow: [
          BoxShadow(
            color: borderColor.withOpacity(0.15),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(14),
          onTap: () {}, // for ripple effect
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            child: Row(
              children: [
                // Position indicator (slot number)
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: _checked
                          ? isCorrect == true
                              ? [const Color(0xFF4CAF50), const Color(0xFF2E7D32)]
                              : [const Color(0xFFE53935), const Color(0xFFC62828)]
                          : [
                              _tileBorderColors[colorIdx],
                              _tileBorderColors[colorIdx].withOpacity(0.7),
                            ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: _tileBorderColors[colorIdx].withOpacity(0.3),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Center(
                    child: Text(
                      '${displayIndex + 1}',
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),

                // Item text
                Expanded(
                  child: Text(
                    text,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: _checked && isCorrect == false
                          ? const Color(0xFFC62828)
                          : const Color(0xFF212121),
                      letterSpacing: 0.2,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),

                // Drag handle or status icon
                if (statusIcon != null)
                  statusIcon
                else
                  ReorderableDragStartListener(
                    index: displayIndex,
                    child: Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: _tileBorderColors[colorIdx].withOpacity(0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        Icons.drag_indicator_rounded,
                        size: 24,
                        color: _tileBorderColors[colorIdx],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildScoreFeedback() {
    final correct = _correctPositions!.where((c) => c).length;
    final total = _correctPositions!.length;
    final allCorrect = correct == total;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
      decoration: BoxDecoration(
        color: allCorrect ? const Color(0xFFE8F5E9) : const Color(0xFFFFF3E0),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: allCorrect ? const Color(0xFF4CAF50) : const Color(0xFFFF9800),
          width: 1.5,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            allCorrect ? '🎉' : '💪',
            style: const TextStyle(fontSize: 20),
          ),
          const SizedBox(width: 8),
          Text(
            allCorrect
                ? 'Perfect order!'
                : '$correct of $total in the right spot',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: allCorrect ? const Color(0xFF2E7D32) : const Color(0xFFE65100),
            ),
          ),
        ],
      ),
    );
  }
}
