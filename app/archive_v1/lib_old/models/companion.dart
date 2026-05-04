/// Kiwimath Companion System — Dart models + client-side resolver.
///
/// Mirrors backend companion.py exactly. Client fetches config bundle
/// once per session, then resolves companions locally for <1ms latency.
library;

import 'dart:ui';

// ── Enums ────────────────────────────────────────────────────────────

enum CompanionId { kiwi, mau, lumi, pico, hedge }

enum Emotion { neutral, thinking, happy, encouraging, celebrating, waving, reading }

enum CompanionSurface {
  onboardingStep1,
  onboardingStep2Picker,
  homeNodePeek,
  homeAdventure,
  lessonFraming,
  lessonHint1,
  lessonHint2,
  lessonWrong,
  lessonRetry,
  lessonMulti,
  lessonMastery,
  habitat,
  regionCeremony,
  gradeCeremony,
  idleInactive,
}

enum AgeTier { k2, middle, senior }

enum DismissReason { autoFade, kidDismissed, surfaceChanged, deepThinkRetreat }

// ── Surface string mapping (matches backend) ─────────────────────────

const _surfaceStrings = {
  CompanionSurface.onboardingStep1: 'onboarding_wizard_step1',
  CompanionSurface.onboardingStep2Picker: 'onboarding_wizard_step2_picker',
  CompanionSurface.homeNodePeek: 'home_recommended_node_peek',
  CompanionSurface.homeAdventure: 'home_today_adventure_card',
  CompanionSurface.lessonFraming: 'lesson_problem_framing',
  CompanionSurface.lessonHint1: 'lesson_hint_first',
  CompanionSurface.lessonHint2: 'lesson_hint_second',
  CompanionSurface.lessonWrong: 'lesson_wrong_answer',
  CompanionSurface.lessonRetry: 'lesson_second_attempt',
  CompanionSurface.lessonMulti: 'lesson_multi_step',
  CompanionSurface.lessonMastery: 'lesson_mastery_moment',
  CompanionSurface.habitat: 'habitat_tab',
  CompanionSurface.regionCeremony: 'region_completion_ceremony',
  CompanionSurface.gradeCeremony: 'grade_promotion_ceremony',
  CompanionSurface.idleInactive: 'idle_inactive',
};

String surfaceToString(CompanionSurface s) => _surfaceStrings[s] ?? s.name;

// ── Data models ──────────────────────────────────────────────────────

class CompanionData {
  final CompanionId id;
  final String name;
  final String region;
  final String role;
  final Color signatureColor;
  final Color signatureColorSoft;
  final Color signatureColorText;
  final String? habitatRegionId;
  final bool isDefault;
  final bool shipped;

  const CompanionData({
    required this.id,
    required this.name,
    required this.region,
    required this.role,
    required this.signatureColor,
    required this.signatureColorSoft,
    required this.signatureColorText,
    this.habitatRegionId,
    this.isDefault = false,
    this.shipped = false,
  });

  factory CompanionData.fromJson(Map<String, dynamic> j) => CompanionData(
        id: CompanionId.values.firstWhere((e) => e.name == j['id']),
        name: j['name'] ?? '',
        region: j['region'] ?? '',
        role: j['role'] ?? '',
        signatureColor: _hexToColor(j['signature_color'] ?? '#16A34A'),
        signatureColorSoft: _hexToColor(j['signature_color_soft'] ?? '#D1FAE5'),
        signatureColorText: _hexToColor(j['signature_color_text'] ?? '#065F46'),
        habitatRegionId: j['habitat_region_id'],
        isDefault: j['is_default'] ?? false,
        shipped: j['shipped'] ?? false,
      );
}

class UserCompanionState {
  CompanionId chosenPrimary;
  AgeTier ageTier;
  bool audioEnabled;

  UserCompanionState({
    this.chosenPrimary = CompanionId.kiwi,
    this.ageTier = AgeTier.k2,
    this.audioEnabled = true,
  });

  Map<String, dynamic> toJson() => {
        'chosen_primary_companion_id': chosenPrimary.name,
        'age_tier': ageTier.name,
        'audio_enabled': audioEnabled,
      };

  factory UserCompanionState.fromJson(Map<String, dynamic> j) =>
      UserCompanionState(
        chosenPrimary: CompanionId.values.firstWhere(
          (e) => e.name == (j['chosen_primary_companion_id'] ?? 'kiwi'),
          orElse: () => CompanionId.kiwi,
        ),
        ageTier: AgeTier.values.firstWhere(
          (e) => e.name == (j['age_tier'] ?? 'k2'),
          orElse: () => AgeTier.k2,
        ),
        audioEnabled: j['audio_enabled'] ?? true,
      );
}

class SummonResponse {
  final CompanionId primaryId;
  final Emotion primaryEmotion;
  final CompanionId? secondaryId;
  final Emotion? secondaryEmotion;
  final Map<String, String> assetPaths;
  final bool fallbackUsed;
  final String? fallbackReason;
  final bool showAllFive;

  const SummonResponse({
    required this.primaryId,
    required this.primaryEmotion,
    this.secondaryId,
    this.secondaryEmotion,
    this.assetPaths = const {},
    this.fallbackUsed = false,
    this.fallbackReason,
    this.showAllFive = false,
  });

  factory SummonResponse.fromJson(Map<String, dynamic> j) => SummonResponse(
        primaryId: CompanionId.values.firstWhere(
          (e) => e.name == j['primary_companion_id'],
          orElse: () => CompanionId.kiwi,
        ),
        primaryEmotion: Emotion.values.firstWhere(
          (e) => e.name == j['primary_emotion'],
          orElse: () => Emotion.neutral,
        ),
        secondaryId: j['secondary_companion_id'] != null
            ? CompanionId.values.firstWhere(
                (e) => e.name == j['secondary_companion_id'],
                orElse: () => CompanionId.kiwi,
              )
            : null,
        secondaryEmotion: j['secondary_emotion'] != null
            ? Emotion.values.firstWhere(
                (e) => e.name == j['secondary_emotion'],
                orElse: () => Emotion.celebrating,
              )
            : null,
        assetPaths: Map<String, String>.from(j['asset_paths'] ?? {}),
        fallbackUsed: j['fallback_used'] ?? false,
        fallbackReason: j['fallback_reason'],
        showAllFive: j['show_all_five'] ?? false,
      );
}

// ── Client-side companion config (cached per session) ────────────────

class CompanionConfig {
  final List<CompanionData> cast;
  final CompanionId chosenPrimary;
  final AgeTier ageTier;
  final bool audioEnabled;
  final List<String> prefetchManifest;
  final Map<String, dynamic> performanceBudgets;
  final Map<String, dynamic> idleBehaviors;
  final Map<String, dynamic> constraints;

  const CompanionConfig({
    required this.cast,
    required this.chosenPrimary,
    required this.ageTier,
    required this.audioEnabled,
    required this.prefetchManifest,
    required this.performanceBudgets,
    required this.idleBehaviors,
    required this.constraints,
  });

  factory CompanionConfig.fromJson(Map<String, dynamic> j) => CompanionConfig(
        cast: (j['cast'] as List).map((c) => CompanionData.fromJson(c)).toList(),
        chosenPrimary: CompanionId.values.firstWhere(
          (e) => e.name == j['chosen_primary'],
          orElse: () => CompanionId.kiwi,
        ),
        ageTier: AgeTier.values.firstWhere(
          (e) => e.name == j['age_tier'],
          orElse: () => AgeTier.k2,
        ),
        audioEnabled: j['audio_enabled'] ?? true,
        prefetchManifest: List<String>.from(j['prefetch_manifest'] ?? []),
        performanceBudgets: Map<String, dynamic>.from(j['performance_budgets'] ?? {}),
        idleBehaviors: Map<String, dynamic>.from(j['idle_behaviors'] ?? {}),
        constraints: Map<String, dynamic>.from(j['constraints'] ?? {}),
      );

  CompanionData get primary => cast.firstWhere(
        (c) => c.id == chosenPrimary,
        orElse: () => cast.first,
      );

  bool isShipped(CompanionId id) => cast.any((c) => c.id == id && c.shipped);
}

// ── Default emotions per surface ─────────────────────────────────────

const _surfaceEmotions = {
  CompanionSurface.onboardingStep1: Emotion.waving,
  CompanionSurface.onboardingStep2Picker: Emotion.waving,
  CompanionSurface.homeNodePeek: Emotion.neutral,
  CompanionSurface.homeAdventure: Emotion.happy,
  CompanionSurface.lessonFraming: Emotion.reading,
  CompanionSurface.lessonHint1: Emotion.thinking,
  CompanionSurface.lessonHint2: Emotion.thinking,
  CompanionSurface.lessonWrong: Emotion.encouraging,
  CompanionSurface.lessonRetry: Emotion.encouraging,
  CompanionSurface.lessonMulti: Emotion.thinking,
  CompanionSurface.lessonMastery: Emotion.celebrating,
  CompanionSurface.habitat: Emotion.neutral,
  CompanionSurface.regionCeremony: Emotion.celebrating,
  CompanionSurface.gradeCeremony: Emotion.celebrating,
  CompanionSurface.idleInactive: Emotion.neutral,
};

// ── Client-side summon resolver (pure function, <1ms) ────────────────

SummonResponse resolveCompanion({
  required CompanionSurface surface,
  required CompanionConfig config,
  int problemStepsRequired = 1,
  int picoAppearancesInLesson = 0,
  bool kidTyping = false,
  int lastKidActionMsAgo = 0,
}) {
  final primary = config.chosenPrimary;
  CompanionId candidate;
  CompanionId? secondaryId;
  Emotion? secondaryEmotion;
  bool fallbackUsed = false;
  String? fallbackReason;
  bool showAll = false;

  // Rule lookup
  switch (surface) {
    case CompanionSurface.onboardingStep1:
      candidate = CompanionId.kiwi;
      break;
    case CompanionSurface.onboardingStep2Picker:
      showAll = true;
      candidate = primary;
      break;
    case CompanionSurface.lessonHint2:
      candidate = CompanionId.lumi;
      break;
    case CompanionSurface.lessonRetry:
      candidate = CompanionId.mau;
      break;
    case CompanionSurface.lessonMulti:
      candidate = problemStepsRequired > 1 ? CompanionId.hedge : primary;
      break;
    case CompanionSurface.lessonMastery:
      candidate = CompanionId.pico;
      secondaryId = primary;
      secondaryEmotion = Emotion.celebrating;
      break;
    case CompanionSurface.regionCeremony:
    case CompanionSurface.gradeCeremony:
      showAll = true;
      candidate = primary;
      break;
    default:
      candidate = primary;
  }

  // Pico cap
  if (candidate == CompanionId.pico && picoAppearancesInLesson >= 1) {
    candidate = primary;
    secondaryId = null;
    secondaryEmotion = null;
    fallbackUsed = true;
    fallbackReason = 'pico_max_1_per_lesson';
  }

  // Hedge gate
  if (candidate == CompanionId.hedge && problemStepsRequired <= 1) {
    candidate = primary;
    fallbackUsed = true;
    fallbackReason = 'hedge_single_step_blocked';
  }

  // Ship version gate
  if (!config.isShipped(candidate)) {
    fallbackUsed = true;
    fallbackReason = 'unshipped_companion';
    candidate = primary;
    if (!config.isShipped(candidate)) candidate = CompanionId.kiwi;
  }
  if (secondaryId != null && !config.isShipped(secondaryId!)) {
    secondaryId = null;
    secondaryEmotion = null;
  }

  // Resolve emotion
  Emotion emotion = _surfaceEmotions[surface] ?? Emotion.neutral;
  if (surface == CompanionSurface.lessonHint2 && candidate == CompanionId.lumi) {
    emotion = primary == CompanionId.lumi ? Emotion.encouraging : Emotion.thinking;
  }

  // Build asset paths
  final tier = config.ageTier.name;
  final cid = candidate.name;
  final paths = <String, String>{
    'pose_svg': '/assets/companions/$cid/$tier/${emotion.name}.svg',
    'silhouette_svg': '/assets/companions/$cid/silhouette.svg',
  };
  if (secondaryId != null) {
    final sid = secondaryId!.name;
    final se = (secondaryEmotion ?? Emotion.celebrating).name;
    paths['secondary_pose_svg'] = '/assets/companions/$sid/$tier/$se.svg';
  }

  return SummonResponse(
    primaryId: candidate,
    primaryEmotion: emotion,
    secondaryId: secondaryId,
    secondaryEmotion: secondaryEmotion,
    assetPaths: paths,
    fallbackUsed: fallbackUsed,
    fallbackReason: fallbackReason,
    showAllFive: showAll,
  );
}

// ── Helpers ──────────────────────────────────────────────────────────

Color _hexToColor(String hex) {
  hex = hex.replaceFirst('#', '');
  if (hex.length == 6) hex = 'FF$hex';
  return Color(int.parse(hex, radix: 16));
}
