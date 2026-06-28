/// Lifecycle of a book's **offline copy**.
///
/// ```
/// notDownloaded ──download()──▶ queued ──(slot free)──▶ downloading ──done──▶ downloaded
///        ▲                         │                        │  │
///        │                      cancel()                pause()│ (stream error)
///        │                         ▼                        ▼  ▼
///        └─────────── remove() ── (notDownloaded) ◀── paused   failed ──retry()──▶ queued
/// ```
enum DownloadState {
  /// No offline copy and not in the queue.
  notDownloaded,

  /// Requested; waiting for a concurrency slot.
  queued,

  /// Bytes are streaming in.
  downloading,

  /// User paused an in-progress download (partial bytes discarded).
  paused,

  /// Fully downloaded and available offline.
  downloaded,

  /// The download failed; [DownloadStatus.error] explains why. Retryable.
  failed,
}

/// Immutable snapshot of one book's download/offline state. Pure data — the
/// `DownloadManager` produces these and persists them via `OfflineBookStore`,
/// and the Library UI binds to them. JSON round-trips so the state survives an
/// app restart.
class DownloadStatus {
  final String bookId;
  final DownloadState state;
  final int receivedBytes;
  final int? totalBytes;
  final String? error;

  /// `contentVersion` of the bytes currently on disk. Lets the UI detect when
  /// an offline copy is stale relative to the catalog and offer a refresh.
  final String? version;

  const DownloadStatus({
    required this.bookId,
    this.state = DownloadState.notDownloaded,
    this.receivedBytes = 0,
    this.totalBytes,
    this.error,
    this.version,
  });

  factory DownloadStatus.initial(String bookId) =>
      DownloadStatus(bookId: bookId);

  bool get isAvailableOffline => state == DownloadState.downloaded;

  bool get isActive =>
      state == DownloadState.queued || state == DownloadState.downloading;

  /// Fractional progress in `0.0..1.0`, or `null` when the total size is
  /// unknown (show an indeterminate spinner). Always `1.0` once downloaded.
  double? get progress {
    if (state == DownloadState.downloaded) return 1.0;
    final t = totalBytes;
    if (t == null || t <= 0) return null;
    final p = receivedBytes / t;
    if (p < 0) return 0.0;
    if (p > 1) return 1.0;
    return p;
  }

  DownloadStatus copyWith({
    DownloadState? state,
    int? receivedBytes,
    int? totalBytes,
    String? error,
    String? version,
    bool clearError = false,
    bool clearTotal = false,
  }) =>
      DownloadStatus(
        bookId: bookId,
        state: state ?? this.state,
        receivedBytes: receivedBytes ?? this.receivedBytes,
        totalBytes: clearTotal ? null : (totalBytes ?? this.totalBytes),
        error: clearError ? null : (error ?? this.error),
        version: version ?? this.version,
      );

  Map<String, dynamic> toJson() => {
        'bookId': bookId,
        'state': state.name,
        'receivedBytes': receivedBytes,
        if (totalBytes != null) 'totalBytes': totalBytes,
        if (error != null) 'error': error,
        if (version != null) 'version': version,
      };

  factory DownloadStatus.fromJson(Map<String, dynamic> j) => DownloadStatus(
        bookId: j['bookId'] as String,
        state: DownloadState.values.byName(j['state'] as String),
        receivedBytes: (j['receivedBytes'] as num?)?.toInt() ?? 0,
        totalBytes: (j['totalBytes'] as num?)?.toInt(),
        error: j['error'] as String?,
        version: j['version'] as String?,
      );

  @override
  bool operator ==(Object other) =>
      other is DownloadStatus &&
      other.bookId == bookId &&
      other.state == state &&
      other.receivedBytes == receivedBytes &&
      other.totalBytes == totalBytes &&
      other.error == error &&
      other.version == version;

  @override
  int get hashCode =>
      Object.hash(bookId, state, receivedBytes, totalBytes, error, version);

  @override
  String toString() =>
      'DownloadStatus($bookId, ${state.name}, $receivedBytes/$totalBytes)';
}
