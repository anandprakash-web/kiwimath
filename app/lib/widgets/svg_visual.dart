import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../models/question.dart';

/// Renders a KiwiVisual (inline SVG or static asset). For now we only support
/// svg_inline — static asset rendering lands when we ship real illustrations.
class KiwiVisualWidget extends StatelessWidget {
  final KiwiVisual visual;
  const KiwiVisualWidget({super.key, required this.visual});

  @override
  Widget build(BuildContext context) {
    if (visual.kind == 'svg_inline' && visual.svg != null) {
      return ConstrainedBox(
        constraints: const BoxConstraints(maxHeight: 140),
        child: SvgPicture.string(
          visual.svg!,
          fit: BoxFit.contain,
          semanticsLabel: 'Question illustration',
        ),
      );
    }
    return const SizedBox.shrink();
  }
}
