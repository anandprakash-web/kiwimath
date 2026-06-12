import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Hive-backed offline cache for question bundles, user progress,
/// and pending answer submissions.
///
/// Call [OfflineStore.init] once from main() before runApp.
class OfflineStore {
  static const _questionBundlesBox = 'questionBundles';
  static const _userProgressBox = 'userProgress';
  static const _pendingResponsesBox = 'pendingResponses';

  static OfflineStore? _instance;
  static OfflineStore get instance => _instance ??= OfflineStore._();
  OfflineStore._();

  late Box<Map> _questionBundles;
  late Box<Map> _userProgress;
  late Box<Map> _pendingResponses;

  bool _initialized = false;

  /// Initialize Hive and open all boxes. Call once at app startup.
  static Future<void> init() async {
    await Hive.initFlutter();
    final store = OfflineStore.instance;
    store._questionBundles = await Hive.openBox<Map>(_questionBundlesBox);
    store._userProgress = await Hive.openBox<Map>(_userProgressBox);
    store._pendingResponses = await Hive.openBox<Map>(_pendingResponsesBox);
    store._initialized = true;
    debugPrint('OfflineStore: initialized (${store._questionBundles.length} cached bundles)');
  }

  // ---------------------------------------------------------------------------
  // Question Bundles
  // ---------------------------------------------------------------------------

  /// Cache a list of questions under [key] (e.g. "topic_grade_3_arithmetic").
  ///
  /// Each entry is stored with a `cachedAt` ISO-8601 timestamp so callers
  /// can decide whether to refresh stale data.
  void cacheQuestions(String key, List<Map<String, dynamic>> questions) {
    _ensureInitialized();
    final entry = <String, dynamic>{
      'questions': questions,
      'cachedAt': DateTime.now().toIso8601String(),
    };
    _questionBundles.put(key, entry);
  }

  /// Retrieve cached questions for [key], or null if not cached.
  List<Map<String, dynamic>>? getCachedQuestions(String key) {
    _ensureInitialized();
    final raw = _questionBundles.get(key);
    if (raw == null) return null;
    final entry = Map<String, dynamic>.from(raw);
    final questions = entry['questions'];
    if (questions == null) return null;
    return (questions as List).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  /// Return the `cachedAt` timestamp for a question bundle, or null.
  DateTime? getQuestionsCachedAt(String key) {
    _ensureInitialized();
    final raw = _questionBundles.get(key);
    if (raw == null) return null;
    final entry = Map<String, dynamic>.from(raw);
    final ts = entry['cachedAt'] as String?;
    return ts != null ? DateTime.tryParse(ts) : null;
  }

  // ---------------------------------------------------------------------------
  // User Progress
  // ---------------------------------------------------------------------------

  /// Cache user engagement data (streak, coins, daily progress).
  void cacheProgress(String userId, Map<String, dynamic> data) {
    _ensureInitialized();
    final entry = <String, dynamic>{
      ...data,
      'cachedAt': DateTime.now().toIso8601String(),
    };
    _userProgress.put(userId, entry);
  }

  /// Retrieve cached progress data for a user, or null.
  Map<String, dynamic>? getCachedProgress(String userId) {
    _ensureInitialized();
    final raw = _userProgress.get(userId);
    if (raw == null) return null;
    return Map<String, dynamic>.from(raw);
  }

  // ---------------------------------------------------------------------------
  // Pending Responses (offline answer queue)
  // ---------------------------------------------------------------------------

  /// Queue an answer submission for later sync.
  ///
  /// Each response is stored with a unique key so we can enumerate them later.
  void queueResponse(Map<String, dynamic> response) {
    _ensureInitialized();
    final entry = <String, dynamic>{
      ...response,
      'queuedAt': DateTime.now().toIso8601String(),
    };
    // Use a timestamp-based key to maintain insertion order
    final key = 'resp_${DateTime.now().millisecondsSinceEpoch}';
    _pendingResponses.put(key, entry);
    debugPrint('OfflineStore: queued response ($key), pending=${_pendingResponses.length}');
  }

  /// Get all pending answer submissions waiting to be synced.
  List<Map<String, dynamic>> getPendingResponses() {
    _ensureInitialized();
    return _pendingResponses.values
        .map((raw) => Map<String, dynamic>.from(raw))
        .toList();
  }

  /// Clear all pending responses after a successful sync.
  void clearPendingResponses() {
    _ensureInitialized();
    _pendingResponses.clear();
    debugPrint('OfflineStore: cleared pending responses');
  }

  /// Number of responses waiting to sync.
  int get pendingResponseCount {
    _ensureInitialized();
    return _pendingResponses.length;
  }

  // ---------------------------------------------------------------------------
  // Housekeeping
  // ---------------------------------------------------------------------------

  /// Clear all cached data (call on sign-out).
  Future<void> clearAll() async {
    _ensureInitialized();
    await _questionBundles.clear();
    await _userProgress.clear();
    await _pendingResponses.clear();
    debugPrint('OfflineStore: all data cleared');
  }

  void _ensureInitialized() {
    assert(_initialized, 'OfflineStore.init() must be called before use');
  }
}
