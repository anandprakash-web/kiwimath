import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// A single slide in the explanation carousel.
class ExplanationSlide {
  final String title;
  final String content;
  final Widget? visual;
  final String? visualLabel;
  final bool isConclusion;

  const ExplanationSlide({
    required this.title,
    required this.content,
    this.visual,
    this.visualLabel,
    this.isConclusion = false,
  });
}

/// Explanation carousel shown after "Help me learn" on a wrong answer.
/// Receives context about what went wrong and builds relevant slides.
class ExplanationScreen extends StatefulWidget {
  final String feedbackMessage;
  final String questionStem;
  final String correctAnswer;
  final String wrongAnswer;
  final VoidCallback onDone;

  const ExplanationScreen({
    super.key,
    required this.feedbackMessage,
    required this.questionStem,
    required this.correctAnswer,
    required this.wrongAnswer,
    required this.onDone,
  });

  @override
  State<ExplanationScreen> createState() => _ExplanationScreenState();
}

class _ExplanationScreenState extends State<ExplanationScreen> {
  int _currentSlide = 0;

  late final List<ExplanationSlide> _slides;

  @override
  void initState() {
    super.initState();
    _slides = _buildSlides();
  }

  List<ExplanationSlide> _buildSlides() {
    // Build contextual slides based on the actual question
    return [
      // Slide 1: What went wrong
      ExplanationSlide(
        title: 'Let\'s think about this',
        content: widget.feedbackMessage,
        visual: Container(
          padding: const EdgeInsets.all(12),
          child: Text(
            widget.questionStem,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: KiwiColors.textDark,
              height: 1.4,
            ),
          ),
        ),
        visualLabel: 'The question you were working on',
      ),
      // Slide 2: The correct answer
      ExplanationSlide(
        title: 'The answer',
        content: 'You picked ${widget.wrongAnswer}, but the correct answer '
            'is ${widget.correctAnswer}. Let\'s practise this step by step '
            'so it clicks!',
        visual: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Wrong
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFFFFEBEE),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: KiwiColors.wrong, width: 1.5),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.close, color: KiwiColors.wrong, size: 18),
                  const SizedBox(width: 6),
                  Text(
                    widget.wrongAnswer,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.wrong,
                    ),
                  ),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Icon(Icons.arrow_forward, color: KiwiColors.textMuted, size: 20),
            ),
            // Correct
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiGreenLight,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: KiwiColors.kiwiGreen, width: 1.5),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.check, color: KiwiColors.kiwiGreenDark, size: 18),
                  const SizedBox(width: 6),
                  Text(
                    widget.correctAnswer,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.kiwiGreenDark,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        visualLabel: 'Your answer → Correct answer',
        isConclusion: true,
      ),
    ];
  }

  void _next() {
    if (_currentSlide < _slides.length - 1) {
      setState(() => _currentSlide++);
    } else {
      widget.onDone();
    }
  }

  void _back() {
    if (_currentSlide > 0) {
      setState(() => _currentSlide--);
    }
  }

  @override
  Widget build(BuildContext context) {
    final slide = _slides[_currentSlide];

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildDots(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: _buildSlideContent(slide),
              ),
            ),
            _buildBottomNav(slide.isConclusion),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: const BoxDecoration(
        color: KiwiColors.visualYellowBg,
        border: Border(
          bottom: BorderSide(color: KiwiColors.visualYellowBorder, width: 1),
        ),
      ),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: const SizedBox(
              width: 28,
              child: Text(
                '\u2715',
                style: TextStyle(fontSize: 16, color: Color(0xFFBF360C)),
              ),
            ),
          ),
          const Expanded(
            child: Text(
              'Understanding the answer',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                color: Color(0xFFE65100),
              ),
            ),
          ),
          const SizedBox(width: 28),
        ],
      ),
    );
  }

  Widget _buildDots() {
    return Padding(
      padding: const EdgeInsets.only(top: 12, bottom: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(_slides.length, (i) {
          final isActive = i == _currentSlide;
          return Padding(
            padding: EdgeInsets.only(left: i == 0 ? 0 : 5),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeInOut,
              width: isActive ? 20 : 7,
              height: 7,
              decoration: BoxDecoration(
                color: isActive
                    ? KiwiColors.warmOrange
                    : KiwiColors.warmOrangeBorder,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildSlideContent(ExplanationSlide slide) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Text(
            slide.title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: KiwiColors.textDark,
            ),
          ),
        ),
        if (slide.visual != null)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: slide.isConclusion
                  ? KiwiColors.kiwiGreenLight
                  : KiwiColors.visualYellowBg,
              border: Border.all(
                color: slide.isConclusion
                    ? const Color(0xFFA5D6A7)
                    : KiwiColors.visualYellowBorder,
                width: 1.5,
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Column(
              children: [
                slide.visual!,
                if (slide.visualLabel != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    slide.visualLabel!,
                    style: TextStyle(
                      fontSize: 10,
                      color: slide.isConclusion
                          ? const Color(0xFF558B2F)
                          : const Color(0xFFF57F17),
                    ),
                  ),
                ],
              ],
            ),
          ),
        const SizedBox(height: 14),
        Text(
          slide.content,
          style: const TextStyle(
            fontSize: 14,
            color: KiwiColors.textDark,
            height: 1.55,
          ),
        ),
      ],
    );
  }

  Widget _buildBottomNav(bool isConclusion) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: Color(0xFFF0F0F0), width: 1)),
      ),
      child: Row(
        children: [
          if (_currentSlide > 0) ...[
            GestureDetector(
              onTap: _back,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  border: Border.all(color: const Color(0xFFE0E0E0), width: 2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  '\u2190 Back',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 10),
          ],
          Expanded(
            child: GestureDetector(
              onTap: _next,
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  color: isConclusion
                      ? KiwiColors.kiwiGreen
                      : KiwiColors.warmOrange,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isConclusion ? 'Now try it yourself \u2192' : 'Next \u2192',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
