import 'package:flutter/material.dart';

import '../config/reader_config.dart';

/// Floating toolbar shown when text is selected: pick a highlight color or
/// attach a note. (Underline/strikethrough/ask-AI are added in later tickets.)
class SelectionToolbar extends StatelessWidget {
  final List<HighlightColor> palette;
  final void Function(HighlightColor color) onColor;
  final VoidCallback onNote;

  const SelectionToolbar({
    super.key,
    required this.palette,
    required this.onColor,
    required this.onNote,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Theme.of(context).colorScheme.inverseSurface,
      borderRadius: BorderRadius.circular(12),
      elevation: 8,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final c in palette)
              Padding(
                padding: const EdgeInsets.all(3),
                child: GestureDetector(
                  onTap: () => onColor(c),
                  child: Container(
                    width: 24,
                    height: 24,
                    decoration: BoxDecoration(
                      color: c.color,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white24),
                    ),
                  ),
                ),
              ),
            Container(
              width: 1,
              height: 24,
              color: Colors.white24,
              margin: const EdgeInsets.symmetric(horizontal: 6),
            ),
            IconButton(
              onPressed: onNote,
              icon: const Icon(
                Icons.note_add_outlined,
                color: Colors.white,
                size: 18,
              ),
              constraints: const BoxConstraints(),
              padding: const EdgeInsets.all(6),
              tooltip: 'Add note',
            ),
          ],
        ),
      ),
    );
  }
}
