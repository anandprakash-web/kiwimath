/// CompanionService — session-level companion state management.
///
/// Responsibilities:
/// - Fetch companion config at session start
/// - Track pico appearances per lesson
/// - Manage deep-think retreat timer
/// - Provide resolved companion state to widgets
/// - Send telemetry events
library;

import 'dart:async';
import 'package:flutter/foundation.dart';
import 'dart:ui' show Color;
import '../models/companion.dart';
import 'api_client.dart';

class CompanionService extends ChangeNotifier {
  final ApiClient _api = ApiClient();

  CompanionConfig? _config;
  CompanionConfig? get config => _config;
  bool get isLoaded => _config != null;

  // Per-lesson tracking
  int _picoAppearancesInLesson = 0;
  int get picoAppearancesInLesson => _picoAppearancesInLesson;

  // Deep-think retreat state
  Timer? _deepThinkTimer;
  bool _isConcentrating = false;
  bool get isConcentrating => _isConcentrating;
  DateTime? _lastKidAction;

  // Current surface companion
  SummonResponse? _currentSummon;
  SummonResponse? get currentSummon => _currentSummon;

  /// Initialize companion config from backend (call once per session).
  Future<void> initialize({
    String chosenPrimary = 'kiwi',
    String ageTier = 'k2',
    int appVersion = 1,
  }) async {
    try {
      final json = await _api.getCompanionConfig(
        chosenPrimary: chosenPrimary,
        ageTier: ageTier,
        appVersion: appVersion,
      );
      _config = CompanionConfig.fromJson(json);
      notifyListeners();
    } catch (e) {
      // Fallback: build minimal config with Kiwi only
      debugPrint('CompanionService: config fetch failed, using fallback: $e');
      _config = _buildFallbackConfig();
      notifyListeners();
    }
  }

  /// Resolve companion for a surface (client-side, <1ms).
  SummonResponse summon(
    CompanionSurface surface, {
    int problemStepsRequired = 1,
  }) {
    if (_config == null) {
      return const SummonResponse(
        primaryId: CompanionId.kiwi,
        primaryEmotion: Emotion.neutral,
      );
    }

    final response = resolveCompanion(
      surface: surface,
      config: _config!,
      problemStepsRequired: problemStepsRequired,
      picoAppearancesInLesson: _picoAppearancesInLesson,
    );

    // Track Pico appearances
    if (response.primaryId == CompanionId.pico) {
      _picoAppearancesInLesson++;
    }

    _currentSummon = response;
    notifyListeners();

    // Fire telemetry asynchronously
    _sendTelemetry('companion_summoned', response.primaryId.name, surface);

    return response;
  }

  /// Reset per-lesson counters (call when starting a new lesson).
  void startNewLesson() {
    _picoAppearancesInLesson = 0;
    _isConcentrating = false;
    _deepThinkTimer?.cancel();
  }

  /// Record that the kid did something (answer, tap, drag).
  void recordKidAction() {
    _lastKidAction = DateTime.now();
    if (_isConcentrating) {
      _isConcentrating = false;
      notifyListeners();
    }
    _resetDeepThinkTimer();
  }

  /// Start monitoring for deep-think retreat.
  void startDeepThinkMonitor() {
    _resetDeepThinkTimer();
  }

  void _resetDeepThinkTimer() {
    _deepThinkTimer?.cancel();
    final retreatMs = _config?.constraints['deep_think_retreat_no_submit_ms'] ?? 10000;
    _deepThinkTimer = Timer(Duration(milliseconds: retreatMs as int), () {
      _isConcentrating = true;
      notifyListeners();
      _sendTelemetry(
        'companion_dismissed',
        _currentSummon?.primaryId.name ?? 'kiwi',
        null,
      );
    });
  }

  /// Send companion telemetry event.
  Future<void> _sendTelemetry(
    String event,
    String companionId,
    CompanionSurface? surface,
  ) async {
    try {
      await _api.sendCompanionTelemetry(
        event: event,
        companionId: companionId,
        surface: surface != null ? surfaceToString(surface) : 'unknown',
      );
    } catch (_) {
      // Telemetry is fire-and-forget
    }
  }

  /// Choose a different primary companion.
  Future<bool> choosePrimary(CompanionId id) async {
    try {
      final result = await _api.summonCompanion(
        surface: 'onboarding_wizard_step2_picker',
        chosenPrimary: id.name,
      );
      if (result['status'] == 'unavailable') return false;

      // Re-fetch config with new primary
      await initialize(chosenPrimary: id.name);
      return true;
    } catch (_) {
      return false;
    }
  }

  CompanionConfig _buildFallbackConfig() {
    return CompanionConfig(
      cast: [
        CompanionData(
          id: CompanionId.kiwi,
          name: 'Kiwi',
          region: 'pacific_oceania',
          role: 'curious_explorer',
          signatureColor: const Color(0xFF16A34A),
          signatureColorSoft: const Color(0xFFD1FAE5),
          signatureColorText: const Color(0xFF065F46),
          isDefault: true,
          shipped: true,
        ),
        for (final entry in [
          (CompanionId.mau, 'Mau', 'east_africa', 'careful_checker', 0xFFD97706, 0xFFFEF3C7, 0xFF92400E),
          (CompanionId.lumi, 'Lumi', 'himalayas_asia', 'quiet_thinker', 0xFF7C3AED, 0xFFEDE9FE, 0xFF5B21B6),
          (CompanionId.pico, 'Pico', 'andes_americas', 'spark', 0xFF0891B2, 0xFFCFFAFE, 0xFF155E75),
          (CompanionId.hedge, 'Hedge', 'europe', 'organiser', 0xFFEA580C, 0xFFFFF7ED, 0xFF9A3412),
        ])
          CompanionData(
            id: entry.$1,
            name: entry.$2,
            region: entry.$3,
            role: entry.$4,
            signatureColor: Color(entry.$5),
            signatureColorSoft: Color(entry.$6),
            signatureColorText: Color(entry.$7),
            shipped: false,
          ),
      ],
      chosenPrimary: CompanionId.kiwi,
      ageTier: AgeTier.k2,
      audioEnabled: true,
      prefetchManifest: const [],
      performanceBudgets: const {},
      idleBehaviors: const {},
      constraints: const {
        'pico_max_per_lesson': 1,
        'lumi_auto_fade_ms': 5000,
        'deep_think_retreat_no_submit_ms': 10000,
      },
    );
  }

  @override
  void dispose() {
    _deepThinkTimer?.cancel();
    super.dispose();
  }
}
