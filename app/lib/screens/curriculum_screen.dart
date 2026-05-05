import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';
import '../services/api_client.dart';
import '../services/companion_service.dart';

/// Curriculum tab — multi-curriculum chapter browser.
///
/// Sub-tabs: Cambridge, NCERT, Singapore, ICSE.
/// Loads chapters from API per curriculum + grade combination.
class CurriculumScreen extends StatefulWidget {
  final String userId;
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;
  final void Function(String topicId, String topicName, {String? curriculum}) onChapterTap;
  final CompanionService? companionService;

  const CurriculumScreen({
    super.key,
    required this.userId,
    required this.selectedGrade,
    required this.onGradeChanged,
    required this.onChapterTap,
    this.companionService,
  });

  @override
  State<CurriculumScreen> createState() => _CurriculumScreenState();
}

class _CurriculumScreenState extends State<CurriculumScreen> {
  static const _curricula = [
    _CurriculumInfo(id: 'cambridge', label: 'Cambridge', icon: Icons.school_outlined),
    _CurriculumInfo(id: 'ncert', label: 'NCERT', icon: Icons.menu_book_outlined),
    _CurriculumInfo(id: 'singapore', label: 'Singapore', icon: Icons.auto_stories_outlined),
    _CurriculumInfo(id: 'icse', label: 'ICSE', icon: Icons.library_books_outlined),
  ];

  String _selectedCurriculum = 'cambridge';
  List<Map<String, dynamic>> _chapters = [];
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadChapters();
  }

  @override
  void didUpdateWidget(covariant CurriculumScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedGrade != widget.selectedGrade) {
      _loadChapters();
    }
  }

  Future<void> _loadChapters() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final chapters = await ApiClient().getChapters(
        curriculum: _selectedCurriculum,
        grade: widget.selectedGrade,
      );
      if (mounted) {
        setState(() {
          _chapters = chapters;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  void _onCurriculumChanged(String id) {
    if (id == _selectedCurriculum) return;
    setState(() {
      _selectedCurriculum = id;
    });
    _loadChapters();
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ---- Header ----
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Text(
                'Curriculum',
                style: TextStyle(
                  fontSize: typo.headlineSize,
                  fontWeight: typo.headlineWeight,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),
            const SizedBox(height: 4),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Text(
                'Browse chapters by curriculum',
                style: TextStyle(
                  fontSize: typo.bodySize,
                  color: colors.textSecondary,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),
            const SizedBox(height: 12),

            // ---- Grade selector ----
            SizedBox(
              height: 40,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: 6,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final grade = index + 1;
                  final isSelected = grade == widget.selectedGrade;
                  return _GradeChip(
                    grade: grade,
                    isSelected: isSelected,
                    tier: tier,
                    onTap: () => widget.onGradeChanged(grade),
                  );
                },
              ),
            ),
            const SizedBox(height: 12),

            // ---- Curriculum chips ----
            SizedBox(
              height: 44,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: _curricula.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, index) {
                  final info = _curricula[index];
                  final isSelected = info.id == _selectedCurriculum;
                  return _CurriculumChip(
                    info: info,
                    isSelected: isSelected,
                    tier: tier,
                    onTap: () => _onCurriculumChanged(info.id),
                  );
                },
              ),
            ),
            const SizedBox(height: 12),

            // ---- Chapter list ----
            Expanded(
              child: _buildBody(tier),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody(KiwiTier tier) {
    if (_loading) {
      return Center(
        child: CircularProgressIndicator(
          color: tier.colors.primary,
          strokeWidth: 3,
        ),
      );
    }

    if (_error != null) {
      return _ErrorView(
        error: _error!,
        tier: tier,
        onRetry: _loadChapters,
      );
    }

    if (_chapters.isEmpty) {
      return _EmptyView(
        curriculum: _selectedCurriculum,
        grade: widget.selectedGrade,
        tier: tier,
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      itemCount: _chapters.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final chapter = _chapters[index];
        return _ChapterCard(
          chapter: chapter,
          index: index,
          tier: tier,
          onTap: () {
            final topicId = chapter['id']?.toString() ??
                chapter['topic_id']?.toString() ??
                '${_selectedCurriculum}-g${widget.selectedGrade}-ch${index + 1}';
            final name = chapter['name']?.toString() ??
                chapter['title']?.toString() ??
                'Chapter ${index + 1}';
            widget.onChapterTap(topicId, name, curriculum: _selectedCurriculum);
          },
        );
      },
    );
  }
}

// =============================================================================
// Curriculum info
// =============================================================================
class _CurriculumInfo {
  final String id;
  final String label;
  final IconData icon;

  const _CurriculumInfo({
    required this.id,
    required this.label,
    required this.icon,
  });
}

// =============================================================================
// Grade chip
// =============================================================================
class _GradeChip extends StatelessWidget {
  final int grade;
  final bool isSelected;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _GradeChip({
    required this.grade,
    required this.isSelected,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? colors.primary : colors.cardBg,
          borderRadius: BorderRadius.circular(tier.shape.chipRadius),
          border: Border.all(
            color: isSelected ? colors.primaryDark : colors.topicCardBorder,
            width: isSelected ? 1.5 : 1,
          ),
        ),
        child: Text(
          'G$grade',
          style: TextStyle(
            fontSize: typo.chipSize,
            fontWeight: FontWeight.w700,
            color: isSelected ? Colors.white : colors.textPrimary,
            fontFamily: typo.fontFamily,
          ),
        ),
      ),
    );
  }
}

// =============================================================================
// Curriculum chip
// =============================================================================
class _CurriculumChip extends StatelessWidget {
  final _CurriculumInfo info;
  final bool isSelected;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _CurriculumChip({
    required this.info,
    required this.isSelected,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? colors.primary : colors.cardBg,
          borderRadius: BorderRadius.circular(tier.shape.chipRadius),
          border: Border.all(
            color: isSelected ? colors.primaryDark : colors.topicCardBorder,
            width: isSelected ? 1.5 : 1,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: colors.primary.withOpacity(0.2),
                    blurRadius: 6,
                    offset: const Offset(0, 2),
                  ),
                ]
              : [],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              info.icon,
              size: 18,
              color: isSelected ? Colors.white : colors.textSecondary,
            ),
            const SizedBox(width: 6),
            Text(
              info.label,
              style: TextStyle(
                fontSize: typo.chipSize,
                fontWeight: FontWeight.w600,
                color: isSelected ? Colors.white : colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Chapter card
// =============================================================================
class _ChapterCard extends StatelessWidget {
  final Map<String, dynamic> chapter;
  final int index;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _ChapterCard({
    required this.chapter,
    required this.index,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    final name = chapter['name']?.toString() ??
        chapter['title']?.toString() ??
        'Chapter ${index + 1}';
    final questionCount = chapter['question_count'] as int? ??
        chapter['num_questions'] as int? ??
        0;
    final completed = chapter['completed'] as int? ??
        chapter['questions_done'] as int? ??
        0;
    final fraction = questionCount > 0
        ? (completed / questionCount).clamp(0.0, 1.0)
        : 0.0;

    // Pick a gradient from the candy palette for visual variety.
    final gradientPair =
        KiwiColors.topicGradients[index % KiwiColors.topicGradients.length];

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: shape.cardPadding,
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(color: colors.topicCardBorder, width: 1),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.04),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            // Color accent bar
            Container(
              width: 6,
              height: 52,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: gradientPair,
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
                borderRadius: BorderRadius.circular(3),
              ),
            ),
            const SizedBox(width: 12),

            // Chapter info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: TextStyle(
                      fontSize: typo.topicNameSize,
                      fontWeight: FontWeight.w600,
                      color: colors.textPrimary,
                      fontFamily: typo.fontFamily,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 6),
                  // Stats
                  Row(
                    children: [
                      Icon(Icons.quiz_outlined,
                          size: 14, color: colors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        '$questionCount questions',
                        style: TextStyle(
                          fontSize: typo.chipSize - 1,
                          color: colors.textMuted,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                      if (completed > 0) ...[
                        const SizedBox(width: 10),
                        Icon(Icons.check_circle_outline,
                            size: 14, color: KiwiColors.kiwiGreen),
                        const SizedBox(width: 4),
                        Text(
                          '$completed done',
                          style: TextStyle(
                            fontSize: typo.chipSize - 1,
                            color: KiwiColors.kiwiGreen,
                            fontFamily: typo.fontFamily,
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 6),
                  // Progress bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: SizedBox(
                      height: 6,
                      child: LinearProgressIndicator(
                        value: fraction,
                        backgroundColor: KiwiColors.backgroundDark,
                        valueColor:
                            AlwaysStoppedAnimation<Color>(gradientPair[0]),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),

            // Arrow
            Icon(
              Icons.chevron_right_rounded,
              color: colors.textMuted,
              size: 24,
            ),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Error view
// =============================================================================
class _ErrorView extends StatelessWidget {
  final String error;
  final KiwiTier tier;
  final VoidCallback onRetry;

  const _ErrorView({
    required this.error,
    required this.tier,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off_outlined, size: 48, color: colors.textMuted),
            const SizedBox(height: 12),
            Text(
              'Could not load chapters',
              style: TextStyle(
                fontSize: typo.bodySize,
                fontWeight: FontWeight.w600,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: typo.chipSize,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 16),
            TextButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
              style: TextButton.styleFrom(foregroundColor: colors.primary),
            ),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Empty view
// =============================================================================
class _EmptyView extends StatelessWidget {
  final String curriculum;
  final int grade;
  final KiwiTier tier;

  const _EmptyView({
    required this.curriculum,
    required this.grade,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('\u{1F4DA}', style: TextStyle(fontSize: 40)),
            const SizedBox(height: 12),
            Text(
              'No chapters yet',
              style: TextStyle(
                fontSize: typo.bodySize,
                fontWeight: FontWeight.w600,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Chapters for ${curriculum[0].toUpperCase()}${curriculum.substring(1)} '
              'Grade $grade are coming soon!',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: typo.chipSize,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
