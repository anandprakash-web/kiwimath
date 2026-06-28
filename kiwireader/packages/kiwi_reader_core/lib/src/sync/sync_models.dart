import '../models/annotation.dart';

/// Body of `POST /v1/sync`. The client pushes its [sinceCursor] and outbox.
///
/// NOTE: the cursor is an OPAQUE, monotonically-increasing token issued by the
/// server — deliberately NOT a wall-clock timestamp. Client and server clocks
/// drift, so filtering deltas by client `updatedAt` is unsafe; a server-side
/// sequence is the correct, skew-proof watermark.
class SyncRequest {
  final String deviceId;
  final int? sinceCursor;
  final List<Annotation>
      changes; // upserts + tombstones (deletes carry deletedAt)

  const SyncRequest(
      {required this.deviceId,
      required this.sinceCursor,
      required this.changes});

  Map<String, dynamic> toJson() => {
        'deviceId': deviceId,
        'sinceCursor': sinceCursor,
        'changes': changes.map((a) => a.toJson()).toList(),
      };

  factory SyncRequest.fromJson(Map<String, dynamic> j) => SyncRequest(
        deviceId: j['deviceId'] as String,
        sinceCursor: (j['sinceCursor'] as num?)?.toInt(),
        changes: (j['changes'] as List)
            .map(
                (e) => Annotation.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

/// Response of `POST /v1/sync`. [cursor] is the client's next [sinceCursor].
class SyncResponse {
  final int cursor;
  final List<String> applied; // ids the server accepted from the client
  final List<Annotation> changes; // remote deltas + conflict resolutions

  const SyncResponse(
      {required this.cursor, required this.applied, required this.changes});

  Map<String, dynamic> toJson() => {
        'cursor': cursor,
        'applied': applied,
        'changes': changes.map((a) => a.toJson()).toList(),
      };

  factory SyncResponse.fromJson(Map<String, dynamic> j) => SyncResponse(
        cursor: (j['cursor'] as num).toInt(),
        applied: (j['applied'] as List).map((e) => e as String).toList(),
        changes: (j['changes'] as List)
            .map(
                (e) => Annotation.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

/// Summary returned to the caller after one sync cycle.
class SyncOutcome {
  final int pushed;
  final int pulled;
  final int conflicts;

  const SyncOutcome(
      {required this.pushed, required this.pulled, this.conflicts = 0});

  @override
  String toString() =>
      'SyncOutcome(pushed=$pushed, pulled=$pulled, conflicts=$conflicts)';
}
