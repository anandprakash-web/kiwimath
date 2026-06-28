import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

import 'helpers.dart';

void main() {
  group('Merge conflict matrix', () {
    test('newer edit wins (LWW), symmetric', () {
      final older = ann(color: 'green', updated: t(0), revision: 1);
      final newer = ann(color: 'yellow', updated: t(10), revision: 2);
      expect(Merge.resolve(older, newer).color, 'yellow');
      expect(Merge.resolve(newer, older).color, 'yellow');
    });

    test('tombstone beats a NEWER edit, symmetric', () {
      final deletedOld = ann(updated: t(0), deleted: t(0), revision: 1);
      final editNew = ann(color: 'yellow', updated: t(50), revision: 5);
      expect(Merge.resolve(editNew, deletedOld).isDeleted, isTrue);
      expect(Merge.resolve(deletedOld, editNew).isDeleted, isTrue);
    });

    test('both deleted -> later tombstone wins', () {
      final d1 = ann(deleted: t(1), updated: t(1));
      final d2 = ann(deleted: t(9), updated: t(9));
      expect(Merge.resolve(d1, d2).deletedAt, t(9));
      expect(Merge.resolve(d2, d1).deletedAt, t(9));
    });

    test('note keep-both merges divergent non-empty notes', () {
      final a = ann(
          type: AnnotationType.note,
          note: 'from A',
          updated: t(5),
          device: 'devA');
      final b = ann(
          type: AnnotationType.note,
          note: 'from B',
          updated: t(6),
          device: 'devB');
      final m = Merge.resolve(a, b);
      expect(m.noteText, contains('from A'));
      expect(m.noteText, contains('from B'));
      expect(m.revision, greaterThan(1));
    });

    test('identical note text does NOT trigger keep-both', () {
      final a = ann(type: AnnotationType.note, note: 'same', updated: t(5));
      final b = ann(type: AnnotationType.note, note: 'same', updated: t(6));
      expect(Merge.resolve(a, b).noteText, 'same');
    });

    test('identical-timestamp tiebreak is deterministic', () {
      final a = ann(color: 'green', updated: t(5), device: 'devA');
      final b = ann(color: 'blue', updated: t(5), device: 'devB');
      expect(Merge.resolve(a, b).color, Merge.resolve(b, a).color);
    });
  });
}
