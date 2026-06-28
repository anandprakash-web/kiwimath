import '../models/annotation.dart';
import '../sync/merge.dart';

/// The local persistence contract. On device this is backed by Drift/Isar;
/// the engine and tests depend only on this interface.
abstract class LocalStore {
  Future<List<Annotation>> all(String bookId, {bool includeDeleted = false});
  Future<Annotation?> get(String id);

  /// Local optimistic write: merges with any existing record and enqueues the
  /// id to the outbox for the next sync.
  Future<Annotation> put(Annotation a);

  /// Apply records pulled from the server. Merges with local; only re-enqueues
  /// to the outbox when the merge produced something the server lacks
  /// (e.g. a note keep-both, or a locally-newer field).
  Future<void> applyRemote(Iterable<Annotation> remote);

  Future<List<Annotation>> outbox();
  Future<void> clearOutbox(Iterable<String> ids);

  /// The opaque, monotonically-increasing server cursor of the last successful
  /// pull (null before the first sync). NOT a wall-clock value.
  Future<int?> lastCursor();
  Future<void> setCursor(int cursor);
}

/// Reference in-memory implementation used by tests and early development.
class InMemoryLocalStore implements LocalStore {
  final Map<String, Annotation> _items = {};
  final Set<String> _outbox = {};
  int? _cursor;

  @override
  Future<List<Annotation>> all(String bookId,
          {bool includeDeleted = false}) async =>
      _items.values
          .where((a) => a.bookId == bookId && (includeDeleted || !a.isDeleted))
          .toList();

  @override
  Future<Annotation?> get(String id) async => _items[id];

  @override
  Future<Annotation> put(Annotation a) async {
    final existing = _items[a.id];
    final merged = existing == null ? a : Merge.resolve(a, existing);
    _items[a.id] = merged;
    _outbox.add(a.id);
    return merged;
  }

  @override
  Future<void> applyRemote(Iterable<Annotation> remote) async {
    for (final r in remote) {
      final existing = _items[r.id];
      final merged = existing == null ? r : Merge.resolve(r, existing);
      _items[r.id] = merged;
      if (merged != r)
        _outbox.add(r.id); // we owe the server our merged version
    }
  }

  @override
  Future<List<Annotation>> outbox() async =>
      _outbox.map((id) => _items[id]).whereType<Annotation>().toList();

  @override
  Future<void> clearOutbox(Iterable<String> ids) async =>
      _outbox.removeAll(ids.toSet());

  @override
  Future<int?> lastCursor() async => _cursor;

  @override
  Future<void> setCursor(int cursor) async => _cursor = cursor;
}
