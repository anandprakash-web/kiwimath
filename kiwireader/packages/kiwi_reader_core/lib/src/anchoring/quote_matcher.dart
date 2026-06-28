import '../models/selectors.dart';

/// A located span in canonical text (half-open: [start, end)).
class MatchSpan {
  final int start;
  final int end;
  const MatchSpan(this.start, this.end);
  int get length => end - start;

  @override
  bool operator ==(Object other) =>
      other is MatchSpan && other.start == start && other.end == end;
  @override
  int get hashCode => Object.hash(start, end);
  @override
  String toString() => 'MatchSpan($start, $end)';
}

/// Finds a [TextQuoteSelector] inside a canonical text string.
///
/// Strategy: exact occurrences first; if several, narrow by prefix/suffix
/// context; if none, fall back to a bounded fuzzy search for minor edits.
class QuoteMatcher {
  final String text;
  QuoteMatcher(this.text);

  /// All exact occurrences of [q], narrowed by prefix/suffix context when that
  /// narrowing still leaves at least one candidate.
  List<MatchSpan> findAll(TextQuoteSelector q) {
    final exact = q.exact;
    if (exact.isEmpty) return const [];
    final all = <MatchSpan>[];
    var i = text.indexOf(exact);
    while (i != -1) {
      all.add(MatchSpan(i, i + exact.length));
      i = text.indexOf(exact, i + 1);
    }
    if (all.length <= 1) return all;

    final hasContext =
        (q.prefix?.isNotEmpty ?? false) || (q.suffix?.isNotEmpty ?? false);
    if (!hasContext) return all;
    final filtered = all.where((m) => _contextOk(m, q)).toList();
    return filtered.isNotEmpty ? filtered : all;
  }

  bool _contextOk(MatchSpan m, TextQuoteSelector q) {
    final prefix = q.prefix;
    if (prefix != null && prefix.isNotEmpty) {
      final before = text.substring(0, m.start);
      final tail = before.length >= prefix.length
          ? before.substring(before.length - prefix.length)
          : before;
      final cmp = prefix.length > tail.length
          ? prefix.substring(prefix.length - tail.length)
          : prefix;
      if (tail != cmp) return false;
    }
    final suffix = q.suffix;
    if (suffix != null && suffix.isNotEmpty) {
      final after = text.substring(m.end);
      final head = after.length >= suffix.length
          ? after.substring(0, suffix.length)
          : after;
      final cmp = suffix.length > head.length
          ? suffix.substring(0, head.length)
          : suffix;
      if (head != cmp) return false;
    }
    return true;
  }

  /// Best fuzzy match for [target] with similarity >= [threshold] (0..1), or
  /// null. Slides word-boundary-aligned windows of a few candidate lengths and
  /// scores them with normalized Levenshtein similarity. Bounded for the
  /// section-sized strings we resolve against (runs in an isolate in prod).
  MatchSpan? findFuzzy(String target, {double threshold = 0.82}) {
    if (target.isEmpty || text.isEmpty) return null;
    final n = target.length;
    final candidateLengths = <int>{n - 2, n - 1, n, n + 1, n + 2}
      ..removeWhere((l) => l <= 0);
    MatchSpan? best;
    var bestSim = threshold;
    for (final start in _wordBoundaryStarts()) {
      for (final len in candidateLengths) {
        final end = start + len;
        if (end > text.length) continue;
        final sim = _similarity(text.substring(start, end), target);
        if (sim >= bestSim) {
          bestSim = sim;
          best = MatchSpan(start, end);
        }
      }
    }
    return best;
  }

  List<int> _wordBoundaryStarts() {
    final starts = <int>[0];
    for (var i = 1; i < text.length; i++) {
      if (text[i - 1] == ' ') starts.add(i);
    }
    return starts;
  }

  static double _similarity(String a, String b) {
    final maxLen = a.length > b.length ? a.length : b.length;
    if (maxLen == 0) return 1.0;
    return 1.0 - _levenshtein(a, b) / maxLen;
  }

  static int _levenshtein(String a, String b) {
    final m = a.length, n = b.length;
    if (m == 0) return n;
    if (n == 0) return m;
    var prev = List<int>.generate(n + 1, (j) => j);
    var cur = List<int>.filled(n + 1, 0);
    for (var i = 1; i <= m; i++) {
      cur[0] = i;
      for (var j = 1; j <= n; j++) {
        final cost = a[i - 1] == b[j - 1] ? 0 : 1;
        final del = prev[j] + 1, ins = cur[j - 1] + 1, sub = prev[j - 1] + cost;
        var min = del < ins ? del : ins;
        if (sub < min) min = sub;
        cur[j] = min;
      }
      final tmp = prev;
      prev = cur;
      cur = tmp;
    }
    return prev[n];
  }
}
