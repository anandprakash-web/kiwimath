import 'package:flutter/material.dart';

/// Bottom-sheet note editor. Returns the trimmed note text, or null if the
/// user cancelled. Pass [initial] to edit an existing note and [quote] to show
/// the highlighted passage for context.
Future<String?> showNoteEditor(
  BuildContext context, {
  String? initial,
  String? quote,
}) {
  final controller = TextEditingController(text: initial ?? '');
  return showModalBottomSheet<String>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (ctx) {
      final bottomInset = MediaQuery.of(ctx).viewInsets.bottom;
      return Padding(
        padding: EdgeInsets.fromLTRB(16, 4, 16, 16 + bottomInset),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (quote != null && quote.isNotEmpty)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.fromLTRB(10, 6, 10, 6),
                decoration: const BoxDecoration(
                  border: Border(
                    left: BorderSide(color: Color(0xFF16A34A), width: 3),
                  ),
                ),
                child: Text(
                  quote,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF52635A),
                  ),
                ),
              ),
            TextField(
              controller: controller,
              autofocus: true,
              minLines: 3,
              maxLines: 6,
              decoration: const InputDecoration(
                hintText: 'Type your note…',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: TextButton(
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('Cancel'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton(
                    onPressed: () => Navigator.pop(ctx, controller.text.trim()),
                    child: const Text('Save note'),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
    },
  );
}
