import '../models/annotation.dart';
import 'annotation_api.dart';
import 'merge.dart';
import 'sync_models.dart';

/// In-memory reference implementation of the Annotation & Sync API, mirroring
/// `POST /v1/sync` in `openapi/openapi.yaml`.
///
/// Doubles as (a) the unit-test backend and (b) a local fake for app
/// development before the real server exists. It assigns each accepted change a
/// monotonic server sequence ([_seq]) and returns deltas by sequence — the
/// skew-proof cursor model the real server must also use.
class InMemoryAnnotationApi implements AnnotationApi {
  final Map<String, Annotation> _server = {};
  final Map<String, int> _seqOf = {};
  int _seq = 0;

  /// Seed an authoritative server record to simulate a change made elsewhere.
  void seed(Annotation a) {
    _server[a.id] = a;
    _seqOf[a.id] = ++_seq;
  }

  List<Annotation> get records => _server.values.toList(growable: false);

  @override
  Future<SyncResponse> sync(SyncRequest request) async {
    final applied = <String>[];
    final echoBack =
        <Annotation>[]; // conflict resolutions the client must learn

    for (final incoming in request.changes) {
      final existing = _server[incoming.id];
      if (existing == null) {
        _server[incoming.id] = incoming;
        _seqOf[incoming.id] = ++_seq;
      } else {
        final winner = Merge.resolve(incoming, existing);
        if (winner != existing) {
          _server[incoming.id] = winner;
          _seqOf[incoming.id] = ++_seq; // server state advanced
        }
        if (winner != incoming) echoBack.add(winner);
      }
      applied.add(incoming.id);
    }

    final since = request.sinceCursor;
    final incomingIds = request.changes.map((c) => c.id).toSet();
    final deltas = _server.values.where((a) {
      if (incomingIds.contains(a.id)) return false; // covered by echoBack
      final seq = _seqOf[a.id] ?? 0;
      return since == null || seq > since;
    }).toList();

    return SyncResponse(
      cursor: _seq,
      applied: applied,
      changes: [...deltas, ...echoBack],
    );
  }
}
