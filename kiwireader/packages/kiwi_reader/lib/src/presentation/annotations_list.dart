import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../state/reader_providers.dart';

/// Full-screen "My annotations" list. Reactive (watches the provider). Tapping
/// an item pops with that [Annotation] so the reader can jump to it; the
/// trailing icon soft-deletes.
class AnnotationsListScreen extends ConsumerWidget {
  final String bookId;
  const AnnotationsListScreen({super.key, required this.bookId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(annotationsProvider(bookId));
    final controller = ref.read(annotationControllerProvider(bookId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('My annotations'),
        actions: [
          IconButton(
            tooltip: 'Export (Markdown)',
            icon: const Icon(Icons.ios_share),
            onPressed: () async {
              final md = await controller.exportMarkdown();
              if (context.mounted) _showExport(context, md);
            },
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (items) {
          final live = items.where((a) => !a.isDeleted).toList()
            ..sort((a, b) => a.anchor.sectionId.compareTo(b.anchor.sectionId));
          if (live.isEmpty) {
            return const Center(child: Text('No annotations yet.'));
          }
          return ListView.separated(
            itemCount: live.length,
            separatorBuilder: (_, __) => const Divider(height: 1),
            itemBuilder: (context, i) {
              final a = live[i];
              final icon = switch (a.type) {
                AnnotationType.note => Icons.sticky_note_2_outlined,
                AnnotationType.bookmark => Icons.bookmark,
                _ => Icons.brush_outlined,
              };
              final subtitle = switch (a.type) {
                AnnotationType.note => a.noteText ?? '',
                AnnotationType.bookmark => a.noteText ?? '(bookmark)',
                _ => a.anchor.quote?.exact ?? '(passage)',
              };
              return ListTile(
                leading: Icon(
                  icon,
                  color: a.type == AnnotationType.bookmark
                      ? const Color(0xFF16A34A)
                      : _dotColor(a.color),
                ),
                title: Text(
                  a.anchor.sectionId,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                subtitle: Text(
                  subtitle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: IconButton(
                  icon: const Icon(Icons.delete_outline),
                  tooltip: 'Delete',
                  onPressed: () async {
                    await controller.delete(a);
                    ref.invalidate(annotationsProvider(bookId));
                  },
                ),
                onTap: () => Navigator.pop(context, a),
              );
            },
          );
        },
      ),
    );
  }

  Color _dotColor(String? token) => switch (token) {
    'green' => const Color(0xFF22C55E),
    'blue' => const Color(0xFF3B82F6),
    'pink' => const Color(0xFFEC4899),
    'yellow' => const Color(0xFFEAB308),
    _ => const Color(0xFF8A988F),
  };

  void _showExport(BuildContext context, String markdown) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Export · Markdown'),
        content: SizedBox(
          width: double.maxFinite,
          child: SingleChildScrollView(
            child: SelectableText(
              markdown,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Clipboard.setData(ClipboardData(text: markdown));
              Navigator.pop(ctx);
            },
            child: const Text('Copy'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
