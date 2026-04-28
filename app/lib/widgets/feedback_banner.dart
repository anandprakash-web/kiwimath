import 'package:flutter/material.dart';

import '../theme/kiwi_theme.dart';

enum BannerTone { gentle, success }

/// v2 wrong-answer bottom sheet with "Try again" / "Help me learn" split.
///
/// When [scaffoldLevel] is 1 or 2 and [retrySameQuestion] is true, the sheet
/// adapts its appearance to show scaffold-level-appropriate hints:
///   Level 1: gentle hint (light blue, lightbulb icon)
///   Level 2: stronger hint with misconception (orange, warning icon)
///   Level 0 / 3: default behaviour (orange, thinking emoji)
class WrongAnswerSheet extends StatelessWidget {
  final String hint;
  final VoidCallback onTryAgain;
  final VoidCallback onHelpMeLearn;

  /// Whether the server wants the user to retry the same question.
  final bool retrySameQuestion;

  /// 0=none, 1=text hint, 2=visual/misconception hint, 3=step-down.
  final int scaffoldLevel;

  /// Whether to show the "Try again" button. Set to false at scaffold level 3+
  /// to force the user into the step-down path.
  final bool showTryAgain;

  const WrongAnswerSheet({
    super.key,
    required this.hint,
    required this.onTryAgain,
    required this.onHelpMeLearn,
    this.retrySameQuestion = false,
    this.scaffoldLevel = 0,
    this.showTryAgain = true,
  });

  @override
  Widget build(BuildContext context) {
    // Determine scaffold-level styling.
    final bool isScaffoldHint = retrySameQuestion && (scaffoldLevel == 1 || scaffoldLevel == 2);
    final Color bgColor;
    final Color borderColor;
    final Color titleColor;
    final Color hintTextColor;
    final IconData? iconData;
    final String titleText;

    if (isScaffoldHint && scaffoldLevel == 1) {
      // Level 1: gentle hint — light blue
      bgColor = const Color(0xFFE3F2FD);          // KiwiColors.visualBlueBg
      borderColor = const Color(0xFF90CAF9);       // KiwiColors.visualBlueBorder
      titleColor = const Color(0xFF1565C0);
      hintTextColor = const Color(0xFF1976D2);
      iconData = Icons.lightbulb_outline;
      titleText = 'Here\'s a hint';
    } else if (isScaffoldHint && scaffoldLevel == 2) {
      // Level 2: stronger hint with misconception — orange/warning
      bgColor = KiwiColors.warmOrangeBg;
      borderColor = KiwiColors.warmOrange;
      titleColor = KiwiColors.warmOrangeDark;
      hintTextColor = const Color(0xFFBF360C);
      iconData = Icons.warning_amber_rounded;
      titleText = 'Watch out for this';
    } else {
      // Default (level 0 or 3)
      bgColor = KiwiColors.warmOrangeBg;
      borderColor = KiwiColors.warmOrange;
      titleColor = KiwiColors.warmOrangeDark;
      hintTextColor = const Color(0xFFBF360C);
      iconData = null; // use emoji instead
      titleText = 'Not quite!';
    }

    return Container(
      decoration: BoxDecoration(
        color: bgColor,
        border: Border(top: BorderSide(color: borderColor, width: 2)),
      ),
      padding: const EdgeInsets.all(14),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (iconData != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Icon(iconData, size: 22, color: titleColor),
                  )
                else
                  const Text('\u{1F914}', style: TextStyle(fontSize: 22)),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        titleText,
                        style: TextStyle(
                          fontWeight: FontWeight.w700,
                          color: titleColor,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        hint,
                        style: TextStyle(
                          fontSize: 12,
                          color: hintTextColor,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // When retrying the same question at scaffold levels 1-2,
            // prominently show "Try again" and de-emphasise "Help me learn".
            if (retrySameQuestion && scaffoldLevel >= 1 && scaffoldLevel <= 2)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onTryAgain,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: scaffoldLevel == 1
                        ? const Color(0xFF42A5F5)
                        : KiwiColors.warmOrange,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    elevation: 2,
                    textStyle: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: const Text('Try again'),
                ),
              )
            // At scaffold level 3+, skip "Try again" and show only the
            // step-down button so the child gets proper scaffolding.
            else if (!showTryAgain)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: onHelpMeLearn,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: KiwiColors.warmOrange,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 11),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                    elevation: 2,
                    textStyle: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  child: const Text("Let\u2019s break it down \u2192"),
                ),
              )
            else
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: onTryAgain,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: KiwiColors.warmOrangeDark,
                        side: const BorderSide(color: Color(0xFFFFB74D), width: 2),
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        textStyle: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: const Text('Try again'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: onHelpMeLearn,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: KiwiColors.warmOrange,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        elevation: 2,
                        shadowColor: KiwiColors.warmOrange.withAlpha(77),
                        textStyle: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: const Text('Help me learn \u2192'),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

/// v2 correct answer inline bar — compact, celebratory.
///
/// Varies the celebration text so repeated correct answers don't feel repetitive.
class CorrectAnswerBar extends StatelessWidget {
  final int xpEarned;
  final VoidCallback onContinue;
  /// Current streak count — used to pick varied celebration text.
  final int streak;

  const CorrectAnswerBar({
    super.key,
    this.xpEarned = 15,
    required this.onContinue,
    this.streak = 0,
  });

  static const _celebrations = [
    'Correct!',
    'Amazing!',
    'Well done!',
    'Great job!',
    'You got it!',
    'Brilliant!',
    'Super!',
    'Awesome!',
    'Nailed it!',
    'Perfect!',
  ];

  String get _celebrationText {
    if (streak >= 5) return 'On fire! \u{1F525}';
    if (streak >= 3) return 'Unstoppable!';
    return _celebrations[xpEarned % _celebrations.length];
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFFB9F6CA), Color(0xFF69F0AE)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
        border: Border(top: BorderSide(color: Color(0xFF00E676), width: 3)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.check_circle, color: Color(0xFF00962E), size: 26),
                const SizedBox(width: 8),
                Text(
                  _celebrationText,
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF00962E),
                    fontSize: 18,
                  ),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFFAA00FF), Color(0xFF7C4DFF)],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFFAA00FF).withOpacity(0.3),
                        blurRadius: 6,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.bolt, size: 14, color: Colors.white),
                      const SizedBox(width: 2),
                      Text(
                        '+$xpEarned XP',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: onContinue,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00C853),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 13),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  elevation: 3,
                  shadowColor: const Color(0xFF00C853).withOpacity(0.4),
                  textStyle: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                child: const Text('Continue'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Legacy feedback banner — kept for backwards compat if needed.
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
        : KiwiColors.warmOrangeBg;
    final border = tone == BannerTone.success
        ? KiwiColors.kiwiGreen
        : const Color(0xFFFFB74D);
    final icon = tone == BannerTone.success
        ? Icons.emoji_events
        : Icons.lightbulb_outline;
    final iconColor =
        tone == BannerTone.success ? KiwiColors.kiwiGreenDark : KiwiColors.warmOrangeDark;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: border, width: 2),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(icon, size: 32, color: iconColor),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  message,
                  style: const TextStyle(
                    fontSize: 15,
                    height: 1.3,
                    color: KiwiColors.textDark,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: onContinue,
            child: Text(ctaLabel),
          ),
        ],
      ),
    );
  }
}
