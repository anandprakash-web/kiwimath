import '../util/equality.dart';
import 'enums.dart';

/// W3C TextQuoteSelector: the exact text plus a little context on each side.
/// This is the reflow-proof workhorse — it survives layout changes and minor
/// edits, and the prefix/suffix disambiguate repeated phrases.
class TextQuoteSelector {
  final String exact;
  final String? prefix;
  final String? suffix;

  const TextQuoteSelector({required this.exact, this.prefix, this.suffix});

  Map<String, dynamic> toJson() => {
        'exact': exact,
        if (prefix != null) 'prefix': prefix,
        if (suffix != null) 'suffix': suffix,
      };

  factory TextQuoteSelector.fromJson(Map<String, dynamic> j) =>
      TextQuoteSelector(
        exact: j['exact'] as String,
        prefix: j['prefix'] as String?,
        suffix: j['suffix'] as String?,
      );

  @override
  bool operator ==(Object other) =>
      other is TextQuoteSelector && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(exact, prefix, suffix);
}

/// W3C TextPositionSelector: character offsets in the section's *normalized*
/// text stream. Used to disambiguate repeated quotes and as a last resort.
class TextPositionSelector {
  final int start;
  final int end;

  const TextPositionSelector(this.start, this.end);

  int get length => end - start;

  Map<String, dynamic> toJson() => {'start': start, 'end': end};

  factory TextPositionSelector.fromJson(Map<String, dynamic> j) =>
      TextPositionSelector(j['start'] as int, j['end'] as int);

  @override
  bool operator ==(Object other) =>
      other is TextPositionSelector && start == other.start && end == other.end;
  @override
  int get hashCode => Object.hash(start, end);
}

/// Format-native locator: EPUB CFI, PDF page+quads, or HTML DOM range.
/// Fast and exact, but brittle across reflow / re-publish — hence it is only
/// the *first* layer the resolver tries.
class StructuralSelector {
  final LocatorType type;
  final Map<String, dynamic> data;

  const StructuralSelector(this.type, this.data);

  Map<String, dynamic> toJson() => {'type': type.name, 'data': data};

  factory StructuralSelector.fromJson(Map<String, dynamic> j) =>
      StructuralSelector(
        LocatorType.values.byName(j['type'] as String),
        Map<String, dynamic>.from(j['data'] as Map),
      );

  @override
  bool operator ==(Object other) =>
      other is StructuralSelector && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(type, data.length);
}
