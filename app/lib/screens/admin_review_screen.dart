import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/authed_svg.dart';

class AdminReviewScreen extends StatefulWidget {
  final String email;
  const AdminReviewScreen({super.key, required this.email});

  @override
  State<AdminReviewScreen> createState() => _AdminReviewScreenState();
}

class _AdminReviewScreenState extends State<AdminReviewScreen> {
  final _api = ApiClient();
  List<Map<String, dynamic>> _questions = [];
  int _currentIndex = 0;
  int _reviewedCount = 0;
  bool _loading = true;
  String? _error;

  int? _filterGrade;
  String? _filterTopic;
  int _page = 1;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  Future<void> _loadQuestions() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final questions = await _api.getReviewQuestions(
        grade: _filterGrade,
        topic: _filterTopic,
        page: _page,
      );
      setState(() {
        _questions = questions;
        _currentIndex = 0;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = _friendlyError(e);
      });
    }
  }

  String _friendlyError(Object e) {
    final msg = e.toString();
    if (msg.contains('SocketException') || msg.contains('ClientException')) {
      return 'Can\'t reach the server.\nCheck your internet and try again.';
    }
    if (msg.contains('TimeoutException')) {
      return 'Request timed out.\nThe server might be busy — try again.';
    }
    if (msg.contains('404')) {
      return 'No questions found for this filter.\nTry a different grade or topic.';
    }
    if (msg.contains('422') || msg.contains('validation')) {
      return 'Something went wrong with the request.\nTry refreshing.';
    }
    if (msg.contains('500') || msg.contains('502') || msg.contains('503')) {
      return 'Server error — try again in a moment.';
    }
    return 'Something went wrong.\nTap Retry to try again.';
  }

  Map<String, dynamic>? get _currentQuestion =>
      _questions.isNotEmpty && _currentIndex < _questions.length
          ? _questions[_currentIndex]
          : null;

  void _advance() {
    _reviewedCount++;
    if (_currentIndex + 1 < _questions.length) {
      setState(() => _currentIndex++);
    } else {
      _page++;
      _loadQuestions();
    }
  }

  Future<void> _onApprove() async {
    final q = _currentQuestion;
    if (q == null) return;
    try {
      await _api.approveQuestion(q['question_id'] as String, widget.email);
    } catch (_) {}
    _advance();
  }

  Future<void> _onFlag(String flagType, String comment,
      {String? correctAnswer}) async {
    final q = _currentQuestion;
    if (q == null) return;
    try {
      await _api.adminFlagQuestion(
        q['question_id'] as String,
        widget.email,
        flagType,
        comment,
        correctAnswer: correctAnswer,
      );
    } catch (_) {}
    _advance();
  }

  void _showFlagPicker() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _FlagSheet(
        onSubmit: (flagType, comment, {String? correctAnswer}) {
          Navigator.of(context).pop();
          _onFlag(flagType, comment, correctAnswer: correctAnswer);
        },
      ),
    );
  }

  void _showStats() async {
    try {
      final stats = await _api.getReviewStats();
      if (!mounted) return;
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: const Text('Review Stats',
              style: TextStyle(fontWeight: FontWeight.w800)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _statRow('Total reviewed', stats['total_reviewed']),
              _statRow('Approved', stats['approved']),
              _statRow('Flagged', stats['flagged']),
              _statRow('Pending', stats['pending']),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Could not load stats. Try again later.'),
            behavior: SnackBarBehavior.floating,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    }
  }

  Widget _statRow(String label, dynamic value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 14)),
          Text('${value ?? '-'}',
              style:
                  const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(_filterGrade ?? 3);

    return Scaffold(
      backgroundColor: tier.colors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: tier.colors.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Reviewed $_reviewedCount / ${_questions.length}',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
            color: tier.colors.textPrimary,
          ),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(Icons.bar_chart_rounded, color: tier.colors.primary),
            onPressed: _showStats,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildFilterChips(tier),
          Expanded(child: _buildBody(tier)),
        ],
      ),
    );
  }

  Widget _buildFilterChips(KiwiTier tier) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      child: Row(
        children: [
          for (int g = 1; g <= 6; g++)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text('Grade $g'),
                selected: _filterGrade == g,
                selectedColor: tier.colors.primary.withOpacity(0.15),
                checkmarkColor: tier.colors.primary,
                onSelected: (on) {
                  setState(() => _filterGrade = on ? g : null);
                  _page = 1;
                  _loadQuestions();
                },
              ),
            ),
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: const Text('Cambridge'),
              selected: _filterTopic == 'cambridge',
              selectedColor: tier.colors.primary.withOpacity(0.15),
              checkmarkColor: tier.colors.primary,
              onSelected: (on) {
                setState(
                    () => _filterTopic = on ? 'cambridge' : null);
                _page = 1;
                _loadQuestions();
              },
            ),
          ),
          FilterChip(
            label: const Text('NCERT'),
            selected: _filterTopic == 'ncert',
            selectedColor: tier.colors.primary.withOpacity(0.15),
            checkmarkColor: tier.colors.primary,
            onSelected: (on) {
              setState(() => _filterTopic = on ? 'ncert' : null);
              _page = 1;
              _loadQuestions();
            },
          ),
        ],
      ),
    );
  }

  Widget _buildBody(KiwiTier tier) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: tier.colors.primary.withOpacity(0.08),
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.cloud_off_rounded,
                    size: 36, color: tier.colors.textMuted),
              ),
              const SizedBox(height: 20),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15,
                  height: 1.5,
                  color: tier.colors.textSecondary,
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: 140,
                height: 44,
                child: ElevatedButton(
                  onPressed: _loadQuestions,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: tier.colors.primary,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                    elevation: 0,
                  ),
                  child: const Text('Retry',
                      style:
                          TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                ),
              ),
            ],
          ),
        ),
      );
    }
    final q = _currentQuestion;
    if (q == null) {
      return Center(
        child: Text('No questions to review',
            style: TextStyle(
                fontSize: 16, color: tier.colors.textSecondary)),
      );
    }
    return _SwipeCard(
      key: ValueKey(q['question_id']),
      question: q,
      tier: tier,
      apiBaseUrl: ApiClient.baseUrl,
      onSwipeRight: _onApprove,
      onSwipeLeft: _showFlagPicker,
    );
  }
}

class _SwipeCard extends StatefulWidget {
  final Map<String, dynamic> question;
  final KiwiTier tier;
  final String apiBaseUrl;
  final VoidCallback onSwipeRight;
  final VoidCallback onSwipeLeft;

  const _SwipeCard({
    super.key,
    required this.question,
    required this.tier,
    required this.apiBaseUrl,
    required this.onSwipeRight,
    required this.onSwipeLeft,
  });

  @override
  State<_SwipeCard> createState() => _SwipeCardState();
}

class _SwipeCardState extends State<_SwipeCard>
    with SingleTickerProviderStateMixin {
  double _dx = 0;
  double _dy = 0;
  double _angle = 0;
  bool _dismissed = false;
  _SwipeOverlay _overlay = _SwipeOverlay.none;

  late final AnimationController _resetController;
  late Animation<Offset> _resetAnimation;

  @override
  void initState() {
    super.initState();
    _resetController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
  }

  @override
  void dispose() {
    _resetController.dispose();
    super.dispose();
  }

  void _onPanUpdate(DragUpdateDetails d) {
    if (_dismissed) return;
    setState(() {
      _dx += d.delta.dx;
      _dy += d.delta.dy;
      _angle = _dx * 0.001;
      if (_dx > 40) {
        _overlay = _SwipeOverlay.approve;
      } else if (_dx < -40) {
        _overlay = _SwipeOverlay.flag;
      } else {
        _overlay = _SwipeOverlay.none;
      }
    });
  }

  void _onPanEnd(DragEndDetails d) {
    if (_dismissed) return;
    final vx = d.velocity.pixelsPerSecond.dx;
    if (_dx > 100 || vx > 800) {
      _dismiss(true);
    } else if (_dx < -100 || vx < -800) {
      _dismiss(false);
    } else {
      _resetPosition();
    }
  }

  void _dismiss(bool approved) {
    setState(() => _dismissed = true);
    final target = approved ? 500.0 : -500.0;
    final start = Offset(_dx, _dy);
    final end = Offset(target, _dy);

    _resetAnimation = Tween<Offset>(begin: start, end: end).animate(
      CurvedAnimation(parent: _resetController, curve: Curves.easeOut),
    );
    _resetController.reset();
    _resetController.forward().then((_) {
      if (approved) {
        widget.onSwipeRight();
      } else {
        widget.onSwipeLeft();
      }
    });

    _resetAnimation.addListener(() {
      setState(() {
        _dx = _resetAnimation.value.dx;
        _dy = _resetAnimation.value.dy;
        _angle = _dx * 0.001;
      });
    });
  }

  void _resetPosition() {
    final start = Offset(_dx, _dy);
    _resetAnimation = Tween<Offset>(begin: start, end: Offset.zero).animate(
      CurvedAnimation(parent: _resetController, curve: Curves.elasticOut),
    );
    _resetController.reset();
    _resetController.forward();
    _resetAnimation.addListener(() {
      setState(() {
        _dx = _resetAnimation.value.dx;
        _dy = _resetAnimation.value.dy;
        _angle = _dx * 0.001;
        _overlay = _SwipeOverlay.none;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final q = widget.question;
    final tier = widget.tier;

    return GestureDetector(
      onPanUpdate: _onPanUpdate,
      onPanEnd: _onPanEnd,
      child: Transform.translate(
        offset: Offset(_dx, _dy),
        child: Transform.rotate(
          angle: _angle,
          child: Stack(
            children: [
              _buildCard(q, tier),
              if (_overlay == _SwipeOverlay.approve)
                Positioned(
                  top: 30,
                  left: 24,
                  child: Transform.rotate(
                    angle: -0.3,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        border: Border.all(
                            color: KiwiColors.kiwiGreen, width: 3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'APPROVE',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w900,
                          color: KiwiColors.kiwiGreen,
                        ),
                      ),
                    ),
                  ),
                ),
              if (_overlay == _SwipeOverlay.flag)
                Positioned(
                  top: 30,
                  right: 24,
                  child: Transform.rotate(
                    angle: 0.3,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        border: Border.all(
                            color: KiwiColors.coral, width: 3),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'FLAG',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w900,
                          color: KiwiColors.coral,
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCard(Map<String, dynamic> q, KiwiTier tier) {
    final stem = q['stem'] as String? ?? '';
    final choices = (q['choices'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];
    final correctAnswer = q['correct_answer'] as int? ?? -1;
    final hint = q['hint'] as String?;
    final difficulty = q['difficulty_tier'] as String? ?? 'unknown';
    final topic = q['topic_name'] as String? ?? q['topic'] as String? ?? '';
    final mode = q['interaction_mode'] as String? ?? 'mcq';
    final questionId = q['question_id'] as String? ?? '';
    final hasVisual = q['visual_svg'] != null ||
        (q['visual_alt'] as String?)?.isNotEmpty == true;

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Meta row
            Row(
              children: [
                _chip(difficulty, _difficultyColor(difficulty), tier),
                const SizedBox(width: 8),
                _chip(mode, tier.colors.primary, tier),
                const Spacer(),
                if (hasVisual)
                  Icon(Icons.image_outlined,
                      size: 18, color: tier.colors.textMuted),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              topic,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: tier.colors.primary,
              ),
            ),
            const SizedBox(height: 14),

            // Visual
            if (questionId.isNotEmpty && hasVisual) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  width: double.infinity,
                  constraints: const BoxConstraints(maxHeight: 180),
                  color: KiwiColors.visualYellowBg,
                  child: AuthedSvg(
                    url: '${widget.apiBaseUrl}/v2/questions/$questionId/visual',
                    fit: BoxFit.contain,
                    placeholderBuilder: (_) => const Center(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 14),
            ],

            // Stem
            Text(
              stem,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: tier.colors.textPrimary,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 16),

            // Choices
            for (int i = 0; i < choices.length; i++)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 8),
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: i == correctAnswer
                      ? KiwiColors.correctBg
                      : tier.colors.background,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: i == correctAnswer
                        ? KiwiColors.correct
                        : tier.colors.topicCardBorder,
                    width: i == correctAnswer ? 2 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 26,
                      height: 26,
                      decoration: BoxDecoration(
                        color: i == correctAnswer
                            ? KiwiColors.correct
                            : tier.colors.primary.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          String.fromCharCode(65 + i),
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: i == correctAnswer
                                ? Colors.white
                                : tier.colors.textSecondary,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        choices[i],
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: i == correctAnswer
                              ? FontWeight.w700
                              : FontWeight.w500,
                          color: tier.colors.textPrimary,
                        ),
                      ),
                    ),
                    if (i == correctAnswer)
                      const Icon(Icons.check_circle,
                          size: 20, color: KiwiColors.correct),
                  ],
                ),
              ),

            // Hint
            if (hint != null && hint.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiPrimaryLight,
                  borderRadius: BorderRadius.circular(10),
                  border:
                      Border.all(color: KiwiColors.amber.withOpacity(0.3)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('\u{1F4A1}', style: TextStyle(fontSize: 16)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        hint,
                        style: TextStyle(
                          fontSize: 13,
                          color: tier.colors.textSecondary,
                          height: 1.4,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 20),
            // Swipe hints
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(Icons.arrow_back, size: 16, color: KiwiColors.coral),
                    const SizedBox(width: 4),
                    Text('Flag',
                        style: TextStyle(
                            fontSize: 12, color: KiwiColors.coral)),
                  ],
                ),
                Row(
                  children: [
                    Text('Approve',
                        style: TextStyle(
                            fontSize: 12, color: KiwiColors.kiwiGreen)),
                    const SizedBox(width: 4),
                    Icon(Icons.arrow_forward,
                        size: 16, color: KiwiColors.kiwiGreen),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _chip(String label, Color color, KiwiTier tier) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }

  Color _difficultyColor(String tier) {
    switch (tier.toLowerCase()) {
      case 'easy':
        return KiwiColors.kiwiGreen;
      case 'medium':
        return KiwiColors.amber;
      case 'hard':
        return KiwiColors.coral;
      default:
        return KiwiColors.textMuted;
    }
  }
}

enum _SwipeOverlay { none, approve, flag }

class _FlagSheet extends StatefulWidget {
  final void Function(String flagType, String comment,
      {String? correctAnswer}) onSubmit;

  const _FlagSheet({required this.onSubmit});

  @override
  State<_FlagSheet> createState() => _FlagSheetState();
}

class _FlagSheetState extends State<_FlagSheet> {
  String? _selectedCategory;
  final _commentController = TextEditingController();
  final _correctAnswerController = TextEditingController();
  final _newHintController = TextEditingController();

  static const _categories = [
    'Wrong Answer',
    'Bad Hint',
    'Bad Stem',
    'Needs Visual',
    'Wrong Difficulty',
    'Duplicate',
    'Other',
  ];

  @override
  void dispose() {
    _commentController.dispose();
    _correctAnswerController.dispose();
    _newHintController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_selectedCategory == null) return;
    String comment = _commentController.text.trim();
    String? correctAnswer;

    if (_selectedCategory == 'Wrong Answer') {
      correctAnswer = _correctAnswerController.text.trim();
      if (correctAnswer.isEmpty) correctAnswer = null;
    }
    if (_selectedCategory == 'Bad Hint') {
      final newHint = _newHintController.text.trim();
      if (newHint.isNotEmpty) {
        comment = comment.isEmpty ? 'New hint: $newHint' : '$comment | New hint: $newHint';
      }
    }

    widget.onSubmit(
      _selectedCategory!,
      comment,
      correctAnswer: correctAnswer,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: KiwiColors.pathLocked,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text('Flag Question',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _categories.map((cat) {
                final selected = _selectedCategory == cat;
                return ChoiceChip(
                  label: Text(cat),
                  selected: selected,
                  selectedColor: KiwiColors.kiwiPrimary.withOpacity(0.15),
                  onSelected: (_) =>
                      setState(() => _selectedCategory = cat),
                );
              }).toList(),
            ),
            if (_selectedCategory == 'Wrong Answer') ...[
              const SizedBox(height: 14),
              TextField(
                controller: _correctAnswerController,
                decoration: InputDecoration(
                  labelText: 'Correct answer',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12)),
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
              ),
            ],
            if (_selectedCategory == 'Bad Hint') ...[
              const SizedBox(height: 14),
              TextField(
                controller: _newHintController,
                maxLines: 2,
                decoration: InputDecoration(
                  labelText: 'Suggested new hint',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12)),
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                ),
              ),
            ],
            const SizedBox(height: 14),
            TextField(
              controller: _commentController,
              maxLines: 2,
              decoration: InputDecoration(
                labelText: 'Additional comment (optional)',
                border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12)),
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              ),
            ),
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [KiwiColors.coral, KiwiColors.kiwiPrimaryDark],
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: ElevatedButton(
                  onPressed: _selectedCategory != null ? _submit : null,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    disabledBackgroundColor: Colors.transparent,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                  ),
                  child: const Text(
                    'Submit Flag',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
