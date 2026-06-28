import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../config/reader_config.dart';
import '../events/reader_event.dart';
import '../rendering/content_renderer.dart';
import '../rendering/epub_renderer.dart';
import '../rendering/html_renderer.dart';
import '../rendering/pdf_renderer.dart';
import '../state/reader_providers.dart';
import 'annotations_list.dart';
import 'epub_reader_surface.dart';
import 'html_reader_surface.dart';
import 'note_editor.dart';
import 'pdf_reader_surface.dart';
import 'selection_toolbar.dart';

/// The single public widget the host embeds in the Read tab. Picks the right
/// surface for the bound renderer (HTML or PDF) — the format-agnostic seam in
/// action. Highlights, notes, the annotations list, live sync status and
/// auto-sync are shared across formats.
class KiwiReader extends ConsumerStatefulWidget {
  final String bookId;
  final ReaderConfig config;
  final void Function(ReaderEvent event)? onEvent;

  const KiwiReader({
    super.key,
    required this.bookId,
    this.config = const ReaderConfig(),
    this.onEvent,
  });

  @override
  ConsumerState<KiwiReader> createState() => _KiwiReaderState();
}

class _KiwiReaderState extends ConsumerState<KiwiReader> {
  LiveSelection? _live;
  late final ContentRenderer _content = ref.read(contentRendererProvider);
  late final Map<String, GlobalKey> _sectionKeys = {
    if (_html != null)
      for (final s in _html!.sections) s.id: GlobalKey(),
  };
  late final SyncScheduler _scheduler = SyncScheduler(
    engine: ref.read(syncEngineProvider),
    connectivity: ref.read(connectivityProvider),
  );
  SyncStatus _syncStatus = SyncStatus.idle;
  StreamSubscription<SyncStatus>? _statusSub;
  final PdfSelectionController _pdfSelection = PdfSelectionController();
  final EpubSelectionController _epubSelection = EpubSelectionController();

  HtmlRenderer? get _html =>
      _content is HtmlRenderer ? _content as HtmlRenderer : null;
  PdfRenderer? get _pdf =>
      _content is PdfRenderer ? _content as PdfRenderer : null;
  EpubRenderer? get _epub =>
      _content is EpubRenderer ? _content as EpubRenderer : null;

  @override
  void initState() {
    super.initState();
    _statusSub = _scheduler.status.listen((s) {
      if (mounted) setState(() => _syncStatus = s);
    });
    _scheduler.start();
    _scheduler.requestSync();
  }

  @override
  void dispose() {
    _statusSub?.cancel();
    _scheduler.dispose();
    _pdfSelection.dispose();
    _epubSelection.dispose();
    super.dispose();
  }

  void _touch() {
    ref.invalidate(annotationsProvider(widget.bookId));
    _scheduler.requestSync();
  }

  String get _title => _html?.book.title ?? widget.bookId;

  @override
  Widget build(BuildContext context) {
    final annotationsAsync = ref.watch(annotationsProvider(widget.bookId));
    return Scaffold(
      appBar: AppBar(
        title: Text(_title),
        actions: [
          IconButton(
            tooltip: 'Sync (${_syncStatus.name})',
            icon: Icon(_syncIcon()),
            onPressed: _sync,
          ),
          IconButton(
            tooltip: 'My annotations',
            icon: const Icon(Icons.list_alt),
            onPressed: _openList,
          ),
        ],
      ),
      // SafeArea keeps the page bottom clear of the Android system nav bar.
      body: SafeArea(
        child: annotationsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Reader error: $e')),
          data: _buildBody,
        ),
      ),
    );
  }

  Widget _buildBody(List<Annotation> annotations) {
    final html = _html;
    if (html != null) {
      return Stack(
        children: [
          HtmlReaderSurface(
            renderer: html,
            annotations: annotations,
            config: widget.config,
            live: _live,
            onDraft: (s) => setState(() => _live = s),
            onTapAnnotation: _showActions,
            sectionKeys: _sectionKeys,
            bookmarkedSections: _bookmarkedSections(annotations),
            onToggleBookmark: _toggleBookmark,
          ),
          if (_live != null)
            Positioned(
              left: 0,
              right: 0,
              bottom: 28,
              child: Center(
                child: SelectionToolbar(
                  palette: widget.config.palette,
                  onColor: (c) => _createHighlight(c.token),
                  onNote: _createNoteFromSelection,
                ),
              ),
            ),
        ],
      );
    }
    final pdf = _pdf;
    if (pdf != null) {
      return PdfReaderSurface(
        renderer: pdf,
        annotations: annotations,
        config: widget.config,
        selection: _pdfSelection,
        onCreateHighlight: (anchor, token) =>
            _createPdf(anchor, token: token),
        onCreateNote: (anchor, text) => _createPdf(anchor, noteText: text),
      );
    }
    final epub = _epub;
    if (epub != null) {
      return EpubReaderSurface(
        renderer: epub,
        annotations: annotations,
        config: widget.config,
        selection: _epubSelection,
        onCreateHighlight: (anchor, token) =>
            _createPdf(anchor, token: token),
        onCreateNote: (anchor, text) => _createPdf(anchor, noteText: text),
      );
    }
    return const Center(child: Text('No renderer bound for this book.'));
  }

  IconData _syncIcon() => switch (_syncStatus) {
    SyncStatus.syncing => Icons.sync,
    SyncStatus.offline => Icons.cloud_off_outlined,
    SyncStatus.error => Icons.sync_problem,
    SyncStatus.backoff => Icons.sync_problem,
    SyncStatus.idle => Icons.cloud_done_outlined,
  };

  Future<void> _openList() async {
    final selected = await Navigator.of(context).push<Annotation>(
      MaterialPageRoute(
        builder: (_) => AnnotationsListScreen(bookId: widget.bookId),
      ),
    );
    if (selected != null) await _jumpTo(selected.anchor.sectionId);
  }

  Future<void> _sync() async {
    final messenger = ScaffoldMessenger.of(context);
    final outcome = await _scheduler.sync();
    if (!mounted) return;
    if (outcome == null) {
      messenger.showSnackBar(
        const SnackBar(content: Text('Sync skipped (offline or busy)')),
      );
    } else {
      ref.invalidate(annotationsProvider(widget.bookId));
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            'Synced — pushed ${outcome.pushed}, pulled ${outcome.pulled}',
          ),
        ),
      );
    }
  }

  Future<void> _jumpTo(String sectionId) async {
    final ctx = _sectionKeys[sectionId]?.currentContext;
    if (ctx != null) {
      await Scrollable.ensureVisible(
        ctx,
        duration: const Duration(milliseconds: 300),
        alignment: 0.1,
      );
    }
  }

  // --- HTML-specific create flow -------------------------------------------

  Future<Anchor?> _anchorFromLive() async {
    final live = _live;
    final html = _html;
    if (live == null || html == null) return null;
    return html.anchorForSelection(
      Selection(
        sectionId: live.sectionId,
        start: live.start,
        end: live.end,
        text: live.text,
      ),
    );
  }

  Future<void> _createHighlight(String color) async {
    final anchor = await _anchorFromLive();
    if (anchor == null) return;
    final a = await ref
        .read(annotationControllerProvider(widget.bookId))
        .createHighlight(anchor: anchor, color: color);
    widget.onEvent?.call(
      AnnotationCreated(a.id, AnnotationType.highlight, color: color),
    );
    _refreshAndClear();
  }

  Future<void> _createNoteFromSelection() async {
    final live = _live;
    final anchor = await _anchorFromLive();
    if (anchor == null || live == null || !mounted) return;
    final text = await showNoteEditor(context, quote: live.text);
    if (text == null || text.isEmpty) return;
    final a = await ref
        .read(annotationControllerProvider(widget.bookId))
        .addNote(anchor: anchor, text: text);
    widget.onEvent?.call(AnnotationCreated(a.id, AnnotationType.note));
    _refreshAndClear();
  }

  void _refreshAndClear() {
    _touch();
    if (mounted) setState(() => _live = null);
  }

  Set<String> _bookmarkedSections(List<Annotation> annotations) => {
    for (final a in annotations)
      if (!a.isDeleted && a.type == AnnotationType.bookmark) a.anchor.sectionId,
  };

  Future<void> _toggleBookmark(String sectionId) async {
    await ref
        .read(annotationControllerProvider(widget.bookId))
        .toggleBookmark(sectionId: sectionId);
    _touch();
  }

  Future<void> _createPdf(
    Anchor anchor, {
    String? token,
    String? noteText,
  }) async {
    final controller = ref.read(annotationControllerProvider(widget.bookId));
    if (noteText != null) {
      final a = await controller.addNote(anchor: anchor, text: noteText);
      widget.onEvent?.call(AnnotationCreated(a.id, AnnotationType.note));
    } else {
      final a = await controller.createHighlight(
        anchor: anchor,
        color: token ?? 'yellow',
      );
      widget.onEvent?.call(
        AnnotationCreated(a.id, AnnotationType.highlight, color: token),
      );
    }
    _touch();
  }

  void _showActions(Annotation a) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetCtx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
              child: Row(
                children: [
                  const Text(
                    'Color',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(width: 12),
                  for (final c in widget.config.palette)
                    Padding(
                      padding: const EdgeInsets.all(4),
                      child: GestureDetector(
                        onTap: () async {
                          Navigator.pop(sheetCtx);
                          await ref
                              .read(annotationControllerProvider(widget.bookId))
                              .recolor(a, c.token);
                          _touch();
                        },
                        child: CircleAvatar(
                          backgroundColor: c.color,
                          radius: 13,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            ListTile(
              leading: const Icon(Icons.note_alt_outlined),
              title: Text(
                (a.noteText?.isEmpty ?? true) ? 'Add note' : 'Edit note',
              ),
              onTap: () async {
                Navigator.pop(sheetCtx);
                if (!mounted) return;
                final text = await showNoteEditor(
                  context,
                  initial: a.noteText,
                  quote: a.anchor.quote?.exact,
                );
                if (text == null) return;
                await ref
                    .read(annotationControllerProvider(widget.bookId))
                    .editNote(a, text);
                _touch();
              },
            ),
            ListTile(
              leading: const Icon(
                Icons.delete_outline,
                color: Color(0xFFDC2626),
              ),
              title: const Text('Delete'),
              onTap: () async {
                Navigator.pop(sheetCtx);
                await ref
                    .read(annotationControllerProvider(widget.bookId))
                    .delete(a);
                widget.onEvent?.call(AnnotationDeleted(a.id));
                _touch();
              },
            ),
          ],
        ),
      ),
    );
  }
}
