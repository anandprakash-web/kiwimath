import '../models/annotation.dart';
import '../models/enums.dart';

/// Exports a book's annotations to Markdown — a study/revision sheet a student
/// can keep, share, or print to PDF. Pure Dart (no Flutter), so it is fully
/// unit-tested. The same grouped model can feed a PDF/HTML exporter on device.
class AnnotationExporter {
  static String _clean(String s) => s.replaceAll(RegExp(r'\s+'), ' ').trim();

  /// Group by `sectionId` (first-seen order), render each annotation, and skip
  /// soft-deleted records.
  static String toMarkdown(List<Annotation> annotations,
      {String title = 'My annotations'}) {
    final live = annotations.where((a) => !a.isDeleted).toList();

    var highlights = 0, notes = 0, bookmarks = 0;
    for (final a in live) {
      switch (a.type) {
        case AnnotationType.note:
          notes++;
        case AnnotationType.bookmark:
          bookmarks++;
        case AnnotationType.highlight:
        case AnnotationType.underline:
        case AnnotationType.strikethrough:
        case AnnotationType.ink:
          highlights++;
      }
    }

    final order = <String>[];
    final bySection = <String, List<Annotation>>{};
    for (final a in live) {
      final s = a.anchor.sectionId;
      if (!bySection.containsKey(s)) {
        bySection[s] = [];
        order.add(s);
      }
      bySection[s]!.add(a);
    }

    final buf = StringBuffer()
      ..writeln('# $title')
      ..writeln()
      ..writeln(
          '_$highlights highlight(s) · $notes note(s) · $bookmarks bookmark(s)_')
      ..writeln();

    for (final section in order) {
      buf
        ..writeln('## $section')
        ..writeln();
      for (final a in bySection[section]!) {
        switch (a.type) {
          case AnnotationType.bookmark:
            final label = (a.noteText?.isNotEmpty ?? false)
                ? ' — ${_clean(a.noteText!)}'
                : '';
            buf.writeln('- 🔖 Bookmark$label');
          case AnnotationType.note:
            final q = a.anchor.quote?.exact;
            if (q != null && q.isNotEmpty) buf.writeln('- > ${_clean(q)}');
            buf.writeln('  - 📝 ${_clean(a.noteText ?? '')}');
          case AnnotationType.highlight:
          case AnnotationType.underline:
          case AnnotationType.strikethrough:
          case AnnotationType.ink:
            final q = a.anchor.quote?.exact ?? '';
            final color = a.color != null ? ' _(${a.color})_' : '';
            buf.writeln('- > ${_clean(q)}$color');
        }
      }
      buf.writeln();
    }

    return '${buf.toString().trimRight()}\n';
  }
}
