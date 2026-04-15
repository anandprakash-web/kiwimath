import 'package:flutter/material.dart';

/// Kiwimath brand colors + theme.
/// v0 is utilitarian — polish and mascot come in Week 4.
class KiwiColors {
  static const Color kiwiGreen = Color(0xFF7CB342);
  static const Color kiwiGreenDark = Color(0xFF558B2F);
  static const Color kiwiGreenLight = Color(0xFFDCEDC8);
  static const Color kiwiBrown = Color(0xFF795548);
  static const Color correct = Color(0xFF43A047);
  static const Color wrong = Color(0xFFE53935);
  static const Color gemGold = Color(0xFFFFB300);
  static const Color background = Color(0xFFFFFBF0);
  static const Color cardBg = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF2E2E2E);
}

ThemeData kiwiTheme() {
  return ThemeData(
    useMaterial3: true,
    scaffoldBackgroundColor: KiwiColors.background,
    colorScheme: ColorScheme.fromSeed(
      seedColor: KiwiColors.kiwiGreen,
      primary: KiwiColors.kiwiGreen,
      brightness: Brightness.light,
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        color: KiwiColors.textDark,
      ),
      headlineMedium: TextStyle(
        fontSize: 22,
        fontWeight: FontWeight.w700,
        color: KiwiColors.textDark,
      ),
      bodyLarge: TextStyle(
        fontSize: 20,
        color: KiwiColors.textDark,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: KiwiColors.kiwiGreen,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
      ),
    ),
  );
}
