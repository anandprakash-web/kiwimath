/// Normalizes section text into a stable canonical stream.
///
/// All quote and position selectors operate in this canonical space so that
/// cosmetic whitespace differences (re-flow, re-export, indentation changes)
/// never shift an anchor. The transform is idempotent.
class TextNormalizer {
  static final _ws = RegExp(r'\s+');

  /// Collapse every run of whitespace to a single space and trim the ends.
  static String normalize(String input) => input.replaceAll(_ws, ' ').trim();
}
