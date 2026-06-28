import 'dart:convert';
import 'dart:io';

import '../models/annotation.dart';
import '../store/local_store.dart';
import '../sync/merge.dart';

/// A real, restart-surviving [LocalStore] backed by a single JSON file.
///
/// Pure Dart + dart:io, so it runs in tests, on desktop, and on a server (and
/// is a perfectly good fallback store). On mobile the production app swaps in a
/// Drift/sqlite store (ticket KR-025) — same interface, so nothing above the
/// store changes. Writes are flushed on every mutation.
class JsonFileStore implements LocalStore {
  final File _file;
  final Map<String, Annotation> _items;
  final Set<String> _outbox;
  int? _cursor;

  JsonFileStore._(this._file, this._items, this._outbox, this._cursor);

  /// Opens (and loads) the store at [path], creating an empty one if absent.
  static Future<JsonFileStore> open(String path) async {
    final file = File(path);
    if (await file.exists()) {
      final data =
          jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      final items = <String, Annotation>{};
      for (final m in (data['items'] as List? ?? const [])) {
        final a = Annotation.fromJson(Map<String, dynamic>.from(m as Map));
        items[a.id] = a;
      }
      final outbox = ((data['outbox'] as List?) ?? const [])
          .map((e) => e as String)
          .toSet();
      final cursor = (data['cursor'] as num?)?.toInt();
      return JsonFileStore._(file, items, outbox, cursor);
    }
    return JsonFileStore._(file, {}, {}, null);
  }

  Future<void> _flush() async {
    await _file.writeAsString(
      jsonEncode({
        'items': _items.values.map((a) => a.toJson()).toList(),
        'outbox': _outbox.toList(),
        'cursor': _cursor,
      }),
      flush: true,
    );
  }

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
    await _flush();
    return merged;
  }

  @override
  Future<void> applyRemote(Iterable<Annotation> remote) async {
    for (final r in remote) {
      final existing = _items[r.id];
      final merged = existing == null ? r : Merge.resolve(r, existing);
      _items[r.id] = merged;
      if (merged != r) _outbox.add(r.id);
    }
    await _flush();
  }

  @override
  Future<List<Annotation>> outbox() async =>
      _outbox.map((id) => _items[id]).whereType<Annotation>().toList();

  @override
  Future<void> clearOutbox(Iterable<String> ids) async {
    _outbox.removeAll(ids.toSet());
    await _flush();
  }

  @override
  Future<int?> lastCursor() async => _cursor;

  @override
  Future<void> setCursor(int cursor) async {
    _cursor = cursor;
    await _flush();
  }
}
