import '../store/local_store.dart';
import 'annotation_api.dart';
import 'sync_models.dart';

/// Orchestrates one offline-first sync cycle as a single round-trip
/// (mirrors `POST /v1/sync`): push the outbox + since-cursor, then merge the
/// server's deltas locally BEFORE clearing the outbox (pull-before-clobber).
class SyncEngine {
  final LocalStore store;
  final AnnotationApi api;
  final String deviceId;

  SyncEngine({required this.store, required this.api, required this.deviceId});

  Future<SyncOutcome> sync() async {
    final since = await store.lastCursor();
    final outbox = await store.outbox();

    final response = await api.sync(
      SyncRequest(deviceId: deviceId, sinceCursor: since, changes: outbox),
    );

    // Merge what the server sent (remote edits + conflict resolutions)...
    await store.applyRemote(response.changes);
    // ...acknowledge only what the server actually accepted...
    await store.clearOutbox(response.applied);
    // ...and advance the cursor.
    await store.setCursor(response.cursor);

    final outboxIds = outbox.map((o) => o.id).toSet();
    return SyncOutcome(
      pushed: response.applied.length,
      pulled: response.changes.length,
      conflicts: response.changes.where((a) => outboxIds.contains(a.id)).length,
    );
  }
}
