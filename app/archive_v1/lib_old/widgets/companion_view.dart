/// CompanionView — renders a companion on any surface.
///
/// Drop this widget wherever a companion should appear. It calls the
/// client-side resolver, loads the SVG pose, runs idle animations,
/// and handles fade/dismiss logic.
///
/// Usage:
///   CompanionView(
///     surface: CompanionSurface.lessonFraming,
///     config: companionConfig,  // fetched once at session start
///     size: 80,
///   )
library;

import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import '../models/companion.dart';

class CompanionView extends StatefulWidget {
  final CompanionSurface surface;
  final CompanionConfig config;
  final double size;
  final int problemStepsRequired;
  final int picoAppearancesInLesson;
  final VoidCallback? onTap;
  final VoidCallback? onDismiss;

  const CompanionView({
    super.key,
    required this.surface,
    required this.config,
    this.size = 72,
    this.problemStepsRequired = 1,
    this.picoAppearancesInLesson = 0,
    this.onTap,
    this.onDismiss,
  });

  @override
  State<CompanionView> createState() => CompanionViewState();
}

class CompanionViewState extends State<CompanionView>
    with TickerProviderStateMixin {
  late SummonResponse _response;
  late AnimationController _breathController;
  late AnimationController _fadeController;
  late AnimationController _bounceController;
  Timer? _blinkTimer;
  bool _isBlinking = false;
  final _random = Random();

  @override
  void initState() {
    super.initState();
    _response = resolveCompanion(
      surface: widget.surface,
      config: widget.config,
      problemStepsRequired: widget.problemStepsRequired,
      picoAppearancesInLesson: widget.picoAppearancesInLesson,
    );

    // Breath animation — continuous 2% scale pulse
    _breathController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 4000),
    )..repeat(reverse: true);

    // Fade controller for dismiss/retreat
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
      value: 1.0,
    );

    // Bounce for reactive animations (correct answer, etc.)
    _bounceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    _startBlinkCycle();
  }

  void _startBlinkCycle() {
    final interval = 4000 + _random.nextInt(3000); // 4-7s
    _blinkTimer = Timer(Duration(milliseconds: interval), () {
      if (mounted) {
        setState(() => _isBlinking = true);
        Future.delayed(const Duration(milliseconds: 200), () {
          if (mounted) {
            setState(() => _isBlinking = false);
            _startBlinkCycle();
          }
        });
      }
    });
  }

  @override
  void didUpdateWidget(CompanionView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.surface != widget.surface ||
        oldWidget.picoAppearancesInLesson != widget.picoAppearancesInLesson) {
      _response = resolveCompanion(
        surface: widget.surface,
        config: widget.config,
        problemStepsRequired: widget.problemStepsRequired,
        picoAppearancesInLesson: widget.picoAppearancesInLesson,
      );
    }
  }

  @override
  void dispose() {
    _blinkTimer?.cancel();
    _breathController.dispose();
    _fadeController.dispose();
    _bounceController.dispose();
    super.dispose();
  }

  /// Trigger a celebration bounce (call from parent on correct answer).
  void playCelebration() {
    _bounceController.forward(from: 0);
  }

  /// Trigger fade-out (call for deep-think retreat or dismiss).
  void fadeOut() {
    _fadeController.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final companion = widget.config.cast.firstWhere(
      (c) => c.id == _response.primaryId,
      orElse: () => widget.config.cast.first,
    );

    return FadeTransition(
      opacity: _fadeController,
      child: GestureDetector(
        onTap: widget.onTap,
        onLongPress: widget.onDismiss,
        child: AnimatedBuilder(
          animation: Listenable.merge([_breathController, _bounceController]),
          builder: (context, child) {
            final breathScale = 1.0 + (_breathController.value * 0.02);
            final bounceOffset =
                _bounceController.isAnimating ? sin(_bounceController.value * pi) * -8 : 0.0;

            return Transform.translate(
              offset: Offset(0, bounceOffset),
              child: Transform.scale(
                scale: breathScale,
                child: child,
              ),
            );
          },
          child: _CompanionAvatar(
            companion: companion,
            emotion: _response.primaryEmotion,
            size: widget.size,
            isBlinking: _isBlinking,
          ),
        ),
      ),
    );
  }
}

/// Renders the companion as a colored circle with the character initial
/// and emotion indicator. In production, this loads the SVG from CDN;
/// for now it's a beautiful placeholder that uses the signature colors.
class _CompanionAvatar extends StatelessWidget {
  final CompanionData companion;
  final Emotion emotion;
  final double size;
  final bool isBlinking;

  const _CompanionAvatar({
    required this.companion,
    required this.emotion,
    required this.size,
    required this.isBlinking,
  });

  @override
  Widget build(BuildContext context) {
    final emotionIcon = _emotionIcons[emotion] ?? '😊';

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Main avatar circle with signature color
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: companion.signatureColorSoft,
              border: Border.all(
                color: companion.signatureColor,
                width: 3,
              ),
              boxShadow: [
                BoxShadow(
                  color: companion.signatureColor.withValues(alpha: 0.3),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Center(
              child: Text(
                companion.name[0],
                style: TextStyle(
                  fontSize: size * 0.4,
                  fontWeight: FontWeight.w800,
                  color: companion.signatureColorText,
                ),
              ),
            ),
          ),
          // Emotion badge
          Positioned(
            bottom: 0,
            right: 0,
            child: Container(
              width: size * 0.35,
              height: size * 0.35,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white,
                border: Border.all(color: companion.signatureColor, width: 2),
              ),
              child: Center(
                child: Text(
                  isBlinking ? '😌' : emotionIcon,
                  style: TextStyle(fontSize: size * 0.18),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

const _emotionIcons = {
  Emotion.neutral: '😊',
  Emotion.thinking: '🤔',
  Emotion.happy: '😄',
  Emotion.encouraging: '💪',
  Emotion.celebrating: '🎉',
  Emotion.waving: '👋',
  Emotion.reading: '📖',
};
