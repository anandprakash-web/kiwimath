import 'dart:async';

/// Abstracts "are we online?" so the [SyncScheduler] is testable without a
/// device. On Flutter the host provides a `connectivity_plus`-backed adapter;
/// tests use [FakeConnectivity]; [AlwaysOnline] is a safe default.
abstract class ConnectivitySource {
  bool get isOnline;
  Stream<bool> get onlineChanges;
}

class AlwaysOnline implements ConnectivitySource {
  const AlwaysOnline();
  @override
  bool get isOnline => true;
  @override
  Stream<bool> get onlineChanges => const Stream.empty();
}

/// Controllable connectivity for tests / previews.
class FakeConnectivity implements ConnectivitySource {
  bool _online;
  final _ctl = StreamController<bool>.broadcast();

  FakeConnectivity({bool online = true}) : _online = online;

  @override
  bool get isOnline => _online;

  @override
  Stream<bool> get onlineChanges => _ctl.stream;

  void setOnline(bool value) {
    _online = value;
    _ctl.add(value);
  }

  Future<void> dispose() => _ctl.close();
}
