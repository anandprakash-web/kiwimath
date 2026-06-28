import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// Monotonic UTC timestamps for deterministic tests.
DateTime t(int seconds) =>
    DateTime.utc(2026, 6, 18, 10, 0, 0).add(Duration(seconds: seconds));

/// Compact annotation builder for tests.
Annotation ann({
  String id = 'a1',
  String book = 'bk',
  AnnotationType type = AnnotationType.highlight,
  String? color = 'green',
  Anchor? anchor,
  String? note,
  int revision = 1,
  String device = 'devA',
  DateTime? created,
  DateTime? updated,
  DateTime? deleted,
}) =>
    Annotation(
      id: id,
      bookId: book,
      type: type,
      color: color,
      anchor: anchor ??
          const Anchor(sectionId: 'ch1', quote: TextQuoteSelector(exact: 'x')),
      noteText: note,
      revision: revision,
      deviceId: device,
      createdAt: created ?? t(0),
      updatedAt: updated ?? t(0),
      deletedAt: deleted,
    );
