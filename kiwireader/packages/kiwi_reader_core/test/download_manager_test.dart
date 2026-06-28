import 'dart:async';

import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

CatalogBook book(String id, {int? size, String version = 'v1'}) => CatalogBook(
      id: id,
      title: id.toUpperCase(),
      format: BookFormat.pdf,
      contentVersion: version,
      byteSize: size,
    );

/// A controllable [DownloadSource]: every call opens a fresh single-subscription
/// stream (so retries get a clean stream), recorded per book id.
class FakeSource {
  final List<String> opens = [];
  final Map<String, List<StreamController<List<int>>>> _byId = {};

  Future<Stream<List<int>>> call(CatalogBook b) async {
    opens.add(b.id);
    final c = StreamController<List<int>>();
    (_byId[b.id] ??= []).add(c);
    return c.stream;
  }

  int count(String id) => _byId[id]?.length ?? 0;

  /// The n-th controller opened for [id], waiting until it exists.
  Future<StreamController<List<int>>> nth(String id, int n) async {
    for (var i = 0; i < 200 && count(id) <= n; i++) {
      await Future<void>.delayed(Duration.zero);
    }
    return _byId[id]![n];
  }
}

void main() {
  test('downloads to completion with progress and commits bytes', () async {
    final store = InMemoryOfflineBookStore();
    final src = FakeSource();
    final m = DownloadManager(store: store, source: src.call);
    await m.init();

    final seenProgress = <double?>[];
    final sub = m.updates
        .where((s) => s.bookId == 'a' && s.state == DownloadState.downloading)
        .listen((s) => seenProgress.add(s.progress));
    final done = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.downloaded);

    await m.download(book('a', size: 10));
    final c = await src.nth('a', 0);
    c.add([1, 2, 3, 4, 5]); // 5/10
    await Future<void>.delayed(Duration.zero);
    c.add([6, 7, 8, 9, 10]); // 10/10
    await c.close();

    final s = await done;
    expect(s.state, DownloadState.downloaded);
    expect(s.isAvailableOffline, isTrue);
    expect(s.progress, 1.0);
    expect(seenProgress, contains(0.5));
    expect(await store.hasBytes('a'), isTrue);
    expect(await store.bytesOf('a'), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    await sub.cancel();
    await m.dispose();
  });

  test('unknown book defaults to notDownloaded', () async {
    final m = DownloadManager(
        store: InMemoryOfflineBookStore(), source: FakeSource().call);
    await m.init();
    expect(m.statusOf('zzz').state, DownloadState.notDownloaded);
    expect(m.statusOf('zzz').isAvailableOffline, isFalse);
    expect(m.statusOf('zzz').progress, isNull);
    await m.dispose();
  });

  test('progress is indeterminate (null) when size is unknown', () async {
    final src = FakeSource();
    final m = DownloadManager(store: InMemoryOfflineBookStore(), source: src.call);
    await m.init();

    final tick = m.updates.firstWhere(
        (s) => s.bookId == 'a' && s.state == DownloadState.downloading && s.receivedBytes > 0);
    await m.download(book('a')); // no byteSize
    final c = await src.nth('a', 0);
    c.add([1, 2, 3]);
    final s = await tick;
    expect(s.progress, isNull); // indeterminate
    await c.close();
    await m.dispose();
  });

  test('honours the concurrency limit and queues the rest', () async {
    final src = FakeSource();
    final m = DownloadManager(
        store: InMemoryOfflineBookStore(), source: src.call, maxConcurrent: 1);
    await m.init();

    await m.download(book('a', size: 4));
    await m.download(book('b', size: 4));

    expect(m.statusOf('a').state, DownloadState.downloading);
    expect(m.statusOf('b').state, DownloadState.queued);
    expect(src.opens, ['a']); // b not opened while a is in flight

    final bStarted = m.updates
        .firstWhere((s) => s.bookId == 'b' && s.state == DownloadState.downloading);
    final ca = await src.nth('a', 0);
    ca.add([1, 2, 3, 4]);
    await ca.close();
    await bStarted;

    expect(m.statusOf('a').state, DownloadState.downloaded);
    expect(src.opens, ['a', 'b']);
    await m.dispose();
  });

  test('pause discards progress; download() resumes to completion', () async {
    final src = FakeSource();
    final store = InMemoryOfflineBookStore();
    final m = DownloadManager(store: store, source: src.call);
    await m.init();

    await m.download(book('a', size: 10));
    final c = await src.nth('a', 0);
    c.add([1, 2, 3]);
    await Future<void>.delayed(Duration.zero);
    await m.pause('a');
    expect(m.statusOf('a').state, DownloadState.paused);
    expect(await store.hasBytes('a'), isFalse);

    final done = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.downloaded);
    await m.download(book('a', size: 10)); // resume
    final c2 = await src.nth('a', 1); // fresh stream
    c2.add(List<int>.generate(10, (i) => i));
    await c2.close();
    await done;
    expect(m.statusOf('a').isAvailableOffline, isTrue);
    await m.dispose();
  });

  test('stream error -> failed (with message); retry recovers', () async {
    final src = FakeSource();
    final m = DownloadManager(store: InMemoryOfflineBookStore(), source: src.call);
    await m.init();

    await m.download(book('a', size: 5));
    final c = await src.nth('a', 0);
    final failed = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.failed);
    c.addError('boom');
    final f = await failed;
    expect(f.error, contains('boom'));

    final done = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.downloaded);
    await m.download(book('a', size: 5)); // retry
    final c2 = await src.nth('a', 1);
    c2.add([1, 2, 3, 4, 5]);
    await c2.close();
    await done;
    expect(m.statusOf('a').isAvailableOffline, isTrue);
    await m.dispose();
  });

  test('remove deletes bytes and resets status; re-download no-ops at same version',
      () async {
    final src = FakeSource();
    final store = InMemoryOfflineBookStore();
    final m = DownloadManager(store: store, source: src.call);
    await m.init();

    final done = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.downloaded);
    await m.download(book('a', size: 3));
    (await src.nth('a', 0))
      ..add([1, 2, 3])
      ..close();
    await done;
    expect(await store.hasBytes('a'), isTrue);

    // Already downloaded at v1 -> no new stream opened.
    final opens = src.count('a');
    await m.download(book('a', size: 3)); // same version
    expect(src.count('a'), opens);

    await m.remove('a');
    expect(await store.hasBytes('a'), isFalse);
    expect(m.statusOf('a').state, DownloadState.notDownloaded);
    await m.dispose();
  });

  test('a changed contentVersion forces a re-download', () async {
    final src = FakeSource();
    final m = DownloadManager(store: InMemoryOfflineBookStore(), source: src.call);
    await m.init();

    final done1 = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.downloaded);
    await m.download(book('a', size: 3, version: 'v1'));
    (await src.nth('a', 0))
      ..add([1, 2, 3])
      ..close();
    await done1;

    final restart = m.updates
        .firstWhere((s) => s.bookId == 'a' && s.state == DownloadState.downloading);
    await m.download(book('a', size: 3, version: 'v2')); // new edition
    await restart;
    expect(src.count('a'), greaterThanOrEqualTo(2));
    await m.dispose();
  });

  test('init() restores downloaded; normalizes interrupted in-flight', () async {
    final store = InMemoryOfflineBookStore();
    await store.saveStatus(const DownloadStatus(
      bookId: 'done',
      state: DownloadState.downloaded,
      receivedBytes: 4,
      totalBytes: 4,
      version: 'v1',
    ));
    await store.saveStatus(const DownloadStatus(
      bookId: 'mid',
      state: DownloadState.downloading,
      receivedBytes: 2,
      totalBytes: 4,
    ));

    final m = DownloadManager(store: store, source: FakeSource().call);
    await m.init();
    expect(m.statusOf('done').state, DownloadState.downloaded);
    expect(m.statusOf('done').isAvailableOffline, isTrue);
    expect(m.statusOf('mid').state, DownloadState.notDownloaded); // not committed
    await m.dispose();
  });

  test('cancel during download discards it; a late completion is ignored',
      () async {
    final store = InMemoryOfflineBookStore();
    final src = FakeSource();
    final m = DownloadManager(store: store, source: src.call);
    await m.init();

    await m.download(book('a', size: 10));
    final c = await src.nth('a', 0);
    c.add([1, 2, 3]);
    await Future<void>.delayed(Duration.zero);
    await m.cancel('a');
    expect(m.statusOf('a').state, DownloadState.notDownloaded);

    // A completion arriving after the cancel must not resurrect the download.
    c.add([4, 5, 6, 7, 8, 9, 10]);
    await c.close();
    await Future<void>.delayed(Duration.zero);
    expect(m.statusOf('a').state, DownloadState.notDownloaded);
    expect(await store.hasBytes('a'), isFalse);
    await m.dispose();
  });

  test('DownloadStatus JSON round-trips', () {
    const s = DownloadStatus(
      bookId: 'a',
      state: DownloadState.downloaded,
      receivedBytes: 12,
      totalBytes: 12,
      version: 'v3',
    );
    expect(DownloadStatus.fromJson(s.toJson()), s);
    final b = book('a', size: 10, version: 'v3');
    expect(CatalogBook.fromJson(b.toJson()), b);
  });
}
