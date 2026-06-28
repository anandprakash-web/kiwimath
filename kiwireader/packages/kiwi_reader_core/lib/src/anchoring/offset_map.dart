import 'text_normalizer.dart';

/// Bidirectional map between a raw DISPLAY string (arbitrary whitespace and
/// line breaks — what the reader paints) and its normalized CANONICAL form
/// (single-spaced, trimmed — what anchors are expressed in).
///
/// This lets a block keep its on-screen formatting (paragraph breaks, poetry,
/// code, multi-line equations) while every annotation offset still lives in the
/// stable canonical space the [AnchorResolver] searches. Selections come in as
/// display offsets and are converted to canonical for the anchor; resolved
/// anchors come back as canonical ranges and are converted to display offsets
/// for painting.
class OffsetMap {
  final String display;
  final String canonical;

  /// canonical index -> display index of that char's start.
  final List<int> _c2d;

  OffsetMap._(this.display, this.canonical, this._c2d);

  static bool _isWs(int c) =>
      c == 0x20 ||
      c == 0x09 ||
      c == 0x0A ||
      c == 0x0D ||
      c == 0x0C ||
      c == 0x0B;

  factory OffsetMap.build(String display) {
    final c2d = <int>[];
    final buf = StringBuffer();
    var pendingSpace = false;
    var runStart = -1;
    var started = false;
    for (var i = 0; i < display.length; i++) {
      final ch = display.codeUnitAt(i);
      if (_isWs(ch)) {
        if (started && !pendingSpace) {
          pendingSpace = true;
          runStart = i;
        }
        continue;
      }
      if (pendingSpace) {
        buf.writeCharCode(0x20);
        c2d.add(runStart);
        pendingSpace = false;
      }
      buf.writeCharCode(ch);
      c2d.add(i);
      started = true;
    }
    return OffsetMap._(display, buf.toString(), c2d);
  }

  int get length => canonical.length;

  /// Display index for a canonical index. `canonical.length` -> `display.length`.
  int toDisplay(int canonicalIndex) {
    if (_c2d.isEmpty) return 0;
    if (canonicalIndex <= 0) return _c2d.first;
    if (canonicalIndex >= _c2d.length) return display.length;
    return _c2d[canonicalIndex];
  }

  /// Canonical index for a display index (binary search over the c2d table).
  int toCanonical(int displayIndex) {
    if (_c2d.isEmpty) return 0;
    if (displayIndex <= _c2d.first) return 0;
    if (displayIndex > _c2d.last) return _c2d.length;
    var lo = 0, hi = _c2d.length - 1, ans = 0;
    while (lo <= hi) {
      final mid = (lo + hi) >> 1;
      if (_c2d[mid] <= displayIndex) {
        ans = mid;
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    return ans;
  }

  (int, int) toCanonicalRange(int displayStart, int displayEnd) =>
      (toCanonical(displayStart), toCanonical(displayEnd));

  (int, int) toDisplayRange(int canonicalStart, int canonicalEnd) =>
      (toDisplay(canonicalStart), toDisplay(canonicalEnd));

  /// Sanity helper: the canonical produced here equals the shared normalizer's.
  bool get isConsistent => canonical == TextNormalizer.normalize(display);
}
