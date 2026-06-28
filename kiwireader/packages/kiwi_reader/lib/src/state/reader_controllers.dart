import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:uuid/uuid.dart';

/// Public CRUD surface over annotations. Every write is optimistic: it lands in
/// the [LocalStore] (which enqueues to the outbox) first; sync is separate.
/// All the hard logic (merge, anchoring) lives in the tested core.
class AnnotationController {
  final String bookId;
  final LocalStore store;
  final SyncEngine syncEngine;
  final String deviceId;
  final Uuid _uuid = const Uuid();

  AnnotationController({
    required this.bookId,
    required this.store,
    required this.syncEngine,
    required this.deviceId,
  });

  Future<List<Annotation>> list() => store.all(bookId);

  Future<Annotation> createHighlight({
    required Anchor anchor,
    required String color,
  }) {
    final now = DateTime.now().toUtc();
    return store.put(
      Annotation(
        id: _uuid.v4(),
        bookId: bookId,
        type: AnnotationType.highlight,
        color: color,
        anchor: anchor,
        deviceId: deviceId,
        createdAt: now,
        updatedAt: now,
      ),
    );
  }

  Future<Annotation> addNote({
    required Anchor anchor,
    required String text,
    String? color,
  }) {
    final now = DateTime.now().toUtc();
    return store.put(
      Annotation(
        id: _uuid.v4(),
        bookId: bookId,
        type: AnnotationType.note,
        color: color,
        noteText: text,
        anchor: anchor,
        deviceId: deviceId,
        createdAt: now,
        updatedAt: now,
      ),
    );
  }

  Future<Annotation> recolor(Annotation a, String color) => store.put(
    a.copyWith(
      color: color,
      revision: a.revision + 1,
      updatedAt: DateTime.now().toUtc(),
    ),
  );

  Future<Annotation> editNote(Annotation a, String text) => store.put(
    a.copyWith(
      noteText: text,
      revision: a.revision + 1,
      updatedAt: DateTime.now().toUtc(),
    ),
  );

  /// Toggle a bookmark for [sectionId]: removes the existing one if present,
  /// otherwise creates it. Bookmarks reuse the annotation store/sync — they are
  /// just `AnnotationType.bookmark` records with no on-page geometry.
  Future<void> toggleBookmark({
    required String sectionId,
    String? label,
  }) async {
    final existing = (await store.all(bookId)).where(
      (a) =>
          a.type == AnnotationType.bookmark && a.anchor.sectionId == sectionId,
    );
    if (existing.isNotEmpty) {
      for (final a in existing) {
        await delete(a);
      }
      return;
    }
    final now = DateTime.now().toUtc();
    await store.put(
      Annotation(
        id: _uuid.v4(),
        bookId: bookId,
        type: AnnotationType.bookmark,
        noteText: label,
        anchor: Anchor(sectionId: sectionId),
        deviceId: deviceId,
        createdAt: now,
        updatedAt: now,
      ),
    );
  }

  /// Soft delete (tombstone). Recoverable until purged.
  Future<Annotation> delete(Annotation a) {
    final now = DateTime.now().toUtc();
    return store.put(
      a.copyWith(deletedAt: now, updatedAt: now, revision: a.revision + 1),
    );
  }

  Future<SyncOutcome> syncNow() => syncEngine.sync();

  /// Export this book's annotations as a Markdown revision sheet.
  Future<String> exportMarkdown({String title = 'My annotations'}) async =>
      AnnotationExporter.toMarkdown(await store.all(bookId), title: title);
}
