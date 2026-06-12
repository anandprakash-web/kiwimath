import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';

import 'offline_store.dart';
import 'api_client.dart';

/// Lightweight connectivity monitor.
///
/// Periodically checks reachability via DNS lookup and exposes a stream
/// of online/offline state changes. When connectivity is restored, it
/// automatically triggers a sync of any pending offline responses.
class ConnectivityService {
  static ConnectivityService? _instance;
  static ConnectivityService get instance =>
      _instance ??= ConnectivityService._();
  ConnectivityService._();

  final _controller = StreamController<bool>.broadcast();
  Timer? _pollTimer;
  bool _isOnline = true;
  bool _started = false;

  /// Current connectivity state.
  bool get isOnline => _isOnline;

  /// Stream that emits `true` when going online and `false` when going offline.
  Stream<bool> get onConnectivityChanged => _controller.stream;

  /// Start periodic connectivity checks. Safe to call multiple times.
  void start({Duration interval = const Duration(seconds: 15)}) {
    if (_started) return;
    _started = true;
    // Do an immediate check
    _check();
    _pollTimer = Timer.periodic(interval, (_) => _check());
  }

  /// Stop polling.
  void stop() {
    _pollTimer?.cancel();
    _pollTimer = null;
    _started = false;
  }

  Future<void> _check() async {
    final wasOnline = _isOnline;
    try {
      // Quick DNS lookup — works on both Android and iOS without extra permissions.
      final result = await InternetAddress.lookup('example.com')
          .timeout(const Duration(seconds: 5));
      _isOnline = result.isNotEmpty && result[0].rawAddress.isNotEmpty;
    } on SocketException catch (_) {
      _isOnline = false;
    } on TimeoutException catch (_) {
      _isOnline = false;
    } catch (_) {
      _isOnline = false;
    }

    if (wasOnline != _isOnline) {
      debugPrint('ConnectivityService: ${_isOnline ? "ONLINE" : "OFFLINE"}');
      _controller.add(_isOnline);

      // When we come back online, try syncing pending responses.
      if (_isOnline) {
        _syncPendingResponses();
      }
    }
  }

  /// Attempt to sync any queued offline answer submissions.
  Future<void> _syncPendingResponses() async {
    final store = OfflineStore.instance;
    final pending = store.getPendingResponses();
    if (pending.isEmpty) return;

    debugPrint('ConnectivityService: syncing ${pending.length} pending responses');
    final api = ApiClient();

    try {
      for (final response in pending) {
        // Each pending response contains the data needed for checkAnswerV2
        // or syncOfflineResults — route based on the 'syncType' field.
        final syncType = response['syncType'] as String? ?? 'answer';

        if (syncType == 'offlineBundle') {
          await api.syncOfflineResults(
            userId: response['userId'] as String,
            grade: response['grade'] as int,
            topicId: response['topicId'] as String,
            results: List<Map<String, dynamic>>.from(response['results'] as List),
            thetaAtDownload: (response['thetaAtDownload'] as num).toDouble(),
            downloadedAt: response['downloadedAt'] as String,
          );
        } else {
          await api.checkAnswerV2(
            questionId: response['questionId'] as String,
            selectedAnswer: response['selectedAnswer'] as int,
            integerAnswer: response['integerAnswer'] as int?,
            dragOrder: response['dragOrder'] != null
                ? List<int>.from(response['dragOrder'] as List)
                : null,
            userId: response['userId'] as String?,
            timeTakenMs: response['timeTakenMs'] as int? ?? 0,
            hintsUsed: response['hintsUsed'] as int? ?? 0,
          );
        }
      }

      // All synced successfully — clear the queue.
      store.clearPendingResponses();
      debugPrint('ConnectivityService: sync complete');
    } catch (e) {
      debugPrint('ConnectivityService: sync failed, will retry later: $e');
      // Leave pending responses in queue for next attempt.
    }
  }

  /// Force a connectivity check and sync now (e.g. after user pulls to refresh).
  Future<void> checkNow() async {
    await _check();
  }

  void dispose() {
    stop();
    _controller.close();
  }
}
