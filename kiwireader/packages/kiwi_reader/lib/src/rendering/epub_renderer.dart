import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../host/providers.dart';
import 'content_renderer.dart';

/// Reflowable EPUB renderer. Rendering, text selection and on-page highlight
/// drawing are delegated to epub.js (via `flutter_epub_viewer`'s WebView), so
/// this adapter is thin: it owns the bytes and builds anchors that combine the
/// epub.js **CFI** (structural locator) with the selected text (quote). If the
/// CFI ever fails to resolve after a re-flow/re-export, the tested
/// [AnchorResolver] falls back to the quote — same resilience as HTML.
///
/// NOTE: epub.js runs in a WebView, so this path is validated on a device.
class EpubRenderer implements ContentRenderer {
  final String bookId;
  final Uint8List bytes;

  EpubRenderer.fromBytes(this.bookId, this.bytes);

  static Future<EpubRenderer> open(
    BookManifest manifest,
    ContentProvider content,
  ) async {
    final stream = await content.bytes(manifest.id);
    final buffer = <int>[];
    await for (final chunk in stream) {
      buffer.addAll(chunk);
    }
    return EpubRenderer.fromBytes(manifest.id, Uint8List.fromList(buffer));
  }

  /// Build an EPUB anchor: CFI as the structural locator + selected text as the
  /// quote. [sectionId] is the spine item href when known.
  Anchor buildAnchor({
    required String cfi,
    required String selectedText,
    String sectionId = 'epub',
  }) => Anchor(
    sectionId: sectionId,
    structural: StructuralSelector(LocatorType.cfi, {'cfi': cfi}),
    quote: TextQuoteSelector(exact: selectedText),
    state: AnchorState.resolved,
  );

  /// Reads the CFI from an EPUB anchor (used to re-apply highlights via epub.js).
  static String? cfiOf(Anchor anchor) {
    final s = anchor.structural;
    if (s == null || s.type != LocatorType.cfi) return null;
    return s.data['cfi'] as String?;
  }

  // --- ContentRenderer (epub.js owns text + rendering) ---

  @override
  Future<void> load(BookManifest manifest, ContentProvider content) async {}

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
  Locator get currentLocation => const Locator(sectionId: 'epub');

  @override
  Stream<double> get progress => Stream<double>.empty();

  @override
  Future<List<SearchHit>> search(String query) async => const [];

  @override
  SectionContent sectionContent(String sectionId) =>
      SectionContent(sectionId: sectionId, text: '');
}
