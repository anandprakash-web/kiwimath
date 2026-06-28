import 'text_normalizer.dart';

/// The current state of a section as seen by the resolver.
///
/// The renderer/format layer fills this in. In particular it reports whether
/// the annotation's structural locator (CFI / PDF quads / DOM range) still
/// resolves ([structuralValid]) and, if so, where it points in canonical text.
/// The pure-Dart core treats those as opaque hints — that keeps it
/// format-agnostic and unit-testable without a PDF/EPUB engine.
class SectionContent {
  final String sectionId;
  final String text;
  final bool structuralValid;
  final int? structuralStart;
  final int? structuralEnd;

  SectionContent({
    required this.sectionId,
    required this.text,
    this.structuralValid = false,
    this.structuralStart,
    this.structuralEnd,
  });

  /// Normalized text. Computed once, lazily.
  late final String canonical = TextNormalizer.normalize(text);
}
