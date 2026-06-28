import 'dart:async';

import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

class _FlakyApi implements AnnotationApi {
  int failuresLeft;
  int calls = 0;
  _FlakyApi(this.failuresLeft);

  @override
  Future<SyncResponse> sync(SyncRequest request) async {
    calls++;
    if (failuresLeft-- > 0) throw StateError('boom');
    return const SyncResponse(cursor: 1, applied: [], changes: []);
  }
}

class _GatedApi implements AnnotationApi {
  final Completer<void> gate;
  int calls = 0;
  _GatedApi(this.gate);

  @override
  Future<SyncResponse> sync(SyncRequest request) async {
    calls++;
    await gate.future;
    return const SyncResponse(cursor: 0, applied: [], changes: []);
  }
}

SyncScheduler _scheduler(AnnotationApi api, ConnectivitySource conn) =>
    SyncScheduler(
      engine:
          SyncEngine(store: InMemoryLocalStore(), api: api, deviceId: 'dev'),
      connectivity: conn,
      interval: Duration.zero, // no real periodic timer in tests
      debounce: Duration.zero,
      initialBackoff: const Duration(milliseconds: 1),
      delay: (_) async {}, // instant backoff/debounce
    );

void main() {
  test('skips sync when offline', () async {
    final api = _FlakyApi(0);
    final s = _scheduler(api, FakeConnectivity(online: false));
    expect(await s.sync(), isNull);
    expect(api.calls, 0);
    await s.dispose();
  });

  test('success path returns an outcome and ends idle', () async {
    final api = _FlakyApi(0);
    final s = _scheduler(api, FakeConnectivity());
    final statuses = <SyncStatus>[];
    s.status.listen(statuses.add);
    expect(await s.sync(), isNotNull);
    expect(api.calls, 1);
    await Future<void>.delayed(Duration.zero);
    expect(statuses, containsAllInOrder([SyncStatus.syncing, SyncStatus.idle]));
    await s.dispose();
  });

  test('retries with exponential backoff until success', () async {
    final api = _FlakyApi(2); // fail twice, then succeed
    final s = _scheduler(api, FakeConnectivity());
    final statuses = <SyncStatus>[];
    s.status.listen(statuses.add);
    await s.sync();
    expect(api.calls, 3);
    await Future<void>.delayed(Duration.zero);
    expect(statuses, contains(SyncStatus.error));
    expect(statuses, contains(SyncStatus.backoff));
    expect(statuses.last, SyncStatus.idle);
    await s.dispose();
  });

  test('coming online triggers a sync', () async {
    final api = _FlakyApi(0);
    final conn = FakeConnectivity(online: false);
    final s = _scheduler(api, conn)..start();
    conn.setOnline(true);
    await Future<void>.delayed(Duration.zero);
    expect(api.calls, 1);
    await s.dispose();
    await conn.dispose();
  });

  test('in-flight guard prevents overlapping syncs', () async {
    final gate = Completer<void>();
    final api = _GatedApi(gate);
    final s = _scheduler(api, FakeConnectivity());
    final first = s.sync(); // starts, suspends inside engine.sync
    final second = await s.sync(); // guarded -> null
    expect(second, isNull);
    gate.complete();
    await first;
    expect(api.calls, 1);
    await s.dispose();
  });
}
