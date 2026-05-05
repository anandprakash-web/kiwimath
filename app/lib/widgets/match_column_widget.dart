import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';

/// Match-the-column widget — connect items from left column to right column.
///
/// Kids tap a left item, then tap a right item to make a match.
/// Matches are shown with colored lines. Tap again to change.
class MatchColumnWidget extends StatefulWidget {
  final List<String> leftItems;
  final List<String> rightItems;

  /// Callback with the user's matches: {leftItem: rightItem}.
  final ValueChanged<Map<String, String>> onSubmit;

  const MatchColumnWidget({
    super.key,
    required this.leftItems,
    required this.rightItems,
    required this.onSubmit,
  });

  @override
  State<MatchColumnWidget> createState() => _MatchColumnWidgetState();
}

class _MatchColumnWidgetState extends State<MatchColumnWidget> {
  /// Current matches: left index → right index.
  final Map<int, int> _matches = {};

  /// Currently selected left item waiting for a right match.
  int? _selectedLeft;

  bool _checked = false;

  // Match line colors — each pair gets a distinct color
  static const _matchColors = [
    Color(0xFFFF6D00), // orange
    Color(0xFF2196F3), // blue
    Color(0xFF4CAF50), // green
    Color(0xFF9C27B0), // purple
    Color(0xFFFF4081), // pink
    Color(0xFF00BCD4), // cyan
  ];

  bool get _allMatched => _matches.length == widget.leftItems.length;

  void _onTapLeft(int index) {
    if (_checked) return;
    HapticFeedback.lightImpact();
    setState(() {
      if (_selectedLeft == index) {
        _selectedLeft = null; // deselect
      } else {
        _selectedLeft = index;
      }
    });
  }

  void _onTapRight(int index) {
    if (_checked || _selectedLeft == null) return;
    HapticFeedback.mediumImpact();
    setState(() {
      // Remove any existing match to this right item
      _matches.removeWhere((k, v) => v == index);
      // Create the match
      _matches[_selectedLeft!] = index;
      _selectedLeft = null;
    });
  }

  void _onCheck() {
    if (!_allMatched) return;
    HapticFeedback.mediumImpact();
    setState(() => _checked = true);

    // Convert to string-based map
    final result = <String, String>{};
    for (final entry in _matches.entries) {
      result[widget.leftItems[entry.key]] = widget.rightItems[entry.value];
    }
    widget.onSubmit(result);
  }

  Color _colorForMatch(int leftIndex) {
    return _matchColors[leftIndex % _matchColors.length];
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Instruction banner
        Container(
          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFFF3E5F5), Color(0xFFE1BEE7)],
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFCE93D8), width: 1.5),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('\u{1F517}', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 8),
              Text(
                'Tap left, then tap right to match!',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFF6A1B9A),
                ),
              ),
            ],
          ),
        ),

        // Match area with custom paint for lines
        LayoutBuilder(
          builder: (context, constraints) {
            return CustomPaint(
              painter: _MatchLinesPainter(
                matches: _matches,
                itemCount: widget.leftItems.length,
                matchColors: _matchColors,
                totalWidth: constraints.maxWidth,
              ),
              child: _buildColumns(),
            );
          },
        ),

        const SizedBox(height: 16),

        // Progress indicator
        if (!_checked)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              '${_matches.length} of ${widget.leftItems.length} matched',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: _allMatched
                    ? const Color(0xFF4CAF50)
                    : KiwiColors.textMuted,
              ),
            ),
          ),

        // Check button
        if (!_checked)
          SizedBox(
            width: double.infinity,
            child: _allMatched
                ? DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF9C27B0), Color(0xFF7B1FA2)],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF9C27B0).withOpacity(0.4),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ElevatedButton.icon(
                      onPressed: _onCheck,
                      icon: const Icon(Icons.check_circle_outline, size: 22),
                      label: const Text('Check Matches!'),
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
                        ),
                      ),
                    ),
                  )
                : ElevatedButton(
                    onPressed: null,
                    style: ElevatedButton.styleFrom(
                      disabledBackgroundColor:
                          const Color(0xFF9C27B0).withOpacity(0.08),
                      disabledForegroundColor:
                          const Color(0xFF9C27B0).withOpacity(0.35),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      textStyle: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    child: const Text('Match all pairs'),
                  ),
          ),
      ],
    );
  }

  Widget _buildColumns() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Left column
        Expanded(
          child: Column(
            children: List.generate(widget.leftItems.length, (i) {
              final isSelected = _selectedLeft == i;
              final isMatched = _matches.containsKey(i);
              final color = isMatched ? _colorForMatch(i) : null;

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: GestureDetector(
                  onTap: () => _onTapLeft(i),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(
                        vertical: 14, horizontal: 12),
                    decoration: BoxDecoration(
                      color: isSelected
                          ? const Color(0xFFE1BEE7)
                          : isMatched
                              ? color!.withOpacity(0.1)
                              : Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: isSelected
                            ? const Color(0xFF9C27B0)
                            : isMatched
                                ? color!
                                : const Color(0xFFE0E0E0),
                        width: isSelected || isMatched ? 2.5 : 1.5,
                      ),
                      boxShadow: isSelected
                          ? [
                              BoxShadow(
                                color:
                                    const Color(0xFF9C27B0).withOpacity(0.2),
                                blurRadius: 8,
                                offset: const Offset(0, 3),
                              ),
                            ]
                          : [],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 26,
                          height: 26,
                          decoration: BoxDecoration(
                            color: isMatched
                                ? color!
                                : isSelected
                                    ? const Color(0xFF9C27B0)
                                    : const Color(0xFFE0E0E0),
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: isMatched
                                ? const Icon(Icons.link,
                                    size: 14, color: Colors.white)
                                : Text(
                                    '${i + 1}',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w800,
                                      color: isSelected
                                          ? Colors.white
                                          : const Color(0xFF757575),
                                    ),
                                  ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            widget.leftItems[i],
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: const Color(0xFF212121),
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ),

        // Middle gap for lines
        const SizedBox(width: 24),

        // Right column (shuffled display order)
        Expanded(
          child: Column(
            children: List.generate(widget.rightItems.length, (i) {
              // Check if this right item is matched
              final matchedLeftIndex =
                  _matches.entries.where((e) => e.value == i).isEmpty
                      ? null
                      : _matches.entries.firstWhere((e) => e.value == i).key;
              final isMatched = matchedLeftIndex != null;
              final color =
                  isMatched ? _colorForMatch(matchedLeftIndex) : null;
              final isHighlighted = _selectedLeft != null && !isMatched;

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: GestureDetector(
                  onTap: () => _onTapRight(i),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(
                        vertical: 14, horizontal: 12),
                    decoration: BoxDecoration(
                      color: isMatched
                          ? color!.withOpacity(0.1)
                          : isHighlighted
                              ? const Color(0xFFF3E5F5)
                              : Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: isMatched
                            ? color!
                            : isHighlighted
                                ? const Color(0xFFCE93D8)
                                : const Color(0xFFE0E0E0),
                        width: isMatched ? 2.5 : 1.5,
                      ),
                      boxShadow: isHighlighted
                          ? [
                              BoxShadow(
                                color:
                                    const Color(0xFFCE93D8).withOpacity(0.2),
                                blurRadius: 6,
                                offset: const Offset(0, 2),
                              ),
                            ]
                          : [],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 26,
                          height: 26,
                          decoration: BoxDecoration(
                            color: isMatched
                                ? color!
                                : const Color(0xFFE0E0E0),
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: isMatched
                                ? const Icon(Icons.link,
                                    size: 14, color: Colors.white)
                                : Text(
                                    String.fromCharCode(65 + i), // A, B, C...
                                    style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w800,
                                      color: Color(0xFF757575),
                                    ),
                                  ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            widget.rightItems[i],
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: const Color(0xFF212121),
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }),
          ),
        ),
      ],
    );
  }
}

/// Custom painter to draw connecting lines between matched pairs.
class _MatchLinesPainter extends CustomPainter {
  final Map<int, int> matches;
  final int itemCount;
  final List<Color> matchColors;
  final double totalWidth;

  _MatchLinesPainter({
    required this.matches,
    required this.itemCount,
    required this.matchColors,
    required this.totalWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Each item row is ~62px tall (14 padding top + 26 circle + 14 padding bottom + 10 margin)
    const itemHeight = 62.0;
    const halfItem = 31.0; // vertical center of item

    final leftColumnEnd = (totalWidth - 24) / 2; // end of left column
    final rightColumnStart = leftColumnEnd + 24; // start of right column

    for (final entry in matches.entries) {
      final leftIdx = entry.key;
      final rightIdx = entry.value;
      final color = matchColors[leftIdx % matchColors.length];

      final paint = Paint()
        ..color = color.withOpacity(0.5)
        ..strokeWidth = 3
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      final startY = leftIdx * itemHeight + halfItem;
      final endY = rightIdx * itemHeight + halfItem;

      final path = Path()
        ..moveTo(leftColumnEnd, startY)
        ..cubicTo(
          leftColumnEnd + 12, startY,
          rightColumnStart - 12, endY,
          rightColumnStart, endY,
        );

      canvas.drawPath(path, paint);
    }
  }

  @override
  bool shouldRepaint(covariant _MatchLinesPainter oldDelegate) =>
      matches != oldDelegate.matches;
}
