import 'dart:convert';

import 'package:kiwi_reader_core/kiwi_reader_core.dart' show OffsetMap;

/// Block kinds in the custom HTML/JSON content format (Phase-0 source format).
enum HtmlBlockType { heading, paragraph, math }

class HtmlBlock {
  final HtmlBlockType type;

  /// Raw display text. May contain intentional line breaks (kept on screen via
  /// the per-block [OffsetMap]). For [HtmlBlockType.math] this is LaTeX source.
  final String text;

  const HtmlBlock(this.type, this.text);

  factory HtmlBlock.fromJson(Map<String, dynamic> j) => HtmlBlock(
    HtmlBlockType.values.byName((j['type'] as String?) ?? 'paragraph'),
    (j['text'] as String?) ?? '',
  );
}

class HtmlSection {
  final String id;
  final String? title;
  final List<HtmlBlock> blocks;

  const HtmlSection({required this.id, this.title, required this.blocks});

  factory HtmlSection.fromJson(Map<String, dynamic> j) => HtmlSection(
    id: j['id'] as String,
    title: j['title'] as String?,
    blocks: ((j['blocks'] as List?) ?? const [])
        .map((e) => HtmlBlock.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList(),
  );
}

class HtmlBook {
  final String id;
  final String? title;
  final List<HtmlSection> sections;

  const HtmlBook({required this.id, this.title, required this.sections});

  factory HtmlBook.fromJson(Map<String, dynamic> j) => HtmlBook(
    id: j['id'] as String,
    title: j['title'] as String?,
    sections: ((j['sections'] as List?) ?? const [])
        .map((e) => HtmlSection.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList(),
  );

  static HtmlBook decode(String jsonStr) =>
      HtmlBook.fromJson(jsonDecode(jsonStr) as Map<String, dynamic>);
}

/// One block laid out for the reader: the raw [display] text it paints, an
/// [OffsetMap] between that display text and the block's canonical text, and
/// the block's [base] offset within the section's canonical stream.
class BlockLayout {
  final HtmlBlock block;
  final String display;
  final OffsetMap map;
  final int base;

  const BlockLayout({
    required this.block,
    required this.display,
    required this.map,
    required this.base,
  });

  int get canonStart => base;
  int get canonEnd => base + map.length;
}

/// The canonical text of a section + the laid-out blocks. Both the resolver
/// (via `sectionContent`) and the surface derive from THIS, so selection,
/// anchoring and painting all share one coordinate space.
class SectionCanonical {
  final String text;
  final List<BlockLayout> blocks;
  const SectionCanonical(this.text, this.blocks);
}

SectionCanonical buildSectionCanonical(HtmlSection s) {
  final buf = StringBuffer();
  final layouts = <BlockLayout>[];
  for (final b in s.blocks) {
    final map = OffsetMap.build(b.text);
    if (map.canonical.isEmpty) continue;
    if (buf.isNotEmpty) buf.write(' '); // single-space join == normalized
    final base = buf.length;
    buf.write(map.canonical);
    layouts.add(BlockLayout(block: b, display: b.text, map: map, base: base));
  }
  return SectionCanonical(buf.toString(), layouts);
}

/// A style span (block) within the section's DISPLAY string.
class StyleRun {
  final int start;
  final int end;
  final HtmlBlockType type;
  const StyleRun(this.start, this.end, this.type);
}

/// A whole section rendered as ONE painter: a display string with real
/// paragraph breaks, an [OffsetMap] from that display to the section's
/// canonical text (so selections span blocks — cross-block selection — and
/// anchors stay in canonical coords), and the per-block [StyleRun]s.
class SectionView {
  final String display;
  final OffsetMap map;
  final List<StyleRun> runs;
  const SectionView(this.display, this.map, this.runs);
  String get canonical => map.canonical;
}

/// Blocks joined by a blank line ('\n\n'); each block trimmed at the ends so
/// canonical (whitespace-collapsed) stays stable across re-exports.
SectionView buildSectionView(HtmlSection s) {
  final buf = StringBuffer();
  final runs = <StyleRun>[];
  for (final b in s.blocks) {
    final t = b.text.trim();
    if (t.isEmpty) continue;
    if (buf.isNotEmpty) buf.write('\n\n');
    final start = buf.length;
    buf.write(t);
    runs.add(StyleRun(start, buf.length, b.type));
  }
  final display = buf.toString();
  return SectionView(display, OffsetMap.build(display), runs);
}
