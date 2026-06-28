import 'dart:convert';
import 'dart:io';

import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// On-device [OfflineBookStore]: downloaded bytes are written as files in a
/// directory and statuses are persisted to a small JSON index.
///
/// Mirrors the `JsonFileStore` pattern used for annotations — the unit-tested
/// `InMemoryOfflineBookStore` (in the core) is the reference, and both satisfy
/// the same interface, so the `DownloadManager` and the Library UI are
/// unchanged. Wire it on a device:
///
/// ```dart
/// final dir = '${(await getApplicationSupportDirectory()).path}/kiwi_books';
/// final store = await FileOfflineBookStore.open(dir);
/// // ProviderScope: offlineBookStoreProvider.overrideWithValue(store)
/// ```
class FileOfflineBookStore implements OfflineBookStore {
  final Directory _dir;
  final File _index;
  final Map<String, DownloadStatus> _statuses;

  FileOfflineBookStore._(this._dir, this._index, this._statuses);

  static Future<FileOfflineBookStore> open(String dirPath) async {
    final dir = Directory(dirPath);
    await dir.create(recursive: true);
    final index = File('${dir.path}/index.json');
    final statuses = <String, DownloadStatus>{};
    if (await index.exists()) {
      final raw = jsonDecode(await index.readAsString());
      if (raw is Map) {
        raw.forEach((k, v) {
          statuses[k as String] =
              DownloadStatus.fromJson(Map<String, dynamic>.from(v as Map));
        });
      }
    }
    return FileOfflineBookStore._(dir, index, statuses);
  }

  // Filesystem-safe, reversible per-book filename.
  File _blob(String bookId) =>
      File('${_dir.path}/${base64Url.encode(utf8.encode(bookId))}.bin');

  Future<void> _flushIndex() async {
    final map = {for (final e in _statuses.entries) e.key: e.value.toJson()};
    await _index.writeAsString(jsonEncode(map));
  }

  @override
  Future<Map<String, DownloadStatus>> loadStatuses() async =>
      Map<String, DownloadStatus>.from(_statuses);

  @override
  Future<void> saveStatus(DownloadStatus status) async {
    _statuses[status.bookId] = status;
    await _flushIndex();
  }

  @override
  Future<void> putBytes(String bookId, List<int> bytes) =>
      _blob(bookId).writeAsBytes(bytes, flush: true);

  @override
  Future<bool> hasBytes(String bookId) => _blob(bookId).exists();

  @override
  Future<List<int>?> bytesOf(String bookId) async {
    final f = _blob(bookId);
    return await f.exists() ? f.readAsBytes() : null;
  }

  @override
  Future<void> remove(String bookId) async {
    final f = _blob(bookId);
    if (await f.exists()) await f.delete();
    _statuses.remove(bookId);
    await _flushIndex();
  }
}
