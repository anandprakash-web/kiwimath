import 'package:flutter/widgets.dart';

enum ReaderTheme { light, sepia, dark }

enum ReadingMode { paginated, scroll }

/// A named highlight color. The name (token) is what gets persisted, so the
/// palette can be re-themed (e.g. dark-mode tone-mapping) without rewriting
/// stored annotations. Names also give us color-blind-safe, screen-readable
/// labels ("highlighted, green").
class HighlightColor {
  final String token;
  final Color color;
  const HighlightColor(this.token, this.color);
}

/// Default color-blind-aware palette (matches the design doc swatches).
const List<HighlightColor> kDefaultPalette = [
  HighlightColor('yellow', Color(0xFFFDE68A)),
  HighlightColor('green', Color(0xFFBBF7D0)),
  HighlightColor('blue', Color(0xFFBFDBFE)),
  HighlightColor('pink', Color(0xFFFBCFE8)),
];

/// Public configuration passed to [KiwiReader] by the host.
class ReaderConfig {
  final ReaderTheme theme;
  final ReadingMode readingMode;
  final bool enableInk; // stylus (Phase 2)
  final double fontScale;
  final List<HighlightColor> palette;

  const ReaderConfig({
    this.theme = ReaderTheme.light,
    this.readingMode = ReadingMode.paginated,
    this.enableInk = false,
    this.fontScale = 1.0,
    this.palette = kDefaultPalette,
  });

  ReaderConfig copyWith({
    ReaderTheme? theme,
    ReadingMode? readingMode,
    bool? enableInk,
    double? fontScale,
    List<HighlightColor>? palette,
  }) => ReaderConfig(
    theme: theme ?? this.theme,
    readingMode: readingMode ?? this.readingMode,
    enableInk: enableInk ?? this.enableInk,
    fontScale: fontScale ?? this.fontScale,
    palette: palette ?? this.palette,
  );
}
