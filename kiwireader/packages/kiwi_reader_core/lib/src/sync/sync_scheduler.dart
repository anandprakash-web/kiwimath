import 'dart:async';

import 'connectivity.dart';
import 'sync_engine.dart';
import 'sync_models.dart';

/// Surfaceable sync state (maps to the design's sync FSM).
enum SyncStatus { idle, syncing, offline, error, backoff }

/// Drives [SyncEngine] automatically: syncs when connectivity returns, on a
/// periodic timer, and (debounced) right after local writes — with an
/// in-flight guard and exponential backoff on failure. Pure Dart (only
/// dart:async), so it is unit-testable with injected connectivity + delay.
class SyncScheduler {
  final SyncEngine engine;
  final ConnectivitySource connectivity;
  final Duration interval;
  final Duration debounce;
  final Duration initialBackoff;
  final Duration maxBackoff;
  final Future<void> Function(Duration) _delay;

  final StreamController<SyncStatus> _statusCtl =
      StreamController<SyncStatus>.broadcast();
  StreamSubscription<bool>? _connSub;
  Timer? _periodic;
  bool _inFlight = false;
  bool _disposed = false;
  int _requestToken = 0;
  late Duration _backoff;

  SyncScheduler({
    required this.engine,
    this.connectivity = const AlwaysOnline(),
    this.interval = const Duration(seconds: 30),
    this.debounce = const Duration(seconds: 1),
    this.initialBackoff = const Duration(seconds: 1),
    this.maxBackoff = const Duration(seconds: 60),
    Future<void> Function(Duration)? delay,
  }) : _delay = delay ?? Future<void>.delayed {
    _backoff = initialBackoff;
  }

  Stream<SyncStatus> get status => _statusCtl.stream;

  /// Begin listening to connectivity and (if [interval] > 0) periodic ticks.
  void start() {
    _connSub = connectivity.onlineChanges.listen((online) {
      if (online) {
        sync();
      } else {
        _emit(SyncStatus.offline);
      }
    });
    if (interval > Duration.zero) {
      _periodic = Timer.periodic(interval, (_) => sync());
    }
  }

  /// Debounced trigger — call after a local create/edit/delete.
  void requestSync() {
    final token = ++_requestToken;
    _delay(debounce).then((_) {
      if (!_disposed && token == _requestToken) sync();
    });
  }

  /// Sync now. Skips when offline or already in flight. On failure, emits
  /// [SyncStatus.error] then retries with exponential backoff (capped).
  Future<SyncOutcome?> sync() async {
    if (_disposed) return null;
    if (!connectivity.isOnline) {
      _emit(SyncStatus.offline);
      return null;
    }
    if (_inFlight) return null;
    _inFlight = true;
    _emit(SyncStatus.syncing);
    try {
      final outcome = await engine.sync();
      _backoff = initialBackoff; // reset on success
      _emit(SyncStatus.idle);
      return outcome;
    } catch (_) {
      _emit(SyncStatus.error);
      _inFlight = false;
      await _backoffAndRetry();
      return null;
    } finally {
      _inFlight = false;
    }
  }

  Future<void> _backoffAndRetry() async {
    if (_disposed || !connectivity.isOnline) return;
    final wait = _backoff;
    final next =
        (_backoff.inMilliseconds * 2).clamp(0, maxBackoff.inMilliseconds);
    _backoff = Duration(milliseconds: next);
    _emit(SyncStatus.backoff);
    await _delay(wait);
    if (_disposed) return;
    await sync();
  }

  void _emit(SyncStatus s) {
    if (!_disposed) _statusCtl.add(s);
  }

  Future<void> dispose() async {
    _disposed = true;
    await _connSub?.cancel();
    _periodic?.cancel();
    await _statusCtl.close();
  }
}
