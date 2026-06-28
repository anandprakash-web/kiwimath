import '../models/anchor.dart';
import '../models/enums.dart';
import '../models/selectors.dart';
import 'section_content.dart';

/// Builds a layered [Anchor] from a user selection — the inverse of
/// [AnchorResolver]. The renderer calls this the instant a user highlights,
/// capturing the quote + surrounding context + character position (and an
/// optional format-native structural locator) so the mark can be re-located
/// later even after reflow or a re-published book.
///
/// [start]/[end] are offsets into `content.canonical` (the normalized stream),
/// which is exactly the space the resolver searches — so construction and
/// resolution are guaranteed to speak the same coordinates.
class AnchorFactory {
  /// Default amount of surrounding text captured as prefix/suffix context.
  static const int defaultContextLen = 24;

  static Anchor fromSelection({
    required SectionContent content,
    required int start,
    required int end,
    int contextLen = defaultContextLen,
    StructuralSelector? structural,
  }) {
    final canon = content.canonical;
    if (start < 0 || end > canon.length || start >= end) {
      throw RangeError(
          'Invalid selection [$start, $end) over ${canon.length} chars');
    }
    final exact = canon.substring(start, end);
    final prefix =
        canon.substring(start - contextLen < 0 ? 0 : start - contextLen, start);
    final suffixEnd =
        end + contextLen > canon.length ? canon.length : end + contextLen;
    final suffix = canon.substring(end, suffixEnd);

    return Anchor(
      sectionId: content.sectionId,
      structural: structural,
      quote: TextQuoteSelector(
        exact: exact,
        prefix: prefix.isEmpty ? null : prefix,
        suffix: suffix.isEmpty ? null : suffix,
      ),
      position: TextPositionSelector(start, end),
      state: AnchorState.resolved,
    );
  }
}
