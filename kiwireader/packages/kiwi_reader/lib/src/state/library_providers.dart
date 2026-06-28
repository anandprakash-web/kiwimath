import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../host/providers.dart';
import 'reader_providers.dart';

/// === Library wiring =======================================================
/// The Library tab is built from three things, all reusing existing seams:
///   • `catalogProviderRef`     — the backend book list (host-supplied),
///   • `contentProviderRef`     — already used by the reader, reused for bytes,
///   • `offlineBookStoreProvider` — where downloaded bytes + statuses live.
/// The pure-Dart `DownloadManager` ties them together; the UI binds to its
/// status stream.

/// Host-supplied catalog. Throws until overridden so a missing wiring fails
/// loudly at startup (same convention as the reader's host providers).
final catalogProviderRef = Provider<CatalogProvider>(
  (ref) => throw UnimplementedError(
    'Override catalogProviderRef in the host ProviderScope.',
  ),
);

/// Offline byte + status store. Defaults to in-memory for dev/tests; the host
/// overrides with `FileOfflineBookStore.open(dir)` on a real device so
/// downloads survive restarts.
final offlineBookStoreProvider = Provider<OfflineBookStore>(
  (ref) => InMemoryOfflineBookStore(),
);

/// The single app-wide download orchestrator. Streams a book's bytes through
/// the host's [ContentProvider] into the offline store, capped at two parallel
/// downloads. Restores persisted statuses on creation.
final downloadManagerProvider = Provider<DownloadManager>((ref) {
  final content = ref.watch(contentProviderRef);
  final manager = DownloadManager(
    store: ref.watch(offlineBookStoreProvider),
    source: (book) => content.bytes(book.id),
  );
  // Fire-and-forget restore; the UI binds to [updates] and rebuilds when ready.
  unawaited(manager.init());
  ref.onDispose(manager.dispose);
  return manager;
});

/// The catalog list. Pull-to-refresh calls `ref.refresh(libraryCatalogProvider)`.
final libraryCatalogProvider = FutureProvider<List<CatalogBook>>(
  (ref) => ref.watch(catalogProviderRef).books(),
);

/// Live `bookId -> DownloadStatus` map, re-emitted on every progress tick. The
/// grid watches this so cards animate as downloads progress.
final downloadStatusesProvider =
    StreamProvider<Map<String, DownloadStatus>>((ref) {
  final manager = ref.watch(downloadManagerProvider);
  final controller = StreamController<Map<String, DownloadStatus>>();
  controller.add(manager.statuses);
  final sub = manager.updates.listen((_) => controller.add(manager.statuses));
  ref.onDispose(() {
    sub.cancel();
    controller.close();
  });
  return controller.stream;
});

/// The download status for a single book (defaults to `notDownloaded`).
final bookDownloadStatusProvider =
    Provider.family<DownloadStatus, String>((ref, bookId) {
  final map = ref.watch(downloadStatusesProvider).valueOrNull ?? const {};
  return map[bookId] ?? DownloadStatus.initial(bookId);
});
