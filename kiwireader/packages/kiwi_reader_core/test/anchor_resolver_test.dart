import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

void main() {
  const resolver = AnchorResolver();
  const text =
      'In calculus, the derivative measures the instantaneous rate of change. '
      'Later, the derivative appears again in a different sentence.';

  group('AnchorResolver decision tree', () {
    test('1) structural valid + quote agrees -> resolved', () {
      final start = text.indexOf('the derivative measures');
      final anchor = Anchor(
        sectionId: 'ch1',
        structural: const StructuralSelector(LocatorType.domRange, {'p': 1}),
        quote: const TextQuoteSelector(exact: 'the derivative measures'),
      );
      final content = SectionContent(
        sectionId: 'ch1',
        text: text,
        structuralValid: true,
        structuralStart: start,
        structuralEnd: start + 'the derivative measures'.length,
      );
      final r = resolver.resolve(anchor, content);
      expect(r.state, AnchorState.resolved);
      expect(r.start, start);
      expect(r.anchor.state, AnchorState.resolved);
    });

    test('2) structural stale -> relocated by quote -> repaired', () {
      final anchor = Anchor(
        sectionId: 'ch1',
        structural: const StructuralSelector(LocatorType.domRange, {'p': 1}),
        quote: const TextQuoteSelector(exact: 'instantaneous rate'),
      );
      // Structural claims offset 0..5 where the quote is NOT present.
      final content = SectionContent(
        sectionId: 'ch1',
        text: text,
        structuralValid: true,
        structuralStart: 0,
        structuralEnd: 5,
      );
      final r = resolver.resolve(anchor, content);
      expect(r.state, AnchorState.repaired);
      expect(text.substring(r.start!, r.end!), 'instantaneous rate');
    });

    test('2) no structural, unique quote -> repaired', () {
      final anchor = const Anchor(
        sectionId: 'ch1',
        quote: TextQuoteSelector(exact: 'instantaneous rate'),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: text));
      expect(r.state, AnchorState.repaired);
      expect(text.substring(r.start!, r.end!), 'instantaneous rate');
    });

    test('3) repeated quote disambiguated by position', () {
      final firstIdx = text.indexOf('the derivative');
      final secondIdx = text.indexOf('the derivative', firstIdx + 1);
      final anchor = Anchor(
        sectionId: 'ch1',
        quote: const TextQuoteSelector(exact: 'the derivative'),
        position: TextPositionSelector(secondIdx, secondIdx + 14),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: text));
      expect(r.state, AnchorState.repaired);
      expect(r.start, secondIdx);
    });

    test('3) repeated quote disambiguated by prefix/suffix context', () {
      final anchor = const Anchor(
        sectionId: 'ch1',
        quote: TextQuoteSelector(
            exact: 'the derivative', prefix: 'Later, ', suffix: ' appears'),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: text));
      final expected = text.indexOf('Later, the derivative') + 'Later, '.length;
      expect(r.start, expected);
    });

    test('4) minor edit (typo) -> fuzzy -> approx', () {
      final anchor = const Anchor(
        sectionId: 'ch1',
        // "instantaneus" is a 1-char deletion from "instantaneous".
        quote: TextQuoteSelector(
            exact: 'the derivative measures the instantaneus rate'),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: text));
      expect(r.state, AnchorState.approx);
      expect(r.located, isTrue);
    });

    test('5) position-only anchor (no quote) -> approx', () {
      final anchor =
          const Anchor(sectionId: 'ch1', position: TextPositionSelector(3, 12));
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: text));
      expect(r.state, AnchorState.approx);
      expect(r.start, 3);
    });

    test('6) quote gone -> orphaned (data kept, never misplaced)', () {
      final anchor = const Anchor(
        sectionId: 'ch1',
        quote: TextQuoteSelector(
            exact: 'a completely unrelated phrase about giraffes'),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: text));
      expect(r.state, AnchorState.orphaned);
      expect(r.located, isFalse);
      expect(r.anchor.state, AnchorState.orphaned);
    });

    test('whitespace reflow does not break the exact quote (canonicalization)',
        () {
      const messy =
          'In   calculus,\n\tthe derivative   measures\n the instantaneous rate of change.';
      final anchor = const Anchor(
        sectionId: 'ch1',
        quote: TextQuoteSelector(
            exact: 'the derivative measures the instantaneous rate'),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'ch1', text: messy));
      expect(r.state, AnchorState.repaired);
    });

    test('EPUB-style anchor (CFI structural + quote) relocates by quote', () {
      // Mirrors EpubRenderer.buildAnchor: structural = CFI, quote = text.
      // A CFI can't be validated in pure Dart, so resolution takes the quote
      // path — proving EPUB highlights survive a re-flow the same way HTML does.
      const anchor = Anchor(
        sectionId: 'OEBPS/ch3.xhtml',
        structural: StructuralSelector(LocatorType.cfi, {
          'cfi': 'epubcfi(/6/14!/4/2/14,/1:12,/1:58)',
        }),
        quote: TextQuoteSelector(exact: 'instantaneous rate'),
      );
      final r = resolver.resolve(
          anchor, SectionContent(sectionId: 'OEBPS/ch3.xhtml', text: text));
      expect(r.state, AnchorState.repaired);
      expect(text.substring(r.start!, r.end!), 'instantaneous rate');
    });
  });
}
