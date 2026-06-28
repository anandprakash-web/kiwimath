import 'dart:io';

import 'package:kiwi_reader_core/io.dart';
import 'package:test/test.dart';

import 'helpers.dart';

void main() {
  late Directory tmp;

  setUp(() async => tmp = await Directory.systemTemp.createTemp('kiwi_store_'));
  tearDown(() async {
    if (await tmp.exists()) await tmp.delete(recursive: true);
  });

  test('persists items + outbox + cursor across a reopen', () async {
    final path = '${tmp.path}/store.json';
    final s1 = await JsonFileStore.open(path);
    await s1.put(ann(id: 'a1', color: 'green', updated: t(1)));
    await s1.setCursor(7);
    expect((await s1.outbox()).map((e) => e.id), contains('a1'));

    // A brand-new instance loaded from disk sees everything.
    final s2 = await JsonFileStore.open(path);
    expect((await s2.get('a1'))?.color, 'green');
    expect(await s2.lastCursor(), 7);
    expect((await s2.outbox()).map((e) => e.id), contains('a1'));
  });

  test('cleared outbox and tombstones persist', () async {
    final path = '${tmp.path}/store.json';
    final s1 = await JsonFileStore.open(path);
    await s1.put(ann(id: 'a1', updated: t(1)));
    await s1.clearOutbox(['a1']);
    await s1.put(ann(id: 'a1', updated: t(2), deleted: t(2)));

    final s2 = await JsonFileStore.open(path);
    expect((await s2.get('a1'))?.isDeleted, isTrue);
    expect((await s2.all('bk')), isEmpty); // deleted hidden by default
    expect((await s2.all('bk', includeDeleted: true)).length, 1);
  });
}
