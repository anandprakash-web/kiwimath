import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

void main() {
  const resolver = AnchorResolver();
  const text =
      'In calculus, the derivative measures the instantaneous rate of change. '
      'Later, the derivative appears again in a different sentence.';

  SectionContent content({
    bool structuralValid = false,
    int? sStart,
    int? sEnd,
    String? src,
  }) =>
      SectionContent(
        sectionId: 'ch1',
        text: src ?? text,
        structuralValid: structuralValid,
        structuralStart: sStart,
        structuralEnd: sEnd,
      );

  group('AnchorFactory + AnchorResolver round-trip', () {
    test('valid structural on next render -> resolved, same range', () {
      final c = content();
      final start = c.canonical.indexOf('instantaneous rate');
      final end = start + 'instantaneous rate'.length;
      final anchor = AnchorFactory.fromSelection(
        content: c,
        start: start,
        end: end,
        structural: const StructuralSelector(LocatorType.domRange, {'r': 1}),
      );
      final next = content(structuralValid: true, sStart: start, sEnd: end);
      final r = resolver.resolve(anchor, next);
      expect(r.state, AnchorState.resolved);
      expect(r.start, start);
      expect(next.canonical.substring(r.start!, r.end!), 'instantaneous rate');
    });

    test('survives whitespace reflow (structural invalid) -> repaired', () {
      final c = content();
      final start = c.canonical.indexOf('instantaneous rate');
      final anchor = AnchorFactory.fromSelection(
        content: c,
        start: start,
        end: start + 'instantaneous rate'.length,
      );
      final messy = content(
        src: 'In   calculus,\n\tthe derivative   measures\n the instantaneous '
            'rate of change. Later, the derivative appears again.',
      );
      final r = resolver.resolve(anchor, messy);
      expect(r.state, AnchorState.repaired);
      expect(messy.canonical.substring(r.start!, r.end!), 'instantaneous rate');
    });

    test('survives a content edit that shifts offsets -> repaired', () {
      final c = content();
      final start = c.canonical.indexOf('instantaneous rate');
      final anchor = AnchorFactory.fromSelection(
        content: c,
        start: start,
        end: start + 'instantaneous rate'.length,
      );
      final edited =
          content(src: 'A NEW INTRO PARAGRAPH WAS ADDED FIRST. $text');
      final r = resolver.resolve(anchor, edited);
      expect(r.state, AnchorState.repaired);
      expect(
          edited.canonical.substring(r.start!, r.end!), 'instantaneous rate');
      expect(r.start, isNot(start)); // offsets really did move
    });

    test('disambiguates a repeated phrase via captured prefix/suffix', () {
      const src = 'the cat sat on the mat. the cat ran to the park.';
      final c = SectionContent(sectionId: 'ch1', text: src);
      final secondStart = src.indexOf('the cat', src.indexOf('the cat') + 1);
      final anchor = AnchorFactory.fromSelection(
        content: c,
        start: secondStart,
        end: secondStart + 'the cat'.length,
      );
      final r = resolver.resolve(anchor, c);
      expect(r.start, secondStart);
    });

    test('selection at the very start (empty prefix) round-trips', () {
      final c = content();
      final anchor = AnchorFactory.fromSelection(
          content: c, start: 0, end: 'In calculus'.length);
      expect(anchor.quote!.prefix, isNull);
      final r = resolver.resolve(anchor, c);
      expect(r.located, isTrue);
      expect(c.canonical.substring(r.start!, r.end!), 'In calculus');
    });

    test('rejects an invalid (empty) selection', () {
      final c = content();
      expect(
        () => AnchorFactory.fromSelection(content: c, start: 5, end: 5),
        throwsRangeError,
      );
    });
  });
}
