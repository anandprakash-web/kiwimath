import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../host/providers.dart';
import '../rendering/content_renderer.dart';
import 'reader_controllers.dart';

/// === Host-supplied dependencies =========================================
/// The host overrides these in its `ProviderScope`. They throw by default so a
/// missing wiring fails loudly at startup rather than silently misbehaving.

final authProviderRef = Provider<AuthProvider>(
  (ref) => throw UnimplementedError(
    'Override authProviderRef in the host ProviderScope.',
  ),
);

final contentProviderRef = Provider<ContentProvider>(
  (ref) => throw UnimplementedError(
    'Override contentProviderRef in the host ProviderScope.',
  ),
);

final deviceIdProvider = Provider<String>(
  (ref) => throw UnimplementedError(
    'Override deviceIdProvider in the host ProviderScope.',
  ),
);

/// On device this is overridden with a Drift-backed store (ticket KR-025).
/// For local dev/tests you can override it with [InMemoryLocalStore].
final localStoreProvider = Provider<LocalStore>(
  (ref) => throw UnimplementedError(
    'Provide a LocalStore (KR-025: Drift) or InMemoryLocalStore.',
  ),
);

/// On device this is a Dio REST client (KR-035). For dev you can override with
/// [InMemoryAnnotationApi].
final annotationApiProvider = Provider<AnnotationApi>(
  (ref) => throw UnimplementedError(
    'Provide an AnnotationApi (KR-035: REST) or InMemoryAnnotationApi.',
  ),
);

/// The active content renderer for the open book (e.g. `HtmlRenderer.fromBook`).
final contentRendererProvider = Provider<ContentRenderer>(
  (ref) => throw UnimplementedError(
    'Override contentRendererProvider with a renderer (e.g. HtmlRenderer.fromBook).',
  ),
);

/// Connectivity source driving auto-sync. Defaults to always-online; the host
/// overrides this with `ConnectivityPlusSource()` on a real device.
final connectivityProvider = Provider<ConnectivitySource>(
  (ref) => const AlwaysOnline(),
);

/// === Derived providers ===================================================

final syncEngineProvider = Provider<SyncEngine>(
  (ref) => SyncEngine(
    store: ref.watch(localStoreProvider),
    api: ref.watch(annotationApiProvider),
    deviceId: ref.watch(deviceIdProvider),
  ),
);

final annotationControllerProvider =
    Provider.family<AnnotationController, String>(
      (ref, bookId) => AnnotationController(
        bookId: bookId,
        store: ref.watch(localStoreProvider),
        syncEngine: ref.watch(syncEngineProvider),
        deviceId: ref.watch(deviceIdProvider),
      ),
    );

/// Reactive list of annotations for a book (live list UI binds to this).
final annotationsProvider = FutureProvider.family<List<Annotation>, String>(
  (ref, bookId) => ref.watch(localStoreProvider).all(bookId),
);
