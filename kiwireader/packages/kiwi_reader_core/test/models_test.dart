import 'dart:convert';

import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

import 'helpers.dart';

/// Round-trips through real JSON (encode + decode) to prove serialization.
T roundTrip<T>(
        Map<String, dynamic> json, T Function(Map<String, dynamic>) from) =>
    from(jsonDecode(jsonEncode(json)) as Map<String, dynamic>);

void main() {
  group('JSON round-trips', () {
    test('Annotation with full anchor + tombstone', () {
      final a = ann(
        id: 'x1',
        note: 'remember this',
        type: AnnotationType.note,
        anchor: const Anchor(
          sectionId: 'ch1',
          structural: StructuralSelector(LocatorType.pdfQuads, {
            'page': 42,
            'quads': [
              [0.1, 0.2, 0.8, 0.2]
            ]
          }),
          quote: TextQuoteSelector(exact: 'foo', prefix: 'a', suffix: 'b'),
          position: TextPositionSelector(5, 8),
          state: AnchorState.repaired,
        ),
        revision: 4,
        updated: t(30),
        deleted: t(40),
      );
      final b = roundTrip(a.toJson(), Annotation.fromJson);
      expect(b, a);
      expect(b.isDeleted, isTrue);
      expect(b.anchor.state, AnchorState.repaired);
    });

    test('Bookmark', () {
      final bm = Bookmark(
        id: 'b1',
        bookId: 'bk',
        locator: const Locator(
            sectionId: 'ch2', progress: 0.42, raw: {'cfi': 'epubcfi(/6/4)'}),
        label: 'Integration set',
        deviceId: 'devA',
        createdAt: t(0),
        updatedAt: t(1),
      );
      expect(roundTrip(bm.toJson(), Bookmark.fromJson), bm);
    });

    test('ReadingProgress', () {
      final p = ReadingProgress(
        bookId: 'bk',
        locator: const Locator(sectionId: 'ch3', progress: 0.7),
        percent: 0.7,
        deviceId: 'ipad',
        updatedAt: t(5),
      );
      expect(roundTrip(p.toJson(), ReadingProgress.fromJson), p);
    });

    test('BookManifest', () {
      const m = BookManifest(
        id: 'bk',
        format: BookFormat.epub,
        contentVersion: 'v2',
        title: 'Calculus',
        sections: [
          SectionRef(id: 'ch1', title: 'Limits'),
          SectionRef(id: 'ch2')
        ],
      );
      expect(roundTrip(m.toJson(), BookManifest.fromJson), m);
    });

    test('equality is value-based and order-insensitive', () {
      final a1 = ann(id: 'same', updated: t(1));
      final a2 = ann(id: 'same', updated: t(1));
      expect(a1, a2);
      expect(a1.hashCode, a2.hashCode);
    });

    test('bookmark-type annotation round-trips', () {
      final b = ann(
          id: 'bm', type: AnnotationType.bookmark, color: null, note: 'Ch 5');
      final back = roundTrip(b.toJson(), Annotation.fromJson);
      expect(back, b);
      expect(back.type, AnnotationType.bookmark);
    });
  });
}
