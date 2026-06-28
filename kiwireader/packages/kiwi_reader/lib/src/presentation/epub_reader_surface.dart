import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_epub_viewer/flutter_epub_viewer.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/reader_config.dart';
import '../rendering/epub_renderer.dart';
import 'note_editor.dart';
import 'selection_toolbar.dart';

/// A captured EPUB selection: the epub.js CFI + the selected text.
class EpubSelectionDraft {
  final String cfi;
  final String text;
  const EpubSelectionDraft(this.cfi, this.text);
}

/// Integration seam for EPUB selection — `flutter_epub_viewer`'s `onTextSelected`
/// calls [set]; the surface then shows the toolbar and builds the anchor.
class EpubSelectionController extends ChangeNotifier {
  EpubSelectionDraft? _draft;
  EpubSelectionDraft? get draft => _draft;

  void set(EpubSelectionDraft? draft) {
    _draft = draft;
    notifyListeners();
  }

  void clear() => set(null);
}

/// Renders an EPUB via `flutter_epub_viewer` (epub.js). Existing highlights are
/// re-applied by CFI through the epub controller; new selections flow through
/// the toolbar into [onCreateHighlight] / [onCreateNote].
///
/// NOTE: WebView + epub.js → validated on a device. The selection wiring uses
/// the `flutter_epub_viewer` API as published; confirm callback shapes on the
/// pinned version.
class EpubReaderSurface extends StatefulWidget {
  final EpubRenderer renderer;
  final List<Annotation> annotations;
  final ReaderConfig config;
  final EpubSelectionController selection;
  final void Function(Anchor anchor, String colorToken) onCreateHighlight;
  final void Function(Anchor anchor, String text) onCreateNote;

  const EpubReaderSurface({
    super.key,
    required this.renderer,
    required this.annotations,
    required this.config,
    required this.selection,
    required this.onCreateHighlight,
    required this.onCreateNote,
  });

  @override
  State<EpubReaderSurface> createState() => _EpubReaderSurfaceState();
}

class _EpubReaderSurfaceState extends State<EpubReaderSurface> {
  final EpubController _controller = EpubController();
  File? _epubFile;
  late EpubFlow _flow;          // page-flip vs continuous scroll
  late int _fontPx;             // reader body font size, in px
  Offset? _touchUp;             // normalized (0..1) point a selection ended at
  bool _loaded = false;         // book finished loading in the viewer
  Offset? _downPt;              // where the current touch started (normalized)
  int _downMs = 0;              // when it started (for tap vs hold)
  bool _showHint = false;       // one-time "tap edges to turn" hint
  // Progress drives ONLY the thin bottom bar via a ValueListenableBuilder, so a
  // page turn / scroll never calls setState (which would rebuild the WebView and
  // cause flicker + scroll jank).
  final ValueNotifier<double> _progress = ValueNotifier<double>(0);
  // The EpubViewer is expensive (a WebView). Build it exactly ONCE and reuse the
  // same instance across rebuilds — font/layout changes go through the
  // controller, never by re-creating the viewer.
  Widget? _viewer;
  late EpubFlow _bakedFlow;     // flow/font currently live in the viewer
  late int _bakedFont;
  double _resumeTo = 0;         // progress (0..1) to seek to once locations load
  bool _located = false;        // epub.js locations are ready (safe to seek)
  int _lastPosSaveMs = 0;       // throttle position writes

  static const _kPrefFont = 'kiwi_reader.fontPx';
  static const _kPrefFlow = 'kiwi_reader.flow';
  String get _posKey => 'kiwi_reader.pos.${widget.renderer.bookId}';

  @override
  void initState() {
    super.initState();
    _flow = widget.config.readingMode == ReadingMode.scroll
        ? EpubFlow.scrolled
        : EpubFlow.paginated;
    _fontPx = (18 * widget.config.fontScale).round().clamp(12, 40);
    _bakedFlow = _flow;
    _bakedFont = _fontPx;
    // flutter_epub_viewer 1.2.x loads from a url / file / asset (there is no
    // in-memory bytes constructor), so stage the EPUB bytes to a temp file once
    // and point the viewer at it.
    final dir = Directory.systemTemp.createTempSync('kiwi_epub_');
    _epubFile = File('${dir.path}/book.epub')
      ..writeAsBytesSync(widget.renderer.bytes);
    widget.selection.addListener(_onSelectionChanged);
    _restore(); // load saved font + layout (applied once the book loads)
  }

  // ---- persistence: remember the reader's font + layout across books/sessions
  Future<void> _restore() async {
    try {
      final p = await SharedPreferences.getInstance();
      final px = p.getInt(_kPrefFont);
      final flow = p.getString(_kPrefFlow);
      final pos = p.getDouble(_posKey);
      if (!mounted) return;
      if (px != null) _fontPx = px.clamp(12, 40);
      if (pos != null && pos > 0.001) _resumeTo = pos;
      final restored = flow == 'scrolled'
          ? EpubFlow.scrolled
          : flow == 'paginated'
              ? EpubFlow.paginated
              : _flow;
      if (restored != _flow) {
        // saved layout differs → (re)build the viewer in that layout
        _flow = restored;
        _bakedFlow = restored;
        _located = false;
        _viewer = null;
      }
      setState(() {});
      if (_loaded) {
        _applySettings();
        _tryResume();
      }
    } catch (_) {/* prefs are best-effort */}
  }

  Future<void> _save() async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.setInt(_kPrefFont, _fontPx);
      await p.setString(
          _kPrefFlow, _flow == EpubFlow.scrolled ? 'scrolled' : 'paginated');
    } catch (_) {/* best-effort */}
  }

  // ---- resume-where-you-left-off (per book) --------------------------------
  Future<void> _savePosition() async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.setDouble(_posKey, _progress.value);
    } catch (_) {/* best-effort */}
  }

  void _savePositionThrottled() {
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _lastPosSaveMs < 2500) return; // don't hammer disk while reading
    _lastPosSaveMs = now;
    _savePosition();
  }

  // Seek to the saved spot once epub.js locations are ready. Runs on whichever
  // lands last — the location-load callback or the async prefs restore.
  void _tryResume() {
    if (_located && _resumeTo > 0.001) {
      _controller.toProgressPercentage(_resumeTo);
      _resumeTo = 0;
    }
  }

  // Push the current font + layout into the live viewer, but ONLY when they
  // actually differ from what the viewer is already showing — re-applying the
  // same values triggers a needless epub.js reflow (a visible flicker).
  void _applySettings() {
    if (_flow != _bakedFlow) {
      _controller.setFlow(flow: _flow);
      _bakedFlow = _flow;
    }
    if (_fontPx != _bakedFont) {
      _controller.setFontSize(fontSize: _fontPx.toDouble());
      _bakedFont = _fontPx;
    }
  }

  // ---- Kindle-style tap navigation -----------------------------------------
  // We don't put a Flutter gesture layer over the WebView (that would swallow
  // text selection). Instead we use the viewer's own touch callbacks: a quick,
  // still tap in the left third turns back, the right third turns forward, and
  // the centre is left for reading. Page turns are driven programmatically via
  // controller.next()/prev() — the deterministic way readers do it.
  void _handleTouchUp(double x, double y) {
    final start = _downPt;
    final heldMs = DateTime.now().millisecondsSinceEpoch - _downMs;
    _downPt = null;
    if (start == null) return;
    final moved = (Offset(x, y) - start).distance;
    final isTap = moved < 0.04 && heldMs < 350; // not a swipe or long-press
    if (!isTap || widget.selection.draft != null) return;
    if (_flow != EpubFlow.paginated) return; // scroll mode: you scroll, not tap
    if (x < 0.33) {
      _controller.prev();
    } else if (x > 0.67) {
      _controller.next();
    }
  }

  Future<void> _maybeShowTapHint() async {
    try {
      final p = await SharedPreferences.getInstance();
      if (p.getBool('kiwi_reader.tapHint') == true) return;
      await p.setBool('kiwi_reader.tapHint', true);
      if (!mounted || _flow != EpubFlow.paginated) return;
      setState(() => _showHint = true);
      Future.delayed(const Duration(milliseconds: 3200), () {
        if (mounted) setState(() => _showHint = false);
      });
    } catch (_) {/* hint is optional */}
  }

  @override
  void dispose() {
    widget.selection.removeListener(_onSelectionChanged);
    _savePosition(); // remember the page on the way out (back to Library)
    _progress.dispose();
    try {
      _epubFile?.parent.deleteSync(recursive: true);
    } catch (_) {/* best-effort temp cleanup */}
    super.dispose();
  }

  void _onSelectionChanged() => setState(() {});

  void _applyExistingHighlights() {
    for (final a in widget.annotations) {
      if (a.isDeleted || a.type == AnnotationType.bookmark) continue;
      final cfi = EpubRenderer.cfiOf(a.anchor);
      if (cfi == null) continue;
      final color = _colorFor(a.color);
      _controller.addHighlight(cfi: cfi, color: color);
    }
  }

  Color _colorFor(String? token) {
    for (final c in widget.config.palette) {
      if (c.token == token) return c.color;
    }
    return widget.config.palette.isNotEmpty
        ? widget.config.palette.first.color
        : const Color(0xFFFDE68A);
  }

  Anchor _anchor(EpubSelectionDraft d) =>
      widget.renderer.buildAnchor(cfi: d.cfi, selectedText: d.text);

  void _highlight(String token) {
    final d = widget.selection.draft;
    if (d == null) return;
    widget.onCreateHighlight(_anchor(d), token);
    widget.selection.clear();
  }

  Future<void> _note() async {
    final d = widget.selection.draft;
    if (d == null) return;
    final text = await showNoteEditor(context, quote: d.text);
    if (text == null || text.isEmpty) return;
    widget.onCreateNote(_anchor(d), text);
    widget.selection.clear();
  }

  // ---- reading settings (font size + page layout), live via the controller --
  void _applyFont(int px) {
    _fontPx = px.clamp(12, 40);
    _controller.setFontSize(fontSize: _fontPx.toDouble()); // API wants a double
    _bakedFont = _fontPx;
    _save();
  }

  // Switching paged↔scrolled at RUNTIME (setFlow) does not reliably re-paginate
  // in flutter_epub_viewer — but a FRESH load in either layout does (that's why
  // it worked on first open). So a layout change re-creates the viewer in the new
  // mode, and we seek back to where the reader was.
  void _applyFlow(EpubFlow flow) {
    if (flow == _flow) return;
    _resumeTo = _progress.value; // keep the reader's place across the reload
    _located = false;
    _flow = flow;
    _bakedFlow = flow;
    _viewer = null; // force a rebuild of the EpubViewer in the new layout
    setState(() {});
    _save();
  }

  void _openReadingSettings() {
    final cs = Theme.of(context).colorScheme;
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetCtx) => SafeArea(
        child: StatefulBuilder(
          builder: (sheetCtx, setSheet) {
            void font(int delta) {
              _applyFont(_fontPx + delta);
              setSheet(() {});
            }

            Widget modeChip(String label, IconData icon, EpubFlow flow) {
              final sel = _flow == flow;
              return Expanded(
                child: InkWell(
                  onTap: () {
                    _applyFlow(flow);
                    setSheet(() {});
                  },
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: BoxDecoration(
                      color: sel ? cs.primary.withValues(alpha: 0.12) : null,
                      border: Border.all(
                          color: sel ? cs.primary : cs.outlineVariant,
                          width: sel ? 2 : 1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      children: [
                        Icon(icon, color: sel ? cs.primary : null),
                        const SizedBox(height: 4),
                        Text(label,
                            style: TextStyle(
                                fontWeight: FontWeight.w600,
                                color: sel ? cs.primary : null)),
                      ],
                    ),
                  ),
                ),
              );
            }

            return Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Reading settings',
                      style:
                          TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      const Text('Font size',
                          style: TextStyle(fontWeight: FontWeight.w600)),
                      const Spacer(),
                      IconButton(
                        onPressed: _fontPx > 12 ? () => font(-2) : null,
                        icon: const Icon(Icons.text_decrease),
                      ),
                      SizedBox(
                          width: 56,
                          child: Text('$_fontPx',
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w700))),
                      IconButton(
                        onPressed: _fontPx < 40 ? () => font(2) : null,
                        icon: const Icon(Icons.text_increase),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  const Text('Page layout',
                      style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      modeChip('Pages', Icons.menu_book_outlined,
                          EpubFlow.paginated),
                      const SizedBox(width: 10),
                      modeChip('Scroll', Icons.swap_vert, EpubFlow.scrolled),
                    ],
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  // Built once (a WebView is expensive); reused on every rebuild so a setState
  // for the toolbar/hint never re-creates it. Font/layout go via the controller.
  Widget _buildViewer() => EpubViewer(
        // The key is tied to the layout: changing it forces a clean re-init of
        // epub.js in the new mode (runtime setFlow is unreliable).
        key: ValueKey('epub-${_flow.name}'),
        epubSource: EpubSource.fromFile(_epubFile!),
        epubController: _controller,
        // NOTE: flutter_epub_viewer 1.2.8 exposes only one EpubManager
        // (continuous), so we leave `manager` default — `flow` alone selects
        // paged vs scrolled. Reliable page turns come from the tap-zones driving
        // controller.next()/prev().
        displaySettings: EpubDisplaySettings(
          flow: _flow,
          snap: _flow == EpubFlow.paginated,
          useSnapAnimationAndroid: false,
          fontSize: _fontPx,
          theme: EpubTheme.light(),
          allowScriptedContent: true,
        ),
        onChaptersLoaded: (_) => _applyExistingHighlights(),
        onEpubLoaded: () {
          _loaded = true;
          _applySettings(); // apply restored font/layout on the live book
          _maybeShowTapHint();
        },
        onLocationLoaded: () {
          _located = true;
          _tryResume(); // seek back to the saved page once locations are ready
        },
        // Update the progress notifier only — NO setState, so a page turn or
        // scroll never rebuilds the WebView (that was the flicker + scroll jank).
        onRelocated: (loc) {
          _progress.value = loc.progress;
          _savePositionThrottled();
        },
        onTextSelected: (selection) {
          widget.selection.set(
            EpubSelectionDraft(selection.selectionCfi, selection.selectedText),
          );
        },
        onTouchDown: (x, y) {
          _downPt = Offset(x, y);
          _downMs = DateTime.now().millisecondsSinceEpoch;
        },
        onTouchUp: (x, y) {
          _touchUp = Offset(x, y);
          _handleTouchUp(x, y); // Kindle tap-zones: left=back, right=next
        },
        onDeselection: () {
          _touchUp = null;
          widget.selection.clear();
        },
      );

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final draft = widget.selection.draft;
    _viewer ??= _buildViewer(); // build the WebView exactly once
    return LayoutBuilder(
      builder: (context, constraints) {
        return Stack(
          // Tight, full-size constraints for the WebView — epub.js needs a
          // fixed height to lay out into pages, or paging silently fails.
          fit: StackFit.expand,
          children: [
            _viewer!,
            // reading-settings affordance (font size + page layout)
            Positioned(
              top: 8,
              right: 8,
              child: Material(
                color: cs.surface.withValues(alpha: 0.92),
                shape: const CircleBorder(),
                elevation: 2,
                child: IconButton(
                  tooltip: 'Reading settings',
                  icon: Icon(Icons.text_fields, color: cs.primary),
                  onPressed: _openReadingSettings,
                ),
              ),
            ),
            // thin reading-progress bar — repaints itself only, via the notifier
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: ValueListenableBuilder<double>(
                valueListenable: _progress,
                builder: (_, v, __) => LinearProgressIndicator(
                  value: v.clamp(0.0, 1.0).toDouble(),
                  minHeight: 2.5,
                  backgroundColor: Colors.black.withValues(alpha: 0.06),
                  valueColor: AlwaysStoppedAnimation<Color>(cs.primary),
                ),
              ),
            ),
            if (_showHint) _tapHintOverlay(cs),
            if (draft != null) _toolbar(constraints),
          ],
        );
      },
    );
  }

  // One-time, non-blocking hint that teaches the tap-zones (auto-dismisses).
  Widget _tapHintOverlay(ColorScheme cs) {
    Widget side(IconData icon, String label) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: Colors.white, size: 40),
              const SizedBox(height: 6),
              Text(label,
                  style: const TextStyle(
                      color: Colors.white, fontWeight: FontWeight.w700)),
            ],
          ),
        );
    return Positioned.fill(
      child: IgnorePointer(
        child: Container(
          color: Colors.black.withValues(alpha: 0.42),
          child: Row(
            children: [
              Expanded(child: side(Icons.chevron_left, 'Tap: back')),
              const Expanded(child: SizedBox()),
              Expanded(child: side(Icons.chevron_right, 'Tap: next')),
            ],
          ),
        ),
      ),
    );
  }

  // Anchor the selection toolbar near where the selection ended, not the
  // bottom of the screen. Falls back to bottom-centre if we have no point yet.
  Widget _toolbar(BoxConstraints c) {
    final tb = SelectionToolbar(
      palette: widget.config.palette,
      onColor: (col) => _highlight(col.token),
      onNote: _note,
    );
    final t = _touchUp;
    if (t == null) {
      return Positioned(
          left: 0, right: 0, bottom: 28, child: Center(child: tb));
    }
    const tbW = 250.0, tbH = 56.0;
    final cx = (t.dx * c.maxWidth).clamp(tbW / 2, c.maxWidth - tbW / 2);
    final top =
        (t.dy * c.maxHeight - tbH - 14).clamp(8.0, c.maxHeight - tbH - 8);
    return Positioned(
      left: cx - tbW / 2,
      top: top,
      width: tbW,
      child: Center(child: tb),
    );
  }
}
