import 'dart:convert';

import 'package:flutter/widgets.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../content/html_content.dart';
import '../host/providers.dart';
import 'content_renderer.dart';

/// Renders custom HTML/JSON content (Phase-0 source format) and turns user
/// selections into layered anchors via the core's [AnchorFactory] (KR-011/020).
///
/// The on-screen geometry (which glyph boxes a highlight covers) is computed by
/// the reader surface that owns the laid-out `TextPainter`s; this class is the
/// data + anchoring seam.
class HtmlRenderer implements ContentRenderer {
  HtmlBook? _book;
  String? _currentSectionId;

  HtmlRenderer();

  HtmlRenderer.fromBook(HtmlBook book) : _book = book {
    _currentSectionId = book.sections.isNotEmpty
        ? book.sections.first.id
        : null;
  }

  HtmlBook get book => _book ?? (throw StateError('HtmlRenderer not loaded'));
  List<HtmlSection> get sections => book.sections;

  HtmlSection _section(String id) => book.sections.firstWhere(
    (s) => s.id == id,
    orElse: () => throw ArgumentError('No section "$id"'),
  );

  @override
  Future<void> load(BookManifest manifest, ContentProvider content) async {
    final stream = await content.bytes(manifest.id);
    final bytes = <int>[];
    await for (final chunk in stream) {
      bytes.addAll(chunk);
    }
    _book = HtmlBook.decode(utf8.decode(bytes));
    _currentSectionId = _book!.sections.isNotEmpty
        ? _book!.sections.first.id
        : null;
  }

  @override
  SectionContent sectionContent(String sectionId) => SectionContent(
    sectionId: sectionId,
    text: buildSectionView(_section(sectionId)).canonical,
  );

  @override
  Future<Anchor?> anchorForSelection(Selection selection) async =>
      AnchorFactory.fromSelection(
        content: sectionContent(selection.sectionId),
        start: selection.start,
        end: selection.end,
        structural: StructuralSelector(LocatorType.domRange, {
          'sectionId': selection.sectionId,
          'start': selection.start,
          'end': selection.end,
        }),
      );

  @override
  Future<Anchor?> anchorForPoint(Offset point) async => null; // sticky notes: KR-030

  @override
  Future<List<Rect>> rectsForAnchor(Anchor anchor) async => const [];

  @override
  Widget buildViewport(ViewportConfig config) => const SizedBox.shrink();

  @override
  Future<void> goTo(Locator locator) async =>
      _currentSectionId = locator.sectionId;

  @override
  Locator get currentLocation => Locator(sectionId: _currentSectionId ?? '');

  @override
  Stream<double> get progress => Stream<double>.empty();

  @override
  Future<List<SearchHit>> search(String query) async {
    final q = query.trim().toLowerCase();
    if (q.isEmpty) return const [];
    final hits = <SearchHit>[];
    for (final s in book.sections) {
      final canon = buildSectionCanonical(s).text;
      final idx = canon.toLowerCase().indexOf(q);
      if (idx != -1) {
        final from = idx - 20 < 0 ? 0 : idx - 20;
        final to = idx + q.length + 20 > canon.length
            ? canon.length
            : idx + q.length + 20;
        hits.add(
          SearchHit(
            Locator(sectionId: s.id, raw: {'offset': idx}),
            canon.substring(from, to),
          ),
        );
      }
    }
    return hits;
  }
}
