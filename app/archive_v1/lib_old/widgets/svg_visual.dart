import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/question.dart';
import '../models/session_response.dart';

/// Renders an inline SVG visual. Accepts either a KiwiVisual (legacy) or
/// a SessionVisual (session API) or raw SVG string.
class KiwiVisualWidget extends StatelessWidget {
  final KiwiVisual? visual;
  final SessionVisual? sessionVisual;

  const KiwiVisualWidget({super.key, this.visual, this.sessionVisual});

  /// Returns true if the visual has real SVG content to display.
  bool get hasContent {
    final svg = visual?.svg ?? sessionVisual?.svg;
    final kind = visual?.kind ?? sessionVisual?.kind;
    return kind == 'svg_inline' &&
        svg != null &&
        svg.trim().isNotEmpty &&
        svg.contains('<svg');
  }

  @override
  Widget build(BuildContext context) {
    final svg = visual?.svg ?? sessionVisual?.svg;
    if (hasContent && svg != null) {
      // Use the backend-generated alt-text for screen reader accessibility.
      // Falls back to generic label if alt-text is not available.
      final altText = sessionVisual?.altText ?? 'Question illustration';
      return Semantics(
        label: altText,
        image: true,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxHeight: 120),
          child: SvgPicture.string(
            svg,
            fit: BoxFit.contain,
            semanticsLabel: altText,
          ),
        ),
      );
    }
    return const SizedBox.shrink();
  }
}
