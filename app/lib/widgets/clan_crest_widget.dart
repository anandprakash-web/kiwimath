import 'package:flutter/material.dart';
import '../models/clan.dart';
import '../theme/kiwi_theme.dart';

/// Circular crest badge showing a clan's emoji shape on a colored background.
///
/// Used in clan cards, leaderboard rows, and detail headers.
class ClanCrestWidget extends StatelessWidget {
  final ClanCrest crest;
  final double size;

  const ClanCrestWidget({
    super.key,
    required this.crest,
    this.size = 48,
  });

  @override
  Widget build(BuildContext context) {
    final bgColor = _parseHexColor(crest.color);

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: bgColor.withOpacity(0.15),
        border: Border.all(
          color: bgColor.withOpacity(0.5),
          width: size * 0.04,
        ),
        boxShadow: [
          BoxShadow(
            color: bgColor.withOpacity(0.25),
            blurRadius: size * 0.2,
            offset: Offset(0, size * 0.06),
          ),
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: size * 0.1,
            offset: Offset(0, size * 0.04),
          ),
        ],
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            bgColor.withOpacity(0.2),
            bgColor.withOpacity(0.35),
          ],
        ),
      ),
      child: Center(
        child: Text(
          crest.emoji,
          style: TextStyle(
            fontSize: size * 0.48,
            height: 1.0,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  /// Parse a hex color string (e.g. "#FF6D00" or "FF6D00") into a [Color].
  static Color _parseHexColor(String hex) {
    final cleaned = hex.replaceFirst('#', '').trim();
    if (cleaned.length == 6) {
      final value = int.tryParse('FF$cleaned', radix: 16);
      if (value != null) return Color(value);
    } else if (cleaned.length == 8) {
      final value = int.tryParse(cleaned, radix: 16);
      if (value != null) return Color(value);
    }
    // Fallback to Kiwi primary orange.
    return KiwiColors.kiwiPrimary;
  }
}
