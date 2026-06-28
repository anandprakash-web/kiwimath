import 'package:kiwi_reader_core/io.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

import 'helpers.dart';

void main() {
  late SyncServer server;
  late Uri base;

  setUp(() async {
    server = SyncServer();
    final port = await server.start(port: 0);
    base = Uri.parse('http://127.0.0.1:$port');
  });
  tearDown(() async => server.stop());

  test('two clients converge over real HTTP', () async {
    final apiA = HttpAnnotationApi(base);
    final apiB = HttpAnnotationApi(base);
    final storeA = InMemoryLocalStore();
    final storeB = InMemoryLocalStore();
    final engineA = SyncEngine(store: storeA, api: apiA, deviceId: 'devA');
    final engineB = SyncEngine(store: storeB, api: apiB, deviceId: 'devB');

    await storeA
        .put(ann(id: 'a1', color: 'A-green', updated: t(5), device: 'devA'));
    final o1 = await engineA.sync();
    expect(o1.pushed, 1);

    await engineB.sync(); // pulls a1 over the wire
    expect((await storeB.get('a1'))?.color, 'A-green');

    await storeB
        .put(ann(id: 'a1', color: 'B-yellow', updated: t(40), device: 'devB'));
    await engineB.sync();
    await engineA.sync();
    expect((await storeA.get('a1'))?.color, 'B-yellow');
    expect((await storeB.get('a1'))?.color, 'B-yellow');

    apiA.close();
    apiB.close();
  });

  test('a delete propagates as a tombstone over HTTP', () async {
    final api = HttpAnnotationApi(base);
    final store = InMemoryLocalStore();
    final engine = SyncEngine(store: store, api: api, deviceId: 'devA');

    await store.put(ann(id: 'd1', updated: t(1)));
    await engine.sync();
    await store.put(ann(id: 'd1', updated: t(5), deleted: t(5)));
    await engine.sync();

    final store2 = InMemoryLocalStore();
    final engine2 = SyncEngine(
        store: store2, api: HttpAnnotationApi(base), deviceId: 'devC');
    await engine2.sync();
    expect((await store2.get('d1'))?.isDeleted, isTrue);

    api.close();
  });

  test('sends the bearer token from tokenProvider over HTTP', () async {
    final api =
        HttpAnnotationApi(base, tokenProvider: () async => 'test-token');
    final store = InMemoryLocalStore();
    final engine = SyncEngine(store: store, api: api, deviceId: 'devA');
    await store.put(ann(id: 'a1', updated: t(1)));
    await engine.sync();
    expect(server.lastAuthHeader, 'Bearer test-token');
    api.close();
  });
}
