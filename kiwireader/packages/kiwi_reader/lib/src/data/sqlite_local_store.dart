import 'dart:convert';

import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:sqflite/sqflite.dart';

/// On-device [LocalStore] backed by SQLite (`sqflite`, no code-gen). This is
/// the production mobile store; `JsonFileStore` (in the core's io entrypoint)
/// is the unit-tested reference used on desktop/CI. Both implement the exact
/// same interface, so `SyncEngine`, the controllers and the UI are unchanged —
/// wire it by overriding `localStoreProvider`:
///
/// ```dart
/// final store = await SqliteLocalStore.open(await _dbPath());
/// // localStoreProvider.overrideWithValue(store)
/// ```
///
/// The full annotation is stored as JSON; columns mirror the query/merge needs
/// (bookId, deleted, outbox, updatedAt) so reads stay indexed.
class SqliteLocalStore implements LocalStore {
  final Database _db;
  SqliteLocalStore._(this._db);

  static Future<SqliteLocalStore> open(String path) async {
    final db = await openDatabase(
      path,
      version: 1,
      onCreate: (db, _) async {
        await db.execute('''
          CREATE TABLE annotations (
            id TEXT PRIMARY KEY,
            bookId TEXT NOT NULL,
            json TEXT NOT NULL,
            updatedAt TEXT NOT NULL,
            deleted INTEGER NOT NULL DEFAULT 0,
            inOutbox INTEGER NOT NULL DEFAULT 0
          )''');
        await db.execute('CREATE INDEX idx_ann_book ON annotations(bookId)');
        await db.execute(
          'CREATE INDEX idx_ann_outbox ON annotations(inOutbox)',
        );
        await db.execute(
          'CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)',
        );
      },
    );
    return SqliteLocalStore._(db);
  }

  Future<void> close() => _db.close();

  Annotation _decode(Map<String, Object?> row) => Annotation.fromJson(
    jsonDecode(row['json']! as String) as Map<String, dynamic>,
  );

  Future<void> _write(Annotation a, {required bool inOutbox}) =>
      _db.insert('annotations', {
        'id': a.id,
        'bookId': a.bookId,
        'json': jsonEncode(a.toJson()),
        'updatedAt': a.updatedAt.toUtc().toIso8601String(),
        'deleted': a.isDeleted ? 1 : 0,
        'inOutbox': inOutbox ? 1 : 0,
      }, conflictAlgorithm: ConflictAlgorithm.replace);

  Future<bool> _isOutbox(String id) async {
    final rows = await _db.query(
      'annotations',
      columns: ['inOutbox'],
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    return rows.isNotEmpty && (rows.first['inOutbox'] as int) == 1;
  }

  @override
  Future<List<Annotation>> all(
    String bookId, {
    bool includeDeleted = false,
  }) async {
    final rows = await _db.query(
      'annotations',
      where: includeDeleted ? 'bookId = ?' : 'bookId = ? AND deleted = 0',
      whereArgs: [bookId],
    );
    return rows.map(_decode).toList();
  }

  @override
  Future<Annotation?> get(String id) async {
    final rows = await _db.query(
      'annotations',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    return rows.isEmpty ? null : _decode(rows.first);
  }

  @override
  Future<Annotation> put(Annotation a) async {
    final existing = await get(a.id);
    final merged = existing == null ? a : Merge.resolve(a, existing);
    await _write(merged, inOutbox: true);
    return merged;
  }

  @override
  Future<void> applyRemote(Iterable<Annotation> remote) async {
    for (final r in remote) {
      final existing = await get(r.id);
      final merged = existing == null ? r : Merge.resolve(r, existing);
      // Re-enqueue only if our merge changed the record vs the server's copy.
      final outbox = merged != r ? true : await _isOutbox(r.id);
      await _write(merged, inOutbox: outbox);
    }
  }

  @override
  Future<List<Annotation>> outbox() async {
    final rows = await _db.query('annotations', where: 'inOutbox = 1');
    return rows.map(_decode).toList();
  }

  @override
  Future<void> clearOutbox(Iterable<String> ids) async {
    final batch = _db.batch();
    for (final id in ids) {
      batch.update(
        'annotations',
        {'inOutbox': 0},
        where: 'id = ?',
        whereArgs: [id],
      );
    }
    await batch.commit(noResult: true);
  }

  @override
  Future<int?> lastCursor() async {
    final rows = await _db.query(
      'meta',
      where: 'k = ?',
      whereArgs: ['cursor'],
      limit: 1,
    );
    return rows.isEmpty ? null : int.tryParse(rows.first['v']! as String);
  }

  @override
  Future<void> setCursor(int cursor) => _db.insert('meta', {
    'k': 'cursor',
    'v': '$cursor',
  }, conflictAlgorithm: ConflictAlgorithm.replace);
}
