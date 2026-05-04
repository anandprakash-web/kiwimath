import 'package:flutter/material.dart';

/// Kiwimath design tokens — v7.0 play-first kids' brand.
///
/// Primary brand: Kiwimath Orange (#FF6D00) + Warm Cream (#FFF8F0)
/// Identity: Standalone kids' math app — playful, warm, encouraging.
/// No parent company branding on user-facing surfaces.
///
/// K-2 (grades 1-2): Warm, playful, big rounded shapes, cute Kiwi mascot.
/// 3-5 (grades 3-5): Modern, sharper, anime-inspired energy.

// ===========================================================================
// Shared base colors
// ===========================================================================
class KiwiColors {
  // Brand — Kiwimath orange (primary)
  static const Color kiwiPrimary = Color(0xFFFF6D00);      // Kiwimath orange
  static const Color kiwiPrimaryDark = Color(0xFFE65100);  // Deep orange
  static const Color kiwiPrimaryLight = Color(0xFFFFF3E0); // Light orange mist

  // Brand — warm cream surfaces
  static const Color cream = Color(0xFFFFF8F0);           // Primary background
  static const Color creamDark = Color(0xFFF5EFDF);       // Darker cream surface

  // Correct / incorrect feedback (semantic — never used for branding)
  static const Color kiwiGreen = Color(0xFF4CAF50);       // Correct answer
  static const Color kiwiGreenDark = Color(0xFF2E7D32);   // Correct text
  static const Color kiwiGreenLight = Color(0xFFE8F5E9);  // Correct bg

  // Accent palette — world-inspired
  static const Color coral = Color(0xFFFF6B6B);
  static const Color amber = Color(0xFFFFB74D);
  static const Color teal = Color(0xFF26C6DA);
  static const Color indigo = Color(0xFF7C4DFF);
  static const Color sky = Color(0xFF42A5F5);
  static const Color sunset = Color(0xFFFF8A65);  // Warm accent

  // Functional — feedback colors
  static const Color correct = Color(0xFF66BB6A);
  static const Color correctBg = Color(0xFFE8F5E9);
  static const Color wrong = Color(0xFFFF8A65);
  static const Color wrongBg = Color(0xFFFFF3E0);

  // Path states
  static const Color pathDone = Color(0xFFFF6D00);        // Orange for completed
  static const Color pathCurrent = Color(0xFFFF9100);     // Bright orange for current
  static const Color pathLocked = Color(0xFFE0E0E0);

  // Currency / gamification
  static const Color gemBlue = Color(0xFF448AFF);
  static const Color xpPurple = Color(0xFFAA00FF);
  static const Color gemGold = Color(0xFFFFD600);
  static const Color streakWarm = Color(0xFFFF8A65);   // Gentle, warm streak color
  static const Color leagueBlue = Color(0xFF2979FF);

  // Surfaces
  static const Color background = Color(0xFFFFF8F0);     // Warm cream
  static const Color backgroundDark = Color(0xFFF5EFDF); // Darker cream
  static const Color cardBg = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF1A1A2E);
  static const Color textMid = Color(0xFF4A4A5A);
  static const Color textMuted = Color(0xFF9A9AAA);

  // Visual card backgrounds
  static const Color visualYellowBg = Color(0xFFFFFDE7);
  static const Color visualYellowBorder = Color(0xFFFFD54F);
  static const Color visualBlueBg = Color(0xFFE1F5FE);
  static const Color visualBlueBorder = Color(0xFF4FC3F7);

  // Candy topic card palette — 12 vivid gradients
  // Index 0 is Kiwimath orange (brand)
  static const List<List<Color>> topicGradients = [
    [Color(0xFFFF6D00), Color(0xFFE65100)], // Kiwimath orange (brand)
    [Color(0xFF448AFF), Color(0xFF2962FF)], // electric blue
    [Color(0xFFFF4081), Color(0xFFF50057)], // bubblegum pink
    [Color(0xFFAA00FF), Color(0xFF7C4DFF)], // grape
    [Color(0xFF00E5FF), Color(0xFF00B8D4)], // aqua
    [Color(0xFFFF8A65), Color(0xFFFF5722)], // sunset orange
    [Color(0xFFFFD600), Color(0xFFFFC400)], // sunshine
    [Color(0xFF76FF03), Color(0xFF64DD17)], // lime
    [Color(0xFFFF6E40), Color(0xFFFF3D00)], // coral
    [Color(0xFF536DFE), Color(0xFF304FFE)], // indigo pop
    [Color(0xFFFF80AB), Color(0xFFFF4081)], // rose
    [Color(0xFF1DE9B6), Color(0xFF00BFA5)], // mint
  ];
}

// ===========================================================================
// Grade tier
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

  /// K-2: Warm, playful orange — friendly and inviting.
  static const junior = KiwiTierColors(
    primary: Color(0xFFFF6D00),        // Kiwimath orange
    primaryDark: Color(0xFFE65100),    // Deep orange
    accent: Color(0xFFFFD600),         // Sunshine yellow
    background: Color(0xFFFFF8F0),     // Warm cream
    backgroundDark: Color(0xFFF5EFDF),
    cardBg: Color(0xFFFFFFFF),
    textPrimary: Color(0xFF1A1A2E),
    textSecondary: Color(0xFF4A4A5A),
    textMuted: Color(0xFF9A9AAA),
    streakGradientStart: Color(0xFFFF8A65),
    streakGradientEnd: Color(0xFFFF5722),
    buttonGradientStart: Color(0xFFFF6D00),  // Kiwimath orange
    buttonGradientEnd: Color(0xFFE65100),    // Deep orange
    topicCardBorder: Color(0xFFFFE0B2),      // Soft orange border
  );

  /// 3-5: Deep orange + indigo energy — sharper, more mature.
  static const senior = KiwiTierColors(
    primary: Color(0xFFE65100),        // Deep orange
    primaryDark: Color(0xFFBF360C),    // Darkest orange
    accent: Color(0xFF7C4DFF),         // Purple accent for contrast
    background: Color(0xFFFFF8F0),     // Warm cream (consistent brand)
    backgroundDark: Color(0xFFF0E8DD),
    cardBg: Color(0xFFFFFFFF),
    textPrimary: Color(0xFF1A1A2E),
    textSecondary: Color(0xFF7C4DFF),  // Purple secondary
    textMuted: Color(0xFF9A9AAA),
    streakGradientStart: Color(0xFFFF8A65),
    streakGradientEnd: Color(0xFFFF5722),
    buttonGradientStart: Color(0xFFE65100),
    buttonGradientEnd: Color(0xFFBF360C),
    topicCardBorder: Color(0xFFFFCC80),
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
    fontFamily: 'Nunito',
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
    fontFamily: 'Poppins',
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

  String get mascotStyle => isJunior ? 'chibi' : 'anime';

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
