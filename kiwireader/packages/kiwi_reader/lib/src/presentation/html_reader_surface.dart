import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../config/reader_config.dart';
import '../content/html_content.dart';
import '../rendering/html_renderer.dart';

/// A draft text selection (offsets in the section's canonical text).
class LiveSelection {
  final String sectionId;
  final int start;
  final int end;
  final String text;
  const LiveSelection({
    required this.sectionId,
    required this.start,
    required this.end,
    required this.text,
  });
}

/// The reading surface. Renders each SECTION as a single styled [TextPainter]
/// (paragraph breaks preserved) so a long-press-drag selection spans blocks
/// (cross-block selection). Highlights and selections live in canonical space
/// via the section's [OffsetMap]; per-section bookmark toggles sit in the
/// header.
class HtmlReaderSurface extends StatelessWidget {
  final HtmlRenderer renderer;
  final List<Annotation> annotations;
  final ReaderConfig config;
  final LiveSelection? live;
  final void Function(LiveSelection?) onDraft;
  final void Function(Annotation) onTapAnnotation;
  final Map<String, GlobalKey> sectionKeys;
  final Set<String> bookmarkedSections;
  final void Function(String sectionId) onToggleBookmark;

  const HtmlReaderSurface({
    super.key,
    required this.renderer,
    required this.annotations,
    required this.config,
    required this.live,
    required this.onDraft,
    required this.onTapAnnotation,
    required this.sectionKeys,
    required this.bookmarkedSections,
    required this.onToggleBookmark,
  });

  static const _resolver = AnchorResolver();

  Color _colorFor(String? token) {
    for (final c in config.palette) {
      if (c.token == token) return c.color;
    }
    return config.palette.isNotEmpty
        ? config.palette.first.color
        : const Color(0xFFFDE68A);
  }

  @override
  Widget build(BuildContext context) {
    final isDark = config.theme == ReaderTheme.dark;
    final ink = isDark ? const Color(0xFFE6EDE9) : const Color(0xFF13211A);
    final body = TextStyle(
      fontSize: 16 * config.fontScale,
      height: 1.6,
      color: ink,
    );
    final head = body.copyWith(
      fontSize: 20 * config.fontScale,
      fontWeight: FontWeight.w700,
    );
    final mono = body.copyWith(fontFamily: 'monospace');
    TextStyle styleFor(HtmlBlockType t) => switch (t) {
      HtmlBlockType.heading => head,
      HtmlBlockType.math => mono,
      HtmlBlockType.paragraph => body,
    };

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 140),
      itemCount: renderer.sections.length,
      itemBuilder: (context, i) {
        final section = renderer.sections[i];
        final sv = buildSectionView(section);
        final sectionContent = SectionContent(
          sectionId: section.id,
          text: sv.canonical,
        );

        final paint = <(int, int, Color)>[];
        final hit = <(int, int, Annotation)>[];
        for (final a in annotations) {
          if (a.isDeleted || a.anchor.sectionId != section.id) continue;
          if (a.type == AnnotationType.bookmark) continue;
          final r = _resolver.resolve(a.anchor, sectionContent);
          if (r.located && r.state != AnchorState.orphaned) {
            final opacity = a.type == AnnotationType.note ? 0.30 : 0.55;
            paint.add((
              r.start!,
              r.end!,
              _colorFor(a.color).withOpacity(opacity),
            ));
            hit.add((r.start!, r.end!, a));
          }
        }
        final liveGlobal = (live != null && live!.sectionId == section.id)
            ? (live!.start, live!.end)
            : null;
        final isBookmarked = bookmarkedSections.contains(section.id);

        return Container(
          key: sectionKeys[section.id],
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.only(bottom: 10, top: 6),
                child: Row(
                  children: [
                    Expanded(
                      child: section.title != null
                          ? Text(section.title!, style: head)
                          : const SizedBox.shrink(),
                    ),
                    IconButton(
                      tooltip: 'Bookmark',
                      visualDensity: VisualDensity.compact,
                      icon: Icon(
                        isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                        color: isBookmarked ? const Color(0xFF16A34A) : null,
                        size: 20,
                      ),
                      onPressed: () => onToggleBookmark(section.id),
                    ),
                  ],
                ),
              ),
              _SectionTextView(
                view: sv,
                styleFor: styleFor,
                highlights: paint, // canonical coords
                live: liveGlobal,
                onSelect: (s, e, ended) =>
                    _onSelect(section.id, sv, s, e, ended),
                onTap: (canon) => _onTap(hit, canon),
              ),
            ],
          ),
        );
      },
    );
  }

  void _onSelect(String sectionId, SectionView sv, int s, int e, bool ended) {
    final start = math.min(s, e), end = math.max(s, e);
    if (start >= end) {
      if (ended) onDraft(null);
      return;
    }
    onDraft(
      LiveSelection(
        sectionId: sectionId,
        start: start,
        end: end,
        text: sv.canonical.substring(start, end),
      ),
    );
  }

  void _onTap(List<(int, int, Annotation)> hit, int canon) {
    for (final h in hit) {
      if (canon >= h.$1 && canon < h.$2) {
        onTapAnnotation(h.$3);
        return;
      }
    }
  }
}

/// One section: a single styled [TextPainter] (multi-span) that handles
/// cross-block selection, highlight painting and taps. Display↔canonical
/// conversion goes through the section's [OffsetMap].
class _SectionTextView extends StatefulWidget {
  final SectionView view;
  final TextStyle Function(HtmlBlockType) styleFor;
  final List<(int, int, Color)> highlights; // canonical
  final (int, int)? live; // canonical
  final void Function(int canonStart, int canonEnd, bool ended) onSelect;
  final void Function(int canon) onTap;

  const _SectionTextView({
    required this.view,
    required this.styleFor,
    required this.highlights,
    required this.live,
    required this.onSelect,
    required this.onTap,
  });

  @override
  State<_SectionTextView> createState() => _SectionTextViewState();
}

class _SectionTextViewState extends State<_SectionTextView> {
  TextPainter? _tp;
  double _width = -1;
  int? _baseCanon;

  TextSpan _span() {
    final d = widget.view.display;
    final children = <TextSpan>[];
    var cursor = 0;
    for (final run in widget.view.runs) {
      if (run.start > cursor) {
        children.add(
          TextSpan(text: d.substring(cursor, run.start)),
        ); // separators
      }
      children.add(
        TextSpan(
          text: d.substring(run.start, run.end),
          style: widget.styleFor(run.type),
        ),
      );
      cursor = run.end;
    }
    if (cursor < d.length) children.add(TextSpan(text: d.substring(cursor)));
    return TextSpan(children: children);
  }

  TextPainter _layout(double width) =>
      TextPainter(text: _span(), textDirection: TextDirection.ltr)
        ..layout(maxWidth: width);

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        if (_tp == null || _width != width) {
          _tp = _layout(width);
          _width = width;
        }
        final tp = _tp!;
        int canonAt(Offset local) =>
            widget.view.map.toCanonical(tp.getPositionForOffset(local).offset);

        return GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapUp: (d) => widget.onTap(canonAt(d.localPosition)),
          onLongPressStart: (d) {
            _baseCanon = canonAt(d.localPosition);
            widget.onSelect(_baseCanon!, _baseCanon!, false);
          },
          onLongPressMoveUpdate: (d) {
            final e = canonAt(d.localPosition);
            widget.onSelect(_baseCanon ?? e, e, false);
          },
          onLongPressEnd: (d) {
            final e = canonAt(d.localPosition);
            widget.onSelect(_baseCanon ?? e, e, true);
          },
          child: CustomPaint(
            size: Size(width, tp.height),
            painter: _SectionPainter(
              tp,
              widget.view.map,
              widget.highlights,
              widget.live,
            ),
          ),
        );
      },
    );
  }
}

class _SectionPainter extends CustomPainter {
  final TextPainter tp;
  final OffsetMap map;
  final List<(int, int, Color)> highlights; // canonical
  final (int, int)? live; // canonical

  _SectionPainter(this.tp, this.map, this.highlights, this.live);

  void _paintRange(Canvas canvas, int canonStart, int canonEnd, Paint paint) {
    if (canonStart >= canonEnd) return;
    final (ds, de) = map.toDisplayRange(canonStart, canonEnd);
    if (ds >= de) return;
    for (final box in tp.getBoxesForSelection(
      TextSelection(baseOffset: ds, extentOffset: de),
    )) {
      canvas.drawRRect(RRect.fromRectXY(box.toRect(), 2, 2), paint);
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (final h in highlights) {
      _paintRange(canvas, h.$1, h.$2, Paint()..color = h.$3);
    }
    final l = live;
    if (l != null) {
      _paintRange(canvas, l.$1, l.$2, Paint()..color = const Color(0x3316A34A));
    }
    tp.paint(canvas, Offset.zero);
  }

  @override
  bool shouldRepaint(covariant _SectionPainter old) => true;
}
