import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

import 'helpers.dart';

void main() {
  Annotation withAnchor(String id, AnnotationType type, String section,
          {String? quote, String? color, String? note, DateTime? deleted}) =>
      ann(
        id: id,
        type: type,
        color: color,
        note: note,
        deleted: deleted,
        anchor: Anchor(
          sectionId: section,
          quote: quote == null ? null : TextQuoteSelector(exact: quote),
        ),
      );

  test('renders sections, quotes, notes, bookmarks; excludes deleted', () {
    final md = AnnotationExporter.toMarkdown([
      withAnchor('h1', AnnotationType.highlight, 'ch1',
          quote: 'the derivative', color: 'green'),
      withAnchor('n1', AnnotationType.note, 'ch1',
          quote: 'slope of tangent', note: 'revise this'),
      withAnchor('b1', AnnotationType.bookmark, 'ch2', note: 'Integration set'),
      withAnchor('d1', AnnotationType.highlight, 'ch1',
          quote: 'SECRET DELETED', deleted: t(9)),
    ], title: 'Calculus notes');

    expect(md, contains('# Calculus notes'));
    expect(md, contains('1 highlight(s) · 1 note(s) · 1 bookmark(s)'));
    expect(md, contains('## ch1'));
    expect(md, contains('## ch2'));
    expect(md, contains('> the derivative'));
    expect(md, contains('_(green)_'));
    expect(md, contains('📝 revise this'));
    expect(md, contains('🔖 Bookmark — Integration set'));
    expect(md, isNot(contains('SECRET DELETED'))); // deleted excluded
  });

  test('groups by section in first-seen order', () {
    final md = AnnotationExporter.toMarkdown([
      withAnchor('a', AnnotationType.highlight, 'intro', quote: 'alpha'),
      withAnchor('b', AnnotationType.highlight, 'later', quote: 'beta'),
      withAnchor('c', AnnotationType.highlight, 'intro', quote: 'gamma'),
    ]);
    expect(md.indexOf('## intro'), lessThan(md.indexOf('## later')));
    // both 'intro' items render under the single intro header
    final introBlock =
        md.substring(md.indexOf('## intro'), md.indexOf('## later'));
    expect(introBlock, contains('alpha'));
    expect(introBlock, contains('gamma'));
  });

  test('collapses whitespace/newlines inside a quote', () {
    final md = AnnotationExporter.toMarkdown([
      withAnchor('h', AnnotationType.highlight, 'ch1',
          quote: 'line one\n   line two'),
    ]);
    expect(md, contains('> line one line two'));
  });
}
