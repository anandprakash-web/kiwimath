import 'package:flutter/material.dart';

/// Kiwimath design tokens — grade-adaptive theming.
///
/// K-2 (grades 1-2): Bright, playful, kid-friendly. Big rounded shapes,
///   warm colors, cute mascot emphasis, larger touch targets.
///
/// 3-5 (grades 3-5): Modern, cooler palette, anime-inspired feel.
///   Deeper colors, sharper corners, more sophisticated layout.

// ===========================================================================
// Shared base colors (used across both tiers)
// ===========================================================================
class KiwiColors {
  // Brand — v4.1 warm kiwi green
  static const Color kiwiGreen = Color(0xFF4CAF50);
  static const Color kiwiGreenDark = Color(0xFF2E7D32);
  static const Color kiwiGreenLight = Color(0xFFE8F5E9);

  // v4.1 palette additions
  static const Color coral = Color(0xFFFF6B6B);
  static const Color amber = Color(0xFFFFB74D);
  static const Color teal = Color(0xFF26C6DA);
  static const Color indigo = Color(0xFF7C4DFF);
  static const Color sky = Color(0xFF42A5F5);

  // Functional — v4.1 softer feedback colors
  static const Color correct = Color(0xFF66BB6A);
  static const Color correctBg = Color(0xFFE8F5E9);
  static const Color wrong = Color(0xFFFF8A65);
  static const Color wrongBg = Color(0xFFFFF3E0);

  // Path states
  static const Color pathDone = Color(0xFF4CAF50);
  static const Color pathCurrent = Color(0xFFFFB74D);
  static const Color pathLocked = Color(0xFFE0E0E0);

  // Legacy functional colors (still used across tiers)
  static const Color gemBlue = Color(0xFF448AFF);
  static const Color xpPurple = Color(0xFFAA00FF);
  static const Color gemGold = Color(0xFFFFD600);
  static const Color streakOrange = Color(0xFFFF6D00);
  static const Color leagueBlue = Color(0xFF2979FF);

  // Warm / step-down — richer tones
  static const Color warmOrange = Color(0xFFFF9100);
  static const Color warmOrangeDark = Color(0xFFE65100);
  static const Color warmOrangeBg = Color(0xFFFFF3E0);
  static const Color warmOrangeBorder = Color(0xFFFFCC80);

  // Surfaces — v4.1 warm cream
  static const Color background = Color(0xFFFFFBF5);
  static const Color backgroundDark = Color(0xFFF5F0EA);
  static const Color cardBg = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF1A1A2E);
  static const Color textMid = Color(0xFF4A4A5A);
  static const Color textMuted = Color(0xFF9A9AAA);

  // Visual card backgrounds — brighter
  static const Color visualYellowBg = Color(0xFFFFFDE7);
  static const Color visualYellowBorder = Color(0xFFFFD54F);
  static const Color visualBlueBg = Color(0xFFE1F5FE);
  static const Color visualBlueBorder = Color(0xFF4FC3F7);

  // Candy topic card palette — 12 vivid gradients
  static const List<List<Color>> topicGradients = [
    [Color(0xFF00E676), Color(0xFF00C853)], // emerald
    [Color(0xFF448AFF), Color(0xFF2962FF)], // electric blue
    [Color(0xFFFF6D00), Color(0xFFFF3D00)], // tangerine
    [Color(0xFFAA00FF), Color(0xFF7C4DFF)], // grape
    [Color(0xFFFF4081), Color(0xFFF50057)], // bubblegum pink
    [Color(0xFF00E5FF), Color(0xFF00B8D4)], // aqua
    [Color(0xFFFFD600), Color(0xFFFFC400)], // sunshine
    [Color(0xFF76FF03), Color(0xFF64DD17)], // lime
    [Color(0xFFFF6E40), Color(0xFFFF3D00)], // coral
    [Color(0xFF536DFE), Color(0xFF304FFE)], // indigo pop
    [Color(0xFFFF80AB), Color(0xFFFF4081)], // rose
    [Color(0xFF1DE9B6), Color(0xFF00BFA5)], // mint
  ];
}

// ===========================================================================
// Grade tier — determines which theme to use
// ===========================================================================
enum GradeTier { junior, senior }

GradeTier gradeTier(int grade) => grade <= 2 ? GradeTier.junior : GradeTier.senior;

// ===========================================================================
// Tier-specific design tokens
// ===========================================================================
class KiwiTierColors {
  final Color primary;
  final Color primaryDark;
  final Color accent;
  final Color background;
  final Color backgroundDark;
  final Color cardBg;
  final Color textPrimary;
  final Color textSecondary;
  final Color textMuted;
  final Color streakGradientStart;
  final Color streakGradientEnd;
  final Color buttonGradientStart;
  final Color buttonGradientEnd;
  final Color topicCardBorder;

  const KiwiTierColors({
    required this.primary,
    required this.primaryDark,
    required this.accent,
    required this.background,
    required this.backgroundDark,
    required this.cardBg,
    required this.textPrimary,
    required this.textSecondary,
    required this.textMuted,
    required this.streakGradientStart,
    required this.streakGradientEnd,
    required this.buttonGradientStart,
    required this.buttonGradientEnd,
    required this.topicCardBorder,
  });

  /// K-2: v4.1 warm cream palette — friendly, playful, inviting.
  static const junior = KiwiTierColors(
    primary: Color(0xFF4CAF50),        // Kiwi green (v4.1)
    primaryDark: Color(0xFF2E7D32),
    accent: Color(0xFFFFD600),         // Sunshine yellow
    background: Color(0xFFFFFBF5),     // Warm cream (v4.1)
    backgroundDark: Color(0xFFF5F0EA), // Warm cream dark (v4.1)
    cardBg: Color(0xFFFFFFFF),
    textPrimary: Color(0xFF1A1A2E),    // v4.1 textDark
    textSecondary: Color(0xFF4A4A5A),  // v4.1 textMid
    textMuted: Color(0xFF9A9AAA),      // v4.1 textMuted
    streakGradientStart: Color(0xFFFF6D00),  // Blazing orange
    streakGradientEnd: Color(0xFFFF3D00),    // Fire red-orange
    buttonGradientStart: Color(0xFF4CAF50),  // Kiwi green (v4.1)
    buttonGradientEnd: Color(0xFF2E7D32),    // Kiwi dark (v4.1)
    topicCardBorder: Color(0xFFFFD54F),      // Golden border
  );

  /// 3-5: Electric, modern, anime-inspired energy.
  static const senior = KiwiTierColors(
    primary: Color(0xFF536DFE),       // Electric indigo
    primaryDark: Color(0xFF304FFE),
    accent: Color(0xFF00E5FF),        // Neon cyan
    background: Color(0xFFF0F4FF),    // Cool lavender white
    backgroundDark: Color(0xFFE0E4EE),
    cardBg: Color(0xFFFFFFFF),
    textPrimary: Color(0xFF1A1A2E),   // Deep navy
    textSecondary: Color(0xFF7C4DFF), // Vivid purple
    textMuted: Color(0xFF9A9AAA),
    streakGradientStart: Color(0xFF7C4DFF),  // Purple pop
    streakGradientEnd: Color(0xFF304FFE),    // Deep indigo
    buttonGradientStart: Color(0xFF448AFF),  // Bright blue
    buttonGradientEnd: Color(0xFF2962FF),    // Deep blue
    topicCardBorder: Color(0xFFB388FF),      // Lavender border
  );
}

class KiwiTierTypography {
  final double headlineSize;
  final double bodySize;
  final double chipSize;
  final double topicNameSize;
  final double buttonSize;
  final double streakNumberSize;
  final FontWeight headlineWeight;
  final String fontFamily;

  const KiwiTierTypography({
    required this.headlineSize,
    required this.bodySize,
    required this.chipSize,
    required this.topicNameSize,
    required this.buttonSize,
    required this.streakNumberSize,
    required this.headlineWeight,
    required this.fontFamily,
  });

  /// K-2: Larger, rounder, friendlier.
  static const junior = KiwiTierTypography(
    headlineSize: 20,
    bodySize: 16,
    chipSize: 14,
    topicNameSize: 15,
    buttonSize: 17,
    streakNumberSize: 40,
    headlineWeight: FontWeight.w800,
    fontFamily: 'Nunito',  // Round, friendly
  );

  /// 3-5: More compact, sharper, mature.
  static const senior = KiwiTierTypography(
    headlineSize: 17,
    bodySize: 14,
    chipSize: 12,
    topicNameSize: 13,
    buttonSize: 15,
    streakNumberSize: 34,
    headlineWeight: FontWeight.w700,
    fontFamily: 'Poppins',  // Modern, clean
  );
}

class KiwiTierShape {
  final double cardRadius;
  final double buttonRadius;
  final double chipRadius;
  final double topicCardAspect;
  final EdgeInsets buttonPadding;
  final EdgeInsets cardPadding;

  const KiwiTierShape({
    required this.cardRadius,
    required this.buttonRadius,
    required this.chipRadius,
    required this.topicCardAspect,
    required this.buttonPadding,
    required this.cardPadding,
  });

  /// K-2: Rounder, bigger touch targets.
  static const junior = KiwiTierShape(
    cardRadius: 20,
    buttonRadius: 18,
    chipRadius: 20,
    topicCardAspect: 1.4,
    buttonPadding: EdgeInsets.symmetric(vertical: 18, horizontal: 24),
    cardPadding: EdgeInsets.all(16),
  );

  /// 3-5: Sharper corners, standard sizing.
  static const senior = KiwiTierShape(
    cardRadius: 14,
    buttonRadius: 12,
    chipRadius: 16,
    topicCardAspect: 1.55,
    buttonPadding: EdgeInsets.symmetric(vertical: 14, horizontal: 20),
    cardPadding: EdgeInsets.all(12),
  );
}

// ===========================================================================
// Unified theme accessor
// ===========================================================================
class KiwiTier {
  final GradeTier tier;
  final KiwiTierColors colors;
  final KiwiTierTypography typography;
  final KiwiTierShape shape;

  KiwiTier._(this.tier, this.colors, this.typography, this.shape);

  factory KiwiTier.forGrade(int grade) {
    final t = gradeTier(grade);
    switch (t) {
      case GradeTier.junior:
        return KiwiTier._(t, KiwiTierColors.junior, KiwiTierTypography.junior, KiwiTierShape.junior);
      case GradeTier.senior:
        return KiwiTier._(t, KiwiTierColors.senior, KiwiTierTypography.senior, KiwiTierShape.senior);
    }
  }

  bool get isJunior => tier == GradeTier.junior;
  bool get isSenior => tier == GradeTier.senior;

  /// Mascot display style per tier.
  /// K-2: cute chibi style, emoji-heavy, exclamation marks.
  /// 3-5: cool anime style, minimal emoji, confident tone.
  String get mascotStyle => isJunior ? 'chibi' : 'anime';

  /// Emoji set per tier (for topic cards, feedback, etc.)
  String feedbackCorrect() => isJunior ? '\u{1F389}\u{1F31F}' : '\u{2705}';
  String feedbackWrong() => isJunior ? '\u{1F914}\u{1F4AD}' : '\u{1F504}';
  String feedbackStreak() => isJunior ? '\u{1F525}\u{2B50}' : '\u{1F525}';
}

// ===========================================================================
// Theme builder (for MaterialApp)
// ===========================================================================
ThemeData kiwiTheme({int grade = 1}) {
  final tier = KiwiTier.forGrade(grade);
  final c = tier.colors;
  final t = tier.typography;

  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: c.background,
    colorScheme: ColorScheme.fromSeed(
      seedColor: c.primary,
      primary: c.primary,
      brightness: Brightness.light,
    ),
    textTheme: TextTheme(
      headlineLarge: TextStyle(
        fontSize: t.headlineSize + 4,
        fontWeight: t.headlineWeight,
        color: c.textPrimary,
      ),
      headlineMedium: TextStyle(
        fontSize: t.bodySize + 2,
        fontWeight: FontWeight.w600,
        color: c.textPrimary,
        height: 1.45,
      ),
      bodyLarge: TextStyle(
        fontSize: t.bodySize,
        color: c.textPrimary,
      ),
      bodyMedium: TextStyle(
        fontSize: t.bodySize - 2,
        color: c.textPrimary,
      ),
      labelSmall: TextStyle(
        fontSize: t.chipSize - 1,
        fontWeight: FontWeight.w600,
        color: c.textSecondary,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: c.primary,
        foregroundColor: Colors.white,
        padding: tier.shape.buttonPadding,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
        ),
        textStyle: TextStyle(
          fontSize: t.buttonSize,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
  );
}
