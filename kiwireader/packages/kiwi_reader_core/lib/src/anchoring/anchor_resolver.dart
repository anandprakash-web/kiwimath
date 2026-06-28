import '../models/anchor.dart';
import '../models/enums.dart';
import '../models/selectors.dart';
import 'quote_matcher.dart';
import 'section_content.dart';

/// The result of resolving an [Anchor] against current [SectionContent].
class ResolveResult {
  final AnchorState state;

  /// Offsets in canonical text (null when orphaned).
  final int? start;
  final int? end;

  /// The anchor with [AnchorState] (and a refreshed position selector) updated.
  final Anchor anchor;

  const ResolveResult(
      {required this.state, required this.anchor, this.start, this.end});

  bool get located => start != null && end != null;

  @override
  String toString() => 'ResolveResult(${state.name}, $start..$end)';
}

/// Implements the resolution decision tree (design Figure 4).
///
/// Order of attempts, strongest first:
///   1. Structural locator valid AND quote agrees there  -> resolved
///   2. Quote found uniquely (or context-narrowed to one) -> repaired
///   3. Quote found multiple times -> position selector disambiguates -> repaired
///   4. Quote not found exactly -> bounded fuzzy match -> approx
///   5. No quote but a position selector survives -> approx (clamped)
///   6. Nothing matches -> orphaned (data kept, surfaced in "Needs review")
class AnchorResolver {
  /// Minimum similarity (0..1) to accept a fuzzy match as [AnchorState.approx].
  final double fuzzyThreshold;

  const AnchorResolver({this.fuzzyThreshold = 0.82});

  ResolveResult resolve(Anchor anchor, SectionContent content) {
    final canonical = content.canonical;
    final quote = anchor.quote;

    // 1) Structural layer.
    if (content.structuralValid && content.structuralStart != null) {
      final s = content.structuralStart!;
      final e =
          content.structuralEnd ?? (quote != null ? s + quote.exact.length : s);
      final agrees = quote == null || _matchesAt(canonical, s, quote.exact);
      if (agrees) {
        return ResolveResult(
          state: AnchorState.resolved,
          start: s,
          end: e,
          anchor: anchor.copyWith(
            state: AnchorState.resolved,
            position: TextPositionSelector(s, e),
          ),
        );
      }
      // Structural pointer is stale (content edited under it) -> relocate by quote.
    }

    // 2 + 3) Quote relocation, with position disambiguation.
    if (quote != null && quote.exact.isNotEmpty) {
      final matcher = QuoteMatcher(canonical);
      final hits = matcher.findAll(quote);
      if (hits.length == 1) return _repaired(anchor, hits.first);
      if (hits.length > 1)
        return _repaired(anchor, _closest(hits, anchor.position));

      // 4) Minor edits -> fuzzy.
      final fuzzy = matcher.findFuzzy(quote.exact, threshold: fuzzyThreshold);
      if (fuzzy != null) {
        return ResolveResult(
          state: AnchorState.approx,
          start: fuzzy.start,
          end: fuzzy.end,
          anchor: anchor.copyWith(
            state: AnchorState.approx,
            position: TextPositionSelector(fuzzy.start, fuzzy.end),
          ),
        );
      }
    }

    // 5) Position-only last resort (e.g. region/scanned anchors with no quote).
    final pos = anchor.position;
    if ((quote == null || quote.exact.isEmpty) &&
        pos != null &&
        pos.start >= 0 &&
        pos.end <= canonical.length &&
        pos.start < pos.end) {
      return ResolveResult(
        state: AnchorState.approx,
        start: pos.start,
        end: pos.end,
        anchor: anchor.copyWith(state: AnchorState.approx),
      );
    }

    // 6) Orphan — never misplace.
    return ResolveResult(
      state: AnchorState.orphaned,
      anchor: anchor.copyWith(state: AnchorState.orphaned),
    );
  }

  ResolveResult _repaired(Anchor anchor, MatchSpan span) => ResolveResult(
        state: AnchorState.repaired,
        start: span.start,
        end: span.end,
        anchor: anchor.copyWith(
          state: AnchorState.repaired,
          position: TextPositionSelector(span.start, span.end),
        ),
      );

  static bool _matchesAt(String text, int start, String exact) {
    if (start < 0 || start + exact.length > text.length) return false;
    return text.substring(start, start + exact.length) == exact;
  }

  static MatchSpan _closest(List<MatchSpan> hits, TextPositionSelector? pos) {
    if (pos == null) return hits.first;
    var best = hits.first;
    var bestDelta = (best.start - pos.start).abs();
    for (final h in hits.skip(1)) {
      final d = (h.start - pos.start).abs();
      if (d < bestDelta) {
        bestDelta = d;
        best = h;
      }
    }
    return best;
  }
}
