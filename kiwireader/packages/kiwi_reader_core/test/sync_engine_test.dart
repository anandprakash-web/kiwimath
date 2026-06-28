import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

import 'helpers.dart';

void main() {
  late InMemoryLocalStore store;
  late InMemoryAnnotationApi api;
  late SyncEngine engine;

  setUp(() {
    store = InMemoryLocalStore();
    api = InMemoryAnnotationApi();
    engine = SyncEngine(store: store, api: api, deviceId: 'devA');
  });

  test('offline create -> sync pushes to server and clears outbox', () async {
    await store.put(ann(id: 'a1', updated: t(1)));
    final outcome = await engine.sync();
    expect(outcome.pushed, 1);
    expect(api.records.map((e) => e.id), contains('a1'));
    expect(await store.outbox(), isEmpty);
  });

  test('remote delta is pulled and merged into local', () async {
    api.seed(ann(id: 'r1', color: 'pink', updated: t(2)));
    final outcome = await engine.sync();
    expect(outcome.pulled, greaterThanOrEqualTo(1));
    expect((await store.get('r1'))?.color, 'pink');
  });

  test('conflict: server newer edit wins; client learns the resolution',
      () async {
    api.seed(ann(id: 'a1', color: 'server', updated: t(50), revision: 3));
    await store
        .put(ann(id: 'a1', color: 'client', updated: t(10), revision: 2));
    await engine.sync();
    expect((await store.get('a1'))?.color, 'server');
  });

  test('local delete propagates to server as a tombstone', () async {
    api.seed(ann(id: 'a1', color: 'green', updated: t(1)));
    await store.put(ann(id: 'a1', updated: t(20), deleted: t(20)));
    await engine.sync();
    expect(api.records.firstWhere((e) => e.id == 'a1').isDeleted, isTrue);
  });

  test('sync is idempotent: a second cycle pushes nothing new', () async {
    await store.put(ann(id: 'a1', updated: t(1)));
    await engine.sync();
    final countAfterFirst = api.records.length;
    final outcome2 = await engine.sync();
    expect(api.records.length, countAfterFirst);
    expect(outcome2.pushed, 0);
  });

  test('two devices converge on the same record', () async {
    // Device A creates, syncs.
    await store
        .put(ann(id: 'a1', color: 'A-green', updated: t(5), device: 'devA'));
    await engine.sync();

    // Device B (separate store) edits the same id later, syncs to same server.
    final storeB = InMemoryLocalStore();
    final engineB = SyncEngine(store: storeB, api: api, deviceId: 'devB');
    await storeB
        .put(ann(id: 'a1', color: 'B-yellow', updated: t(40), device: 'devB'));
    await engineB.sync();

    // Device A syncs again and should converge to B's newer value.
    await engine.sync();
    expect((await store.get('a1'))?.color, 'B-yellow');
    expect((await storeB.get('a1'))?.color, 'B-yellow');
  });
}
