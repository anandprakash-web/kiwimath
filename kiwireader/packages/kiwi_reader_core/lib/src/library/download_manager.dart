import 'dart:async';

import 'catalog_book.dart';
import 'download_status.dart';
import 'offline_book_store.dart';

/// Produces the byte stream for a book. On device this wraps
/// `ContentProvider.bytes(book.id)`; tests inject a controllable stream. Kept as
/// a plain function so the core has zero dependency on Flutter or HTTP.
typedef DownloadSource = Future<Stream<List<int>>> Function(CatalogBook book);

/// Orchestrates **offline downloads**: a bounded-concurrency queue with live
/// progress, pause / cancel / remove / retry, and restart recovery.
///
/// Pure Dart and fully unit-tested — the riskiest part (the state machine) is
/// verified with no device, network, or Flutter, exactly like the sync engine.
/// Progress ticks are emitted on [updates] (cheap, in-memory); only terminal
/// states (`downloaded` / `failed` / `paused` / `notDownloaded`) are persisted
/// via [OfflineBookStore], so an interrupted download leaves no half-written
/// "offline" record.
class DownloadManager {
  DownloadManager({
    required OfflineBookStore store,
    required DownloadSource source,
    int maxConcurrent = 2,
  })  : _store = store,
        _source = source,
        _maxConcurrent = maxConcurrent;

  final OfflineBookStore _store;
  final DownloadSource _source;
  final int _maxConcurrent;

  final Map<String, DownloadStatus> _statuses = {};
  final Map<String, CatalogBook> _known = {};
  final List<String> _queue = [];
  final Set<String> _active = {};
  final Map<String, StreamSubscription<List<int>>> _subs = {};
  final Map<String, List<int>> _buffers = {};

  /// Per-book "generation" of the current download attempt. Bumped on every
  /// start and on pause/cancel/remove, so a completion/error callback (or a
  /// store write) that resolves after the user changed their mind is detected
  /// as stale and ignored. This closes the pause/cancel-vs-completion race.
  final Map<String, int> _gen = {};

  final StreamController<DownloadStatus> _updates =
      StreamController<DownloadStatus>.broadcast();

  /// Live per-book status updates: `queued`, every progress tick, and the
  /// terminal state. The Library UI binds to this.
  Stream<DownloadStatus> get updates => _updates.stream;

  /// Current statuses (unknown books default to `notDownloaded`).
  Map<String, DownloadStatus> get statuses =>
      Map<String, DownloadStatus>.unmodifiable(_statuses);

  DownloadStatus statusOf(String bookId) =>
      _statuses[bookId] ?? DownloadStatus.initial(bookId);

  /// Restore persisted statuses on startup. A download that was in flight when
  /// the app died (`queued`/`downloading`) is normalized back to
  /// `notDownloaded` — its bytes were never committed.
  Future<void> init() async {
    final loaded = await _store.loadStatuses();
    _statuses
      ..clear()
      ..addAll(loaded);
    for (final e in loaded.entries) {
      if (e.value.isActive) {
        _statuses[e.key] = DownloadStatus(bookId: e.key);
      }
    }
  }

  /// Queue a book for download. Also serves as **retry**/**resume**: calling it
  /// on a `failed`/`paused` book re-queues it. No-op if already downloaded at
  /// the catalog's current `contentVersion`, or already active/queued.
  Future<void> download(CatalogBook book) async {
    _known[book.id] = book;
    final cur = statusOf(book.id);
    if (cur.state == DownloadState.downloaded &&
        cur.version == book.contentVersion) {
      return;
    }
    if (cur.isActive || _queue.contains(book.id)) return;

    _emit(DownloadStatus(
      bookId: book.id,
      state: DownloadState.queued,
      totalBytes: book.byteSize,
    ));
    _queue.add(book.id);
    _pump();
  }

  void _pump() {
    while (_active.length < _maxConcurrent && _queue.isNotEmpty) {
      final id = _queue.removeAt(0);
      // Skip if it was paused/cancelled/removed while waiting in the queue.
      if (statusOf(id).state != DownloadState.queued) continue;
      _start(id);
    }
  }

  Future<void> _start(String id) async {
    final book = _known[id];
    if (book == null) return;
    final gen = (_gen[id] ?? 0) + 1;
    _gen[id] = gen;
    _active.add(id);
    _buffers[id] = <int>[];
    _emit(DownloadStatus(
      bookId: id,
      state: DownloadState.downloading,
      totalBytes: book.byteSize,
    ));
    try {
      final stream = await _source(book);
      // A pause/cancel/remove may have landed during the await above.
      if (_gen[id] != gen) return;
      _subs[id] = stream.listen(
        (chunk) {
          if (_gen[id] != gen) return;
          final buf = _buffers[id];
          if (buf == null) return;
          buf.addAll(chunk);
          _emit(statusOf(id).copyWith(
            state: DownloadState.downloading,
            receivedBytes: buf.length,
          ));
        },
        onError: (Object e) => _fail(id, gen, e),
        onDone: () => _complete(id, gen, book),
        cancelOnError: true,
      );
    } catch (e) {
      await _fail(id, gen, e);
    }
  }

  Future<void> _complete(String id, int gen, CatalogBook book) async {
    if (_gen[id] != gen) return;
    final bytes = List<int>.from(_buffers[id] ?? const <int>[]);
    await _store.putBytes(id, bytes);
    // If a pause/cancel/remove interleaved during the write, discard the bytes
    // and leave the user's chosen state untouched.
    if (_gen[id] != gen) {
      await _store.remove(id);
      return;
    }
    _cleanup(id);
    final status = DownloadStatus(
      bookId: id,
      state: DownloadState.downloaded,
      receivedBytes: bytes.length,
      totalBytes: book.byteSize ?? bytes.length,
      version: book.contentVersion,
    );
    await _store.saveStatus(status);
    _emit(status);
    _pump();
  }

  Future<void> _fail(String id, int gen, Object e) async {
    if (_gen[id] != gen) return;
    final received = _buffers[id]?.length ?? 0;
    _cleanup(id);
    final status = statusOf(id).copyWith(
      state: DownloadState.failed,
      error: e.toString(),
      receivedBytes: received,
    );
    await _store.saveStatus(status);
    _emit(status);
    _pump();
  }

  /// Pause an active or queued download (partial bytes are discarded; resume
  /// with [download]).
  Future<void> pause(String id) async {
    _queue.remove(id);
    _gen[id] = (_gen[id] ?? 0) + 1; // invalidate any in-flight completion
    _cleanup(id);
    final status = statusOf(id)
        .copyWith(state: DownloadState.paused, receivedBytes: 0, clearError: true);
    await _store.saveStatus(status);
    _emit(status);
    _pump();
  }

  /// Cancel a download entirely (back to `notDownloaded`).
  Future<void> cancel(String id) async {
    _queue.remove(id);
    _gen[id] = (_gen[id] ?? 0) + 1; // invalidate any in-flight completion
    _cleanup(id);
    final status = DownloadStatus(bookId: id);
    await _store.saveStatus(status);
    _emit(status);
    _pump();
  }

  /// Delete a book's offline copy (bytes + status) — frees device storage.
  Future<void> remove(String id) async {
    _queue.remove(id);
    _gen[id] = (_gen[id] ?? 0) + 1; // invalidate any in-flight completion
    _cleanup(id);
    await _store.remove(id);
    _emit(DownloadStatus(bookId: id));
    _pump();
  }

  /// The offline bytes for a book (null if not downloaded). The reader reads
  /// through this when a book is available offline.
  Future<List<int>?> bytesOf(String id) => _store.bytesOf(id);

  void _cleanup(String id) {
    _subs.remove(id)?.cancel();
    _buffers.remove(id);
    _active.remove(id);
  }

  void _emit(DownloadStatus status) {
    _statuses[status.bookId] = status;
    if (!_updates.isClosed) _updates.add(status);
  }

  Future<void> dispose() async {
    // Snapshot + clear before awaiting: a completion finishing mid-cancel
    // mutates _subs, which would crash an in-progress iteration.
    final subs = List.of(_subs.values);
    _subs.clear();
    _gen.updateAll((_, g) => g + 1); // invalidate any in-flight completions
    for (final s in subs) {
      await s.cancel();
    }
    await _updates.close();
  }
}
