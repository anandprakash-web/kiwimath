import 'package:flutter/material.dart';
import '../models/companion.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/companion_view.dart';

/// Celebration screen — v7.0 simplified, meaningful.
///
/// Shows:
///   1. Kiwi character reaction (happy/proud based on score)
///   2. Big score display (e.g. "8/10")
///   3. One progress insight ("You moved up in Arithmetic!")
///   4. Gentle practice-days note ("You practiced 3 days this week!")
///   5. Play-again / back-to-home buttons
///
/// Removed: coins, gems, XP, persona badges — too much clutter,
/// no meaning to kids about their actual progress.
class CelebrationScreen extends StatefulWidget {
  final int xpEarned;          // kept internally for backend, not displayed
  final int coinsEarned;       // kept internally for backend, not displayed
  final int gemsEarned;        // kept internally for backend, not displayed
  final int currentStreak;     // reframed as "practice days this week"
  final int dailyRemaining;
  final bool fromStepDown;
  final VoidCallback onContinue;
  final int? correctCount;
  final int? totalQuestions;
  final int? comebackBonus;    // kept for backend, not displayed
  final int? improvementBonus; // kept for backend, not displayed
  final String? personaName;   // kept for backend, not displayed
  final String? personaEmoji;
  final CompanionService? companionService;
  // v6: progress insight message
  final String? progressInsight;

  const CelebrationScreen({
    super.key,
    required this.xpEarned,
    this.coinsEarned = 0,
    required this.gemsEarned,
    required this.currentStreak,
    required this.dailyRemaining,
    this.fromStepDown = false,
    required this.onContinue,
    this.correctCount,
    this.totalQuestions,
    this.comebackBonus,
    this.improvementBonus,
    this.personaName,
    this.personaEmoji,
    this.companionService,
    this.progressInsight,
  });

  @override
  State<CelebrationScreen> createState() => _CelebrationScreenState();
}

class _CelebrationScreenState extends State<CelebrationScreen>
    with SingleTickerProviderStateMixin {
  bool _showContent = false;

  late final AnimationController _bounceCtrl;
  late final Animation<double> _bounceScale;

  @override
  void initState() {
    super.initState();

    _bounceCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _bounceScale = CurvedAnimation(
      parent: _bounceCtrl,
      curve: Curves.elasticOut,
    );

    Future.microtask(() {
      _bounceCtrl.forward();
    });

    Future.delayed(const Duration(milliseconds: 400), () {
      if (mounted) setState(() => _showContent = true);
    });
  }

  @override
  void dispose() {
    _bounceCtrl.dispose();
    super.dispose();
  }

  double get _scoreRatio {
    if (widget.correctCount == null || widget.totalQuestions == null) return 0.5;
    if (widget.totalQuestions == 0) return 0.5;
    return widget.correctCount! / widget.totalQuestions!;
  }

  String get _kiwiReaction {
    if (_scoreRatio >= 0.9) return '\u{1F929}';  // star-struck
    if (_scoreRatio >= 0.7) return '\u{1F60A}';  // happy
    if (_scoreRatio >= 0.5) return '\u{1F44D}';  // thumbs up
    return '\u{1F4AA}';                           // flexed bicep (keep trying!)
  }

  String get _encouragement {
    if (widget.fromStepDown) return 'You broke it into steps and solved it. That\'s real math thinking!';
    if (_scoreRatio >= 0.9) return 'Amazing! You\'re on fire!';
    if (_scoreRatio >= 0.7) return 'Great work! You\'re getting stronger!';
    if (_scoreRatio >= 0.5) return 'Good effort! Keep practicing!';
    return 'Every question makes you better. Let\'s keep going!';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            stops: [0.0, 0.5, 1.0],
            colors: [
              Color(0xFFFFF3E0),  // Warm orange mist
              Color(0xFFFFF8F0),  // Warm cream
              Color(0xFFFFF8F0),  // Warm cream
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              const Spacer(flex: 2),

              // 1. Kiwi character or companion
              ScaleTransition(
                scale: _bounceScale,
                child: widget.companionService != null &&
                        widget.companionService!.isLoaded
                    ? CompanionView(
                        surface: CompanionSurface.gradeCeremony,
                        config: widget.companionService!.config!,
                        size: 100,
                      )
                    : Container(
                        width: 100,
                        height: 100,
                        decoration: const BoxDecoration(
                          color: KiwiColors.kiwiPrimaryLight,
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            _kiwiReaction,
                            style: const TextStyle(fontSize: 52),
                          ),
                        ),
                      ),
              ),

              const SizedBox(height: 24),

              // 2. Big score
              AnimatedOpacity(
                opacity: _showContent ? 1.0 : 0.0,
                duration: const Duration(milliseconds: 500),
                child: Column(
                  children: [
                    if (widget.correctCount != null && widget.totalQuestions != null)
                      Text(
                        '${widget.correctCount}/${widget.totalQuestions}',
                        style: const TextStyle(
                          fontSize: 56,
                          fontWeight: FontWeight.w900,
                          color: KiwiColors.kiwiPrimaryDark,
                          height: 1.0,
                        ),
                      ),
                    const SizedBox(height: 6),
                    Text(
                      widget.fromStepDown ? 'You figured it out!' : 'Session complete!',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: KiwiColors.kiwiPrimaryDark,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40),
                      child: Text(
                        _encouragement,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 14,
                          color: KiwiColors.textMid,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 24),

              // 3. One progress insight (if available)
              if (widget.progressInsight != null)
                AnimatedOpacity(
                  opacity: _showContent ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 600),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 32),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: KiwiColors.kiwiPrimary.withOpacity(0.2)),
                    ),
                    child: Row(
                      children: [
                        const Text('\u{1F4C8}', style: TextStyle(fontSize: 20)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            widget.progressInsight!,
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: KiwiColors.kiwiPrimaryDark,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

              const SizedBox(height: 14),

              // 4. Gentle practice-days note
              AnimatedOpacity(
                opacity: _showContent ? 1.0 : 0.0,
                duration: const Duration(milliseconds: 700),
                child: Text(
                  'You practiced ${widget.currentStreak} days this week!',
                  style: const TextStyle(
                    fontSize: 12,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ),

              // 5. Daily goal nudge (gentle)
              if (widget.dailyRemaining > 0) ...[
                const SizedBox(height: 6),
                AnimatedOpacity(
                  opacity: _showContent ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 700),
                  child: Text(
                    '${widget.dailyRemaining} more to finish today\'s goal',
                    style: const TextStyle(
                      fontSize: 12,
                      color: KiwiColors.textMuted,
                    ),
                  ),
                ),
              ],

              const Spacer(flex: 3),

              // 6. Action buttons
              Padding(
                padding: const EdgeInsets.fromLTRB(28, 0, 28, 16),
                child: Column(
                  children: [
                    // Play again (primary — if daily goal not yet done)
                    if (widget.dailyRemaining > 0)
                      GestureDetector(
                        onTap: widget.onContinue,
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          decoration: BoxDecoration(
                            color: KiwiColors.kiwiPrimary,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 22),
                              const SizedBox(width: 6),
                              const Text(
                                'Keep practicing',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.white,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    if (widget.dailyRemaining > 0) const SizedBox(height: 10),
                    // Back to home (secondary)
                    GestureDetector(
                      onTap: widget.onContinue,
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: Colors.black12),
                        ),
                        child: const Text(
                          'Back to home',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: KiwiColors.kiwiPrimaryDark,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
