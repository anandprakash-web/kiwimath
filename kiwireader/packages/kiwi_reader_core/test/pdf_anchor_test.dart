import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

void main() {
  group('PdfAnchorFactory geometry', () {
    test('normalizes selection rects and denormalizes to a render size', () {
      final anchor = PdfAnchorFactory.fromSelection(
        sectionId: 'page:42',
        page: 42,
        pageWidth: 600,
        pageHeight: 800,
        rects: const [RectD(60, 80, 540, 110)],
        quote: const TextQuoteSelector(exact: 'the derivative'),
      );

      final region = PdfAnchorFactory.regionOf(anchor)!;
      expect(region.page, 42);
      expect(region.rects.single.left, closeTo(0.1, 1e-9)); // 60/600
      expect(region.rects.single.top, closeTo(0.1, 1e-9)); // 80/800
      expect(region.rects.single.right, closeTo(0.9, 1e-9)); // 540/600
      expect(region.rects.single.bottom, closeTo(0.1375, 1e-9)); // 110/800

      // Render at half size: 300 x 400.
      final px =
          PdfAnchorFactory.rectsForPage(anchor, width: 300, height: 400).single;
      expect(px.left, closeTo(30, 1e-6));
      expect(px.top, closeTo(40, 1e-6));
      expect(px.right, closeTo(270, 1e-6));
      expect(px.bottom, closeTo(55, 1e-6));
    });

    test('round-trips through Anchor JSON (page + quads preserved)', () {
      final anchor = PdfAnchorFactory.fromSelection(
        sectionId: 'page:3',
        page: 3,
        pageWidth: 100,
        pageHeight: 200,
        rects: const [RectD(10, 20, 90, 40), RectD(10, 50, 60, 70)],
      );
      final back = Anchor.fromJson(anchor.toJson());
      final region = PdfAnchorFactory.regionOf(back)!;
      expect(region.page, 3);
      expect(region.rects.length, 2);
      expect(region.rects[1].left, closeTo(0.1, 1e-9));
    });

    test('scanned PDF (no text layer) makes a region-only anchor', () {
      final anchor = PdfAnchorFactory.fromSelection(
        sectionId: 'page:7',
        page: 7,
        pageWidth: 600,
        pageHeight: 800,
        rects: const [RectD(0, 0, 600, 800)],
        quote: null,
      );
      expect(anchor.quote, isNull);
      expect(PdfAnchorFactory.regionOf(anchor), isNotNull);
    });

    test('clamps out-of-bounds rects into the page', () {
      final anchor = PdfAnchorFactory.fromSelection(
        sectionId: 'page:1',
        page: 1,
        pageWidth: 100,
        pageHeight: 100,
        rects: const [RectD(-20, -10, 130, 110)],
      );
      final r = PdfAnchorFactory.regionOf(anchor)!.rects.single;
      expect(r.left, 0);
      expect(r.top, 0);
      expect(r.right, 1);
      expect(r.bottom, 1);
    });

    test('regionOf returns null for a non-PDF (text) anchor', () {
      const textAnchor = Anchor(
        sectionId: 'ch1',
        quote: TextQuoteSelector(exact: 'hello'),
      );
      expect(PdfAnchorFactory.regionOf(textAnchor), isNull);
      expect(PdfAnchorFactory.rectsForPage(textAnchor, width: 100, height: 100),
          isEmpty);
    });
  });
}
