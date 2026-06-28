import '../models/anchor.dart';
import '../models/enums.dart';
import '../models/selectors.dart';

/// A rectangle of plain doubles (no Flutter dependency). In a [PdfRegion] the
/// values are normalized to 0..1 of the page; after [PdfAnchorFactory.rectsForPage]
/// they are in the target render space (pixels). Origin is top-left.
class RectD {
  final double left;
  final double top;
  final double right;
  final double bottom;

  const RectD(this.left, this.top, this.right, this.bottom);

  double get width => right - left;
  double get height => bottom - top;

  RectD scaled(double sx, double sy) =>
      RectD(left * sx, top * sy, right * sx, bottom * sy);

  Map<String, dynamic> toJson() =>
      {'l': left, 't': top, 'r': right, 'b': bottom};

  factory RectD.fromJson(Map<String, dynamic> j) => RectD(
        (j['l'] as num).toDouble(),
        (j['t'] as num).toDouble(),
        (j['r'] as num).toDouble(),
        (j['b'] as num).toDouble(),
      );

  @override
  bool operator ==(Object other) =>
      other is RectD &&
      other.left == left &&
      other.top == top &&
      other.right == right &&
      other.bottom == bottom;

  @override
  int get hashCode => Object.hash(left, top, right, bottom);

  @override
  String toString() => 'RectD($left, $top, $right, $bottom)';
}

/// A fixed-layout PDF location: a page index plus the normalized (0..1) quad
/// rectangles covering the selection on that page.
class PdfRegion {
  final int page; // 1-based, matching pdfrx page numbers
  final List<RectD> rects;

  const PdfRegion(this.page, this.rects);

  Map<String, dynamic> toJson() => {
        'page': page,
        'rects': rects.map((r) => r.toJson()).toList(),
      };

  factory PdfRegion.fromJson(Map<String, dynamic> j) => PdfRegion(
        (j['page'] as num).toInt(),
        (j['rects'] as List)
            .map((e) => RectD.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

/// Builds and reads fixed-layout PDF anchors. The rects are stored normalized
/// to the page (0..1) so a highlight survives zoom, DPI and device size — the
/// PDF analogue of the text [AnchorFactory]. When the PDF has a text layer a
/// [TextQuoteSelector] is also attached (so the mark can survive a re-export);
/// scanned PDFs pass `quote: null` and become region-only annotations.
class PdfAnchorFactory {
  static double _clamp01(double v) => v < 0 ? 0 : (v > 1 ? 1 : v);

  static Anchor fromSelection({
    required String sectionId, // e.g. 'page:42'
    required int page,
    required double pageWidth,
    required double pageHeight,
    required List<RectD> rects, // in page-point coordinates
    TextQuoteSelector? quote,
  }) {
    final normalized = [
      for (final r in rects)
        RectD(
          _clamp01(r.left / pageWidth),
          _clamp01(r.top / pageHeight),
          _clamp01(r.right / pageWidth),
          _clamp01(r.bottom / pageHeight),
        ),
    ];
    return Anchor(
      sectionId: sectionId,
      structural: StructuralSelector(
          LocatorType.pdfQuads, PdfRegion(page, normalized).toJson()),
      quote: quote,
      state: AnchorState.resolved,
    );
  }

  /// Reads the [PdfRegion] from a `pdfQuads` anchor, or null if it isn't one.
  static PdfRegion? regionOf(Anchor anchor) {
    final s = anchor.structural;
    if (s == null || s.type != LocatorType.pdfQuads) return null;
    return PdfRegion.fromJson(Map<String, dynamic>.from(s.data));
  }

  /// Denormalizes the region's rects to a rendered page size (pixels), ready
  /// to paint. Returns empty for non-PDF anchors.
  static List<RectD> rectsForPage(Anchor anchor,
      {required double width, required double height}) {
    final region = regionOf(anchor);
    if (region == null) return const [];
    return [for (final r in region.rects) r.scaled(width, height)];
  }
}
