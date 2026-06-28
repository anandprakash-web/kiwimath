import 'package:flutter/widgets.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../config/reader_config.dart';
import '../host/providers.dart';

/// A user text selection, expressed in canonical-text offsets within a section.
class Selection {
  final String sectionId;
  final int start;
  final int end;
  final String text;
  const Selection({
    required this.sectionId,
    required this.start,
    required this.end,
    required this.text,
  });
}

/// A search result location + a short snippet for display.
class SearchHit {
  final Locator locator;
  final String snippet;
  const SearchHit(this.locator, this.snippet);
}

/// Rendering parameters the host's config maps onto.
class ViewportConfig {
  final ReaderTheme theme;
  final ReadingMode mode;
  final double fontScale;
  const ViewportConfig({
    required this.theme,
    required this.mode,
    this.fontScale = 1.0,
  });
}

/// THE SEAM every format implements (design §Architecture, Figure 2).
///
/// The annotation overlay and ink layer talk ONLY to this interface — they
/// never import a PDF/EPUB package. Adding a new format = one new adapter,
/// zero changes elsewhere. The two methods that matter for annotations are
/// [rectsForAnchor] (draw) and [anchorForSelection] (create).
abstract class ContentRenderer {
  Future<void> load(BookManifest manifest, ContentProvider content);
  Widget buildViewport(ViewportConfig config);

  /// Map a resolved anchor to on-screen rectangles (highlight / underline).
  Future<List<Rect>> rectsForAnchor(Anchor anchor);

  /// Build a layered anchor from a user text selection.
  Future<Anchor?> anchorForSelection(Selection selection);

  /// Build a point anchor (sticky note / ink origin) from a tap position.
  Future<Anchor?> anchorForPoint(Offset point);

  Future<void> goTo(Locator locator);
  Locator get currentLocation;
  Stream<double> get progress;
  Future<List<SearchHit>> search(String query);

  /// Canonical text for a section, consumed by the core [AnchorResolver].
  SectionContent sectionContent(String sectionId);
}
