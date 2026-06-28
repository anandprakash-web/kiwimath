import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../host/providers.dart';

/// Decorates the host's [ContentProvider] so that once a book is downloaded the
/// reader streams its bytes from the [OfflineBookStore] instead of the network
/// — this is what makes downloaded books readable offline. Manifest and cover
/// still come from the inner provider (cheap and independently cacheable).
///
/// Wire it by overriding `contentProviderRef`:
/// ```dart
/// contentProviderRef.overrideWith((ref) => OfflineFirstContentProvider(
///       realProvider, ref.watch(offlineBookStoreProvider)));
/// ```
///
/// IMPORTANT: this must read from the **same** `OfflineBookStore` instance the
/// `DownloadManager` writes to (always resolve both from
/// `offlineBookStoreProvider`). If two different stores are used, downloaded
/// books will silently fall through to the network and fail offline.
class OfflineFirstContentProvider implements ContentProvider {
  final ContentProvider _inner;
  final OfflineBookStore _offline;

  OfflineFirstContentProvider(this._inner, this._offline);

  @override
  Future<BookManifest> manifest(String bookId) => _inner.manifest(bookId);

  @override
  Future<Uri?> coverImage(String bookId) => _inner.coverImage(bookId);

  @override
  Future<ByteStream> bytes(String bookId, {ByteRange? range}) async {
    // Ranged reads (e.g. partial PDF) bypass the full-file cache.
    if (range == null) {
      final cached = await _offline.bytesOf(bookId);
      if (cached != null) return Stream<List<int>>.value(cached);
    }
    return _inner.bytes(bookId, range: range);
  }
}
