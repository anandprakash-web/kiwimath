import 'package:flutter/material.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:pdfrx/pdfrx.dart';

import '../config/reader_config.dart';
import '../rendering/pdf_renderer.dart';
import 'note_editor.dart';
import 'selection_toolbar.dart';

/// A captured PDF selection: which page, the page size (points) and the
/// selected rectangles (in page-point space) + optional text.
class PdfSelectionDraft {
  final int page;
  final double pageWidth;
  final double pageHeight;
  final List<RectD> rects;
  final String? text;
  const PdfSelectionDraft({
    required this.page,
    required this.pageWidth,
    required this.pageHeight,
    required this.rects,
    this.text,
  });
}

/// The integration seam for PDF selection. On a device, pdfrx's text-selection
/// listener calls [set] with the page + rects + text; the surface then shows
/// the toolbar and builds the anchor via the tested geometry. This keeps the
/// (version-specific) pdfrx selection wiring in ONE documented place.
class PdfSelectionController extends ChangeNotifier {
  PdfSelectionDraft? _draft;
  PdfSelectionDraft? get draft => _draft;

  void set(PdfSelectionDraft? draft) {
    _draft = draft;
    notifyListeners();
  }

  void clear() => set(null);
}

/// Renders a PDF with `pdfrx`, paints resolved highlight quads via the per-page
/// paint callback (tested geometry), and — when a [PdfSelectionController] has a
/// draft — shows the selection toolbar to create a highlight/note.
class PdfReaderSurface extends StatefulWidget {
  final PdfRenderer renderer;
  final List<Annotation> annotations;
  final ReaderConfig config;
  final PdfSelectionController selection;
  final void Function(Anchor anchor, String colorToken) onCreateHighlight;
  final void Function(Anchor anchor, String text) onCreateNote;

  const PdfReaderSurface({
    super.key,
    required this.renderer,
    required this.annotations,
    required this.config,
    required this.selection,
    required this.onCreateHighlight,
    required this.onCreateNote,
  });

  @override
  State<PdfReaderSurface> createState() => _PdfReaderSurfaceState();
}

class _PdfReaderSurfaceState extends State<PdfReaderSurface> {
  @override
  void initState() {
    super.initState();
    widget.selection.addListener(_onSelectionChanged);
  }

  @override
  void dispose() {
    widget.selection.removeListener(_onSelectionChanged);
    super.dispose();
  }

  void _onSelectionChanged() => setState(() {});

  Color _colorFor(String? token) {
    for (final c in widget.config.palette) {
      if (c.token == token) return c.color;
    }
    return widget.config.palette.isNotEmpty
        ? widget.config.palette.first.color
        : const Color(0xFFFDE68A);
  }

  void _paintHighlights(Canvas canvas, Rect pageRect, PdfPage page) {
    for (final a in widget.annotations) {
      if (a.isDeleted || a.type == AnnotationType.bookmark) continue;
      final region = PdfAnchorFactory.regionOf(a.anchor);
      if (region == null || region.page != page.pageNumber) continue;
      final paint = Paint()
        ..color = _colorFor(
          a.color,
        ).withOpacity(a.type == AnnotationType.note ? 0.30 : 0.40);
      for (final r in PdfAnchorFactory.rectsForPage(
        a.anchor,
        width: pageRect.width,
        height: pageRect.height,
      )) {
        final rect = Rect.fromLTRB(
          pageRect.left + r.left,
          pageRect.top + r.top,
          pageRect.left + r.right,
          pageRect.top + r.bottom,
        );
        canvas.drawRRect(RRect.fromRectXY(rect, 2, 2), paint);
      }
    }
  }

  Anchor _anchorFromDraft(PdfSelectionDraft d) => widget.renderer.buildAnchor(
    page: d.page,
    pageWidth: d.pageWidth,
    pageHeight: d.pageHeight,
    rects: d.rects,
    quoteText: d.text,
  );

  Future<void> _highlight(String token) async {
    final d = widget.selection.draft;
    if (d == null) return;
    widget.onCreateHighlight(_anchorFromDraft(d), token);
    widget.selection.clear();
  }

  Future<void> _note() async {
    final d = widget.selection.draft;
    if (d == null) return;
    final text = await showNoteEditor(context, quote: d.text);
    if (text == null || text.isEmpty) return;
    widget.onCreateNote(_anchorFromDraft(d), text);
    widget.selection.clear();
  }

  @override
  Widget build(BuildContext context) {
    final draft = widget.selection.draft;
    return Stack(
      children: [
        // TODO(KR-012-sel): on device, wire pdfrx text selection to
        // `widget.selection.set(PdfSelectionDraft(page, pageWidth, pageHeight,
        // rects, text))`. The create pipeline below is complete.
        PdfViewer.data(
          widget.renderer.bytes,
          sourceName: widget.renderer.bookId,
          params: PdfViewerParams(
            enableTextSelection: true,
            pagePaintCallbacks: [_paintHighlights],
          ),
        ),
        if (draft != null)
          Positioned(
            left: 0,
            right: 0,
            bottom: 28,
            child: Center(
              child: SelectionToolbar(
                palette: widget.config.palette,
                onColor: (c) => _highlight(c.token),
                onNote: _note,
              ),
            ),
          ),
      ],
    );
  }
}
