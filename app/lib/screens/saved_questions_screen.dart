import 'package:flutter/material.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';
import 'question_screen_v2.dart';

/// Saved Questions screen — shows bookmarked questions for later review.
///
/// Fetches paginated bookmarks from the backend, displays each as a card
/// with question stem, topic, difficulty badge, and a remove-bookmark button.
/// Tapping a card navigates to the question for practice.
class SavedQuestionsScreen extends StatefulWidget {
  final String userId;
  final int grade;
  final VoidCallback? onBackToHome;

  const SavedQuestionsScreen({
    super.key,
    required this.userId,
    required this.grade,
    this.onBackToHome,
  });

  @override
  State<SavedQuestionsScreen> createState() => _SavedQuestionsScreenState();
}

class _SavedQuestionsScreenState extends State<SavedQuestionsScreen> {
  final ApiClient _api = ApiClient();

  KiwiTier get _tier => KiwiTier.forGrade(widget.grade);

  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _questions = [];
  int _page = 1;
  int _totalPages = 1;
  int _total = 0;

  @override
  void initState() {
    super.initState();
    _loadBookmarks();
  }

  Future<void> _loadBookmarks() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _api.getBookmarks(widget.userId, page: _page, perPage: 20);
      if (!mounted) return;
      setState(() {
        _questions = List<Map<String, dynamic>>.from(data['questions'] ?? []);
        _total = data['total'] as int? ?? 0;
        _totalPages = data['total_pages'] as int? ?? 1;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _removeBookmark(String questionId) async {
    try {
      await _api.toggleBookmark(widget.userId, questionId);
      if (!mounted) return;
      setState(() {
        _questions.removeWhere((q) => q['id'] == questionId);
        _total = (_total - 1).clamp(0, _total);
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Bookmark removed'),
            duration: Duration(seconds: 1),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to remove bookmark: $e')),
        );
      }
    }
  }

  void _navigateToQuestion(Map<String, dynamic> question) {
    final questionId = question['id'] as String? ?? '';
    final topic = question['topic'] as String? ?? '';
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionScreenV2(
          topicId: topic,
          topicName: topic,
          userId: widget.userId,
          grade: widget.grade,
          sessionPlan: [question],
          onBackToHome: () => Navigator.of(context).pop(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = _tier.colors;
    final typo = _tier.typography;
    final shape = _tier.shape;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          children: [
            // Top bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: widget.onBackToHome ?? () => Navigator.of(context).maybePop(),
                    child: Container(
                      width: 36,
                      height: 36,
                      decoration: BoxDecoration(
                        color: colors.primary.withOpacity(0.08),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(Icons.arrow_back, size: 20, color: colors.textSecondary),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Text(
                      'Saved Questions',
                      style: TextStyle(
                        fontSize: typo.headlineSize,
                        fontWeight: typo.headlineWeight,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ),
                  if (_total > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: colors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(shape.chipRadius),
                      ),
                      child: Text(
                        '$_total saved',
                        style: TextStyle(
                          fontSize: typo.chipSize,
                          fontWeight: FontWeight.w600,
                          color: colors.primary,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                    ),
                ],
              ),
            ),

            // Content
            Expanded(
              child: _loading
                  ? _buildLoading()
                  : _error != null
                      ? _buildError()
                      : _questions.isEmpty
                          ? _buildEmpty()
                          : _buildList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoading() {
    return Center(
      child: CircularProgressIndicator(color: _tier.colors.primary),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 48, color: _tier.colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Something went wrong',
              style: TextStyle(
                fontSize: _tier.typography.bodySize,
                color: _tier.colors.textPrimary,
                fontFamily: _tier.typography.fontFamily,
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadBookmarks,
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    final colors = _tier.colors;
    final typo = _tier.typography;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.bookmark_outline,
              size: 64,
              color: colors.textMuted.withOpacity(0.5),
            ),
            const SizedBox(height: 20),
            Text(
              'No saved questions yet',
              style: TextStyle(
                fontSize: typo.headlineSize,
                fontWeight: typo.headlineWeight,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 10),
            Text(
              'Tap the bookmark icon on any question to save it here',
              style: TextStyle(
                fontSize: typo.bodySize,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildList() {
    final shape = _tier.shape;
    return RefreshIndicator(
      color: _tier.colors.primary,
      onRefresh: _loadBookmarks,
      child: ListView.builder(
        padding: EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        itemCount: _questions.length + (_page < _totalPages ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _questions.length) {
            return _buildLoadMore();
          }
          final q = _questions[index];
          return _BookmarkCard(
            question: q,
            tier: _tier,
            onTap: () => _navigateToQuestion(q),
            onRemove: () => _removeBookmark(q['id'] as String? ?? ''),
          );
        },
      ),
    );
  }

  Widget _buildLoadMore() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Center(
        child: TextButton(
          onPressed: () {
            setState(() => _page++);
            _loadBookmarks();
          },
          child: Text(
            'Load more',
            style: TextStyle(color: _tier.colors.primary),
          ),
        ),
      ),
    );
  }
}

/// Card for a single bookmarked question.
class _BookmarkCard extends StatelessWidget {
  final Map<String, dynamic> question;
  final KiwiTier tier;
  final VoidCallback onTap;
  final VoidCallback onRemove;

  const _BookmarkCard({
    required this.question,
    required this.tier,
    required this.onTap,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    final stem = question['stem'] as String? ?? '';
    final topic = question['topic'] as String? ?? '';
    final difficulty = question['difficulty_score'] as int? ?? 0;

    // Difficulty label & color
    String diffLabel;
    Color diffColor;
    if (difficulty <= 2) {
      diffLabel = 'Easy';
      diffColor = KiwiColors.kiwiGreen;
    } else if (difficulty <= 4) {
      diffLabel = 'Medium';
      diffColor = KiwiColors.amber;
    } else {
      diffLabel = 'Hard';
      diffColor = KiwiColors.coral;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: shape.cardPadding,
          decoration: BoxDecoration(
            color: colors.cardBg,
            borderRadius: BorderRadius.circular(shape.cardRadius),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Topic + difficulty + remove button
              Row(
                children: [
                  if (topic.isNotEmpty) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: colors.primary.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(shape.chipRadius),
                      ),
                      child: Text(
                        topic,
                        style: TextStyle(
                          fontSize: typo.chipSize - 1,
                          fontWeight: FontWeight.w600,
                          color: colors.primary,
                          fontFamily: typo.fontFamily,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 6),
                  ],
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: diffColor.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(shape.chipRadius),
                    ),
                    child: Text(
                      diffLabel,
                      style: TextStyle(
                        fontSize: typo.chipSize - 1,
                        fontWeight: FontWeight.w600,
                        color: diffColor,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: onRemove,
                    child: Container(
                      width: 30,
                      height: 30,
                      decoration: BoxDecoration(
                        color: colors.primary.withOpacity(0.06),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        Icons.bookmark_remove_outlined,
                        size: 16,
                        color: colors.textMuted,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              // Question stem
              Text(
                stem,
                style: TextStyle(
                  fontSize: typo.bodySize,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                  height: 1.4,
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 8),
              // Tap to practice hint
              Row(
                children: [
                  Icon(Icons.play_circle_outline, size: 14, color: colors.textMuted),
                  const SizedBox(width: 4),
                  Text(
                    'Tap to practice',
                    style: TextStyle(
                      fontSize: typo.chipSize - 1,
                      color: colors.textMuted,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
