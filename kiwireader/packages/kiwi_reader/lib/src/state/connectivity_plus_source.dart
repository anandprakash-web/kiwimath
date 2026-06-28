import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// On-device [ConnectivitySource] backed by `connectivity_plus`.
///
/// Override `connectivityProvider` with this in the host's `ProviderScope`:
/// ```dart
/// connectivityProvider.overrideWith((ref) => ConnectivityPlusSource()),
/// ```
class ConnectivityPlusSource implements ConnectivitySource {
  final Connectivity _connectivity;
  bool _online = true;
  final StreamController<bool> _ctl = StreamController<bool>.broadcast();
  StreamSubscription<List<ConnectivityResult>>? _sub;

  ConnectivityPlusSource([Connectivity? connectivity])
    : _connectivity = connectivity ?? Connectivity() {
    _sub = _connectivity.onConnectivityChanged.listen((results) {
      final online = _isOnline(results);
      if (online != _online) {
        _online = online;
        _ctl.add(online);
      }
    });
    _connectivity.checkConnectivity().then(
      (results) => _online = _isOnline(results),
    );
  }

  static bool _isOnline(List<ConnectivityResult> results) =>
      results.any((r) => r != ConnectivityResult.none);

  @override
  bool get isOnline => _online;

  @override
  Stream<bool> get onlineChanges => _ctl.stream;

  Future<void> dispose() async {
    await _sub?.cancel();
    await _ctl.close();
  }
}
