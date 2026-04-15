import 'package:flutter/material.dart';

import '../theme/kiwi_theme.dart';

/// Warm feedback panel shown after a wrong answer on a parent question.
/// Explains what went wrong in kid-friendly language, then invites the child
/// to try it step by step.
class FeedbackBanner extends StatelessWidget {
  final String message;
  final String ctaLabel;
  final VoidCallback onContinue;
  final BannerTone tone;

  const FeedbackBanner({
    super.key,
    required this.message,
    required this.ctaLabel,
    required this.onContinue,
    this.tone = BannerTone.gentle,
  });

  @override
  Widget build(BuildContext context) {
    final bg = tone == BannerTone.success
        ? KiwiColors.kiwiGreenLight
        : const Color(0xFFFFF3E0);
    final border = tone == BannerTone.success
        ? KiwiColors.kiwiGreen
        : const Color(0xFFFFB74D);
    final icon = tone == BannerTone.success
        ? Icons.emoji_events
        : Icons.lightbulb_outline;
    final iconColor =
        tone == BannerTone.success ? KiwiColors.kiwiGreenDark : const Color(0xFFF57C00);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: border, width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(icon, size: 36, color: iconColor),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  message,
                  style: const TextStyle(
                    fontSize: 18,
                    height: 1.3,
                    color: KiwiColors.textDark,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: onContinue,
            child: Text(ctaLabel),
          ),
        ],
      ),
    );
  }
}

enum BannerTone { gentle, success }
