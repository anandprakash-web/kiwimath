import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// Celebration screen shown when a student masters all 10 levels of a topic
/// and is ready to advance to the next grade level for that topic.
///
/// Inspired by Brilliant's milestone celebrations — bold, animated, and
/// gives the kid a clear sense of achievement before moving to harder content.
class GradeUpgradeScreen extends StatefulWidget {
  final String topicName;
  final int completedGrade;
  final int nextGrade;
  final int totalStars;
  final int maxStars; // typically 30 (10 levels × 3 stars)
  final VoidCallback onContinue;
  final VoidCallback? onStayHere;

  const GradeUpgradeScreen({
    super.key,
    required this.topicName,
    required this.completedGrade,
    required this.nextGrade,
    required this.totalStars,
    this.maxStars = 30,
    required this.onContinue,
    this.onStayHere,
  });

  @override
  State<GradeUpgradeScreen> createState() => _GradeUpgradeScreenState();
}

class _GradeUpgradeScreenState extends State<GradeUpgradeScreen>
    with TickerProviderStateMixin {
  late final AnimationController _trophyController;
  late final Animation<double> _trophyScale;
  late final AnimationController _fadeController;
  late final Animation<double> _fadeAnim;

  bool _showStars = false;
  bool _showMessage = false;
  bool _showButtons = false;

  @override
  void initState() {
    super.initState();
    _trophyController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _trophyScale = CurvedAnimation(
      parent: _trophyController,
      curve: Curves.elasticOut,
    );
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _fadeAnim = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeIn,
    );
    _startSequence();
  }

  Future<void> _startSequence() async {
    await Future.delayed(const Duration(milliseconds: 200));
    _trophyController.forward();
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;
    setState(() => _showStars = true);
    await Future.delayed(const Duration(milliseconds: 400));
    if (!mounted) return;
    setState(() => _showMessage = true);
    _fadeController.forward();
    await Future.delayed(const Duration(milliseconds: 400));
    if (!mounted) return;
    setState(() => _showButtons = true);
  }

  @override
  void dispose() {
    _trophyController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.nextGrade);
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              const Color(0xFF1A237E), // deep indigo
              const Color(0xFF283593),
              const Color(0xFF3949AB),
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              children: [
                const SizedBox(height: 40),
                // Trophy animation
                ScaleTransition(
                  scale: _trophyScale,
                  child: Container(
                    width: 120,
                    height: 120,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFFFD54F), Color(0xFFFFA000)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFFFD54F).withOpacity(0.4),
                          blurRadius: 30,
                          spreadRadius: 5,
                        ),
                      ],
                    ),
                    child: const Center(
                      child: Text(
                        '\u{1F3C6}',
                        style: TextStyle(fontSize: 56),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // Stars earned
                AnimatedOpacity(
                  opacity: _showStars ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 400),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: Colors.white.withOpacity(0.2),
                        width: 1.5,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text('\u{2B50}', style: TextStyle(fontSize: 18)),
                        const SizedBox(width: 8),
                        Text(
                          '${widget.totalStars} / ${widget.maxStars} Stars',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 28),
                // Main message
                AnimatedOpacity(
                  opacity: _showMessage ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 400),
                  child: Column(
                    children: [
                      const Text(
                        'GRADE MASTERED!',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFFFFD54F),
                          letterSpacing: 2,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'You completed all\nGrade ${widget.completedGrade} levels in',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w500,
                          color: Colors.white.withOpacity(0.9),
                          height: 1.4,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        widget.topicName,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 20),
                      // Grade transition visual
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildGradeBadge(
                            widget.completedGrade,
                            completed: true,
                          ),
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 12),
                            child: Icon(
                              Icons.arrow_forward_rounded,
                              color: Color(0xFFFFD54F),
                              size: 28,
                            ),
                          ),
                          _buildGradeBadge(
                            widget.nextGrade,
                            completed: false,
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Ready for Grade ${widget.nextGrade} challenges!',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.white.withOpacity(0.7),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 36),
                // Buttons
                AnimatedOpacity(
                  opacity: _showButtons ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 400),
                  child: Column(
                    children: [
                      // Primary: Continue to next grade
                      GestureDetector(
                        onTap: widget.onContinue,
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFFFFD54F), Color(0xFFFFA000)],
                            ),
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFFFFA000).withOpacity(0.4),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                'Start Grade ${widget.nextGrade}',
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w800,
                                  color: Color(0xFF1A237E),
                                ),
                              ),
                              const SizedBox(width: 8),
                              const Icon(
                                Icons.rocket_launch_rounded,
                                size: 20,
                                color: Color(0xFF1A237E),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      // Secondary: Stay and practice more
                      if (widget.onStayHere != null)
                        GestureDetector(
                          onTap: widget.onStayHere,
                          child: Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: Colors.white.withOpacity(0.25),
                                width: 1.5,
                              ),
                            ),
                            child: Text(
                              'Keep practising Grade ${widget.completedGrade}',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: Colors.white.withOpacity(0.8),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildGradeBadge(int grade, {required bool completed}) {
    return Container(
      width: 64,
      height: 64,
      decoration: BoxDecoration(
        color: completed
            ? const Color(0xFF4CAF50).withOpacity(0.2)
            : Colors.white.withOpacity(0.1),
        shape: BoxShape.circle,
        border: Border.all(
          color: completed
              ? const Color(0xFF4CAF50)
              : const Color(0xFFFFD54F),
          width: 3,
        ),
        boxShadow: !completed
            ? [
                BoxShadow(
                  color: const Color(0xFFFFD54F).withOpacity(0.3),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ]
            : null,
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (completed)
              const Icon(Icons.check_rounded, color: Color(0xFF4CAF50), size: 16),
            Text(
              'G$grade',
              style: TextStyle(
                fontSize: completed ? 14 : 18,
                fontWeight: FontWeight.w800,
                color: completed
                    ? const Color(0xFF4CAF50)
                    : const Color(0xFFFFD54F),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
