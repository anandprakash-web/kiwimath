import 'download_status.dart';

/// Persistence seam for offline books: the downloaded **bytes** plus each
/// book's [DownloadStatus]. The `DownloadManager` orchestrates downloads and
/// talks only to this interface, so the on-device implementation (a file store)
/// and the unit-test reference ([InMemoryOfflineBookStore]) are
/// interchangeable — exactly like `LocalStore` for annotations.
abstract class OfflineBookStore {
  /// Restore every persisted status on startup (keyed by `bookId`).
  Future<Map<String, DownloadStatus>> loadStatuses();

  /// Persist one status (called on every meaningful transition).
  Future<void> saveStatus(DownloadStatus status);

  /// Commit the fully-downloaded bytes for a book.
  Future<void> putBytes(String bookId, List<int> bytes);

  Future<bool> hasBytes(String bookId);

  /// The offline bytes for a book, or null if not downloaded. The reader's
  /// `ContentProvider` reads through this when offline.
  Future<List<int>?> bytesOf(String bookId);

  /// Delete the bytes and the status for a book (back to `notDownloaded`).
  Future<void> remove(String bookId);
}

/// In-memory reference implementation used by tests and early development.
class InMemoryOfflineBookStore implements OfflineBookStore {
  final Map<String, DownloadStatus> _statuses = {};
  final Map<String, List<int>> _bytes = {};

  @override
  Future<Map<String, DownloadStatus>> loadStatuses() async =>
      Map<String, DownloadStatus>.from(_statuses);

  @override
  Future<void> saveStatus(DownloadStatus status) async =>
      _statuses[status.bookId] = status;

  @override
  Future<void> putBytes(String bookId, List<int> bytes) async =>
      _bytes[bookId] = List<int>.from(bytes);

  @override
  Future<bool> hasBytes(String bookId) async => _bytes.containsKey(bookId);

  @override
  Future<List<int>?> bytesOf(String bookId) async => _bytes[bookId];

  @override
  Future<void> remove(String bookId) async {
    _statuses.remove(bookId);
    _bytes.remove(bookId);
  }
}
