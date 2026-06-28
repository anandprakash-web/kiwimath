import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:pdfrx/pdfrx.dart';

import '../host/providers.dart';
import 'content_renderer.dart';

/// Fixed-layout PDF renderer backed by `pdfrx` (PDFium).
///
/// The annotation geometry — mapping a selection to page-relative quads and
/// back to pixels — lives in the unit-tested [PdfAnchorFactory] in the core.
/// This adapter owns the bytes + page metadata and builds anchors via
/// [buildAnchor]; the actual page painting + highlight overlay is done by
/// `PdfReaderSurface` using pdfrx's per-page paint callback.
///
/// NOTE: pdfrx pulls in native PDFium, so this path is validated on a device,
/// not in the pure-Dart test sandbox.
class PdfRenderer implements ContentRenderer {
  final String bookId;
  final Uint8List bytes;
  final int pageCount;

  PdfRenderer.fromBytes(this.bookId, this.bytes, {this.pageCount = 0});

  /// Loads bytes from the host and reads the page count up front.
  static Future<PdfRenderer> open(
    BookManifest manifest,
    ContentProvider content,
  ) async {
    final stream = await content.bytes(manifest.id);
    final buffer = <int>[];
    await for (final chunk in stream) {
      buffer.addAll(chunk);
    }
    final bytes = Uint8List.fromList(buffer);
    final doc = await PdfDocument.openData(bytes);
    final count = doc.pages.length;
    await doc.dispose();
    return PdfRenderer.fromBytes(manifest.id, bytes, pageCount: count);
  }

  /// Build a fixed-layout anchor from a selection on [page] (1-based). [rects]
  /// are in page-point space; [quoteText] is null for scanned PDFs.
  Anchor buildAnchor({
    required int page,
    required double pageWidth,
    required double pageHeight,
    required List<RectD> rects,
    String? quoteText,
  }) => PdfAnchorFactory.fromSelection(
    sectionId: 'page:$page',
    page: page,
    pageWidth: pageWidth,
    pageHeight: pageHeight,
    rects: rects,
    quote: quoteText == null ? null : TextQuoteSelector(exact: quoteText),
  );

  // --- ContentRenderer (the text-centric members are unused for fixed PDF) ---

  @override
  Future<void> load(BookManifest manifest, ContentProvider content) async {
    // Already loaded via [open]; provided for interface completeness.
  }

  @override
  Widget buildViewport(ViewportConfig config) => const SizedBox.shrink();

  @override
  Future<List<Rect>> rectsForAnchor(Anchor anchor) async => const [];

  @override
  Future<Anchor?> anchorForSelection(Selection selection) async => null;

  @override
  Future<Anchor?> anchorForPoint(Offset point) async => null;

  @override
  Future<void> goTo(Locator locator) async {}

  @override
  Locator get currentLocation => const Locator(sectionId: 'page:1');

  @override
  Stream<double> get progress => Stream<double>.empty();

  @override
  Future<List<SearchHit>> search(String query) async => const [];

  @override
  SectionContent sectionContent(String sectionId) =>
      SectionContent(sectionId: sectionId, text: '');
}
