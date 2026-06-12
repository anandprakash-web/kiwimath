import 'package:flutter/material.dart';

import '../models/companion.dart';
import '../models/student_levels.dart';
import '../services/api_client.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import 'question_screen_v2.dart';

/// Learning Path v7.0 — "School" tab, curriculum-first.
///
/// Two tabs:
///   - **Chapters** (default) — curriculum chapter tracker (NCERT, ICSE, etc.)
///   - **Learning Path** — adaptive topic progression
///
/// Chapters tab shows school-aligned content. Learning Path shows
/// the adaptive skill progression.
class LearningPathScreen extends StatefulWidget {
  final String userId;
  final int grade;
  final CompanionService? companionService;
  final StudentLevels? studentLevels;
  final bool embedded;
  final String? curriculum;

  const LearningPathScreen({
    super.key,
    required this.userId,
    required this.grade,
    this.companionService,
    this.studentLevels,
    this.embedded = false,
    this.curriculum,
  });

  @override
  State<LearningPathScreen> createState() => _LearningPathScreenState();
}

class _LearningPathScreenState extends State<LearningPathScreen> {
  final ApiClient _api = ApiClient();
  Map<String, dynamic>? _data;
  String? _error;
  bool _loading = true;

  // Chapters state (Syllabus tab)
  List<Map<String, dynamic>>? _chapters;
  bool _chaptersLoading = false;
  String? _chaptersError;

  /// 0 = Chapters (curriculum, default), 1 = Learning Path (adaptive)
  int _activeTab = 0;

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  // Use theme tokens instead of hardcoded colors
  // _orangeStart → KiwiColors.kiwiPrimary
  // _orangeEnd → KiwiColors.pathCurrent
  // _tealDone → KiwiColors.kiwiGreen

  @override
  void initState() {
    super.initState();
    // v7: Default to Chapters tab (school-first)
    _activeTab = 0;
    _load();
    _loadChapters();
  }

  Future<void> _loadChapters() async {
    final cur = widget.curriculum;
    if (cur == null || cur.isEmpty) return;
    setState(() {
      _chaptersLoading = true;
      _chaptersError = null;
    });
    try {
      final chapters = await _api.getChapters(
        curriculum: cur,
        grade: widget.grade,
      );
      if (!mounted) return;
      setState(() {
        _chapters = chapters;
        _chaptersLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      // Never show raw error/JSON to kids
      final raw = e.toString();
      String msg;
      if (raw.contains('SocketException') || raw.contains('Connection') ||
          raw.contains('TimeoutException')) {
        msg = "Can't reach our servers. Check your internet and try again.";
      } else {
        msg = 'Could not load chapters. Try again later.';
      }
      setState(() {
        _chaptersError = msg;
        _chaptersLoading = false;
      });
    }
  }

  @override
  void didUpdateWidget(covariant LearningPathScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.grade != oldWidget.grade) {
      _load();
      _loadChapters();
    }
    if (widget.curriculum != oldWidget.curriculum) {
      _loadChapters();
    }
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _api.getLearningPath(
        userId: widget.userId,
        grade: widget.grade,
      );
      if (!mounted) return;
      setState(() {
        _data = data;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      // Never leak raw JSON/stack traces — always show kid-friendly messages
      String friendlyError;
      final raw = e.toString();
      if (raw.contains('422') || raw.contains('validation') || raw.contains('404')) {
        friendlyError =
            "We're still building the learning path for Grade ${widget.grade}. "
            "Try Smart Practice for now!";
      } else if (raw.contains('SocketException') || raw.contains('Connection') ||
                 raw.contains('TimeoutException') || raw.contains('ClientException')) {
        friendlyError = "Can't reach our servers right now. Check your internet.";
      } else {
        friendlyError = "Something didn't work. Give it another try!";
      }
      setState(() {
        _error = friendlyError;
        _loading = false;
      });
    }
  }

  void _startStop(Map<String, dynamic> stop) {
    final topicId = stop['topic_id'] as String?;
    final topicName = stop['topic_name'] as String? ?? 'Practice';
    if (topicId == null) return;

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionScreenV2(
          topicId: topicId,
          topicName: topicName,
          userId: widget.userId,
          grade: widget.grade,
          companionService: widget.companionService,
          onBackToHome: () {
            Navigator.of(context).pop();
            _load();
          },
        ),
      ),
    );
  }

  bool get _hasSyllabus =>
      widget.curriculum != null && widget.curriculum!.isNotEmpty;

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.grade);
    return Scaffold(
      backgroundColor: tier.colors.background,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(tier),
            _buildTabs(tier),
            Expanded(child: _buildBody(tier)),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(KiwiTier tier) {
    final typo = tier.typography;
    return Padding(
      padding: KiwiSpacing.sectionPadding,
      child: Row(
        children: [
          Text(
            'School',
            style: TextStyle(
              fontSize: typo.headlineSize,
              fontWeight: typo.headlineWeight,
              color: tier.colors.textPrimary,
              fontFamily: typo.fontFamily,
            ),
          ),
          const Spacer(),
          if (_loading)
            const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          else
            GestureDetector(
              onTap: _load,
              child: Icon(
                Icons.refresh_rounded,
                size: 22,
                color: tier.colors.textPrimary.withOpacity(0.5),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTabs(KiwiTier tier) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(KiwiSpacing.lg, KiwiSpacing.md, KiwiSpacing.lg, KiwiSpacing.sm),
      child: Container(
        height: 36,
        decoration: BoxDecoration(
          color: tier.colors.backgroundDark,
          borderRadius: BorderRadius.circular(tier.shape.chipRadius),
        ),
        child: Row(
          children: [
            _buildTab(label: 'Chapters', index: 0, tier: tier),
            _buildTab(label: 'Learning Path', index: 1, tier: tier),
          ],
        ),
      ),
    );
  }

  Widget _buildTab({
    required String label,
    required int index,
    required KiwiTier tier,
  }) {
    final isActive = _activeTab == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _activeTab = index),
        child: Container(
          margin: const EdgeInsets.all(3),
          decoration: BoxDecoration(
            color: isActive ? tier.colors.cardBg : Colors.transparent,
            borderRadius: BorderRadius.circular(tier.shape.chipRadius - 2),
            boxShadow: isActive
                ? [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.06),
                      blurRadius: 4,
                      offset: const Offset(0, 1),
                    ),
                  ]
                : null,
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              fontSize: tier.typography.chipSize,
              fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
              color: isActive
                  ? tier.colors.textPrimary
                  : tier.colors.textPrimary.withOpacity(0.5),
              fontFamily: tier.typography.fontFamily,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody(KiwiTier tier) {
    // Chapters tab (school curriculum) — default
    if (_activeTab == 0 && _hasSyllabus) {
      return _buildSyllabusTab(tier);
    }
    if (_activeTab == 0 && !_hasSyllabus) {
      return _buildNoSyllabusPlaceholder(tier);
    }

    // Learning Path tab (adaptive)
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return _ErrorView(message: _error!, onRetry: _load);
    }
    final data = _data;
    if (data == null) {
      return Center(
        child: Text(
          'No learning path yet. Try Smart Practice on the Home tab!',
          style: TextStyle(
            fontSize: tier.typography.bodySize,
            color: tier.colors.textPrimary.withOpacity(0.5),
          ),
        ),
      );
    }

    // Defensive: ensure 'path' is a list of maps, never raw JSON strings
    List<Map<String, dynamic>> path;
    try {
      path = (data['path'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .toList();
    } catch (_) {
      path = [];
    }

    if (path.isEmpty) {
      return Center(
        child: Text(
          'No learning path yet. Try Smart Practice on the Home tab!',
          style: TextStyle(
            fontSize: tier.typography.bodySize,
            color: tier.colors.textPrimary.withOpacity(0.5),
          ),
        ),
      );
    }

    int currentIdx = path.indexWhere(
      (s) => (s['mastery_label'] as String? ?? '') != 'mastered',
    );
    if (currentIdx < 0) currentIdx = 0;

    final masteredCount =
        path.where((s) => s['mastery_label'] == 'mastered').length;

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 4, 18, 28),
        children: [
          _buildProgressBar(masteredCount, path.length, tier),
          const SizedBox(height: 14),
          for (int i = 0; i < path.length; i++)
            _PathStopCard(
              stop: path[i],
              index: i,
              isFirst: i == 0,
              isLast: i == path.length - 1,
              isCurrent: i == currentIdx,
              onStart: i == currentIdx ? () => _startStop(path[i]) : null,
              studentLevels: widget.studentLevels,
              tier: tier,
            ),
        ],
      ),
    );
  }

  Widget _buildNoSyllabusPlaceholder(KiwiTier tier) {
    final typo = tier.typography;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(KiwiSpacing.xxl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.school_rounded, size: 48,
                color: tier.colors.primary.withOpacity(0.4)),
            const SizedBox(height: KiwiSpacing.lg),
            Text(
              'No school board selected',
              style: TextStyle(
                fontSize: typo.bodySize,
                fontWeight: FontWeight.w700,
                color: tier.colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            const SizedBox(height: KiwiSpacing.sm),
            Text(
              'Select your curriculum (NCERT, ICSE, etc.) in settings '
              'to see school chapters here.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: typo.chipSize,
                color: tier.colors.textPrimary.withOpacity(0.5),
                height: 1.4,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSyllabusTab(KiwiTier tier) {
    if (_chaptersLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_chaptersError != null) {
      return _ErrorView(message: _chaptersError!, onRetry: _loadChapters);
    }
    final chapters = _chapters;
    if (chapters == null || chapters.isEmpty) {
      final curLabel = (widget.curriculum ?? '').toUpperCase();
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.menu_book_rounded, size: 40,
                  color: tier.colors.textPrimary.withOpacity(0.3)),
              const SizedBox(height: 12),
              Text(
                '$curLabel chapters coming soon',
                style: TextStyle(fontSize: tier.typography.bodySize, fontWeight: FontWeight.w700,
                    color: tier.colors.textPrimary.withOpacity(0.7)),
              ),
              const SizedBox(height: 6),
              Text(
                'Chapter-wise content is being prepared.\nUse Learning Path tab for adaptive learning!',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: tier.typography.chipSize,
                    color: tier.colors.textPrimary.withOpacity(0.5), height: 1.4),
              ),
            ],
          ),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(18, 4, 18, 28),
      children: [
        // Syllabus info header
        Container(
          padding: const EdgeInsets.all(12),
          margin: const EdgeInsets.only(bottom: 14),
          decoration: BoxDecoration(
            color: KiwiColors.kiwiPrimaryLight,
            borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
            border: Border.all(color: KiwiColors.kiwiPrimary.withOpacity(0.2)),
          ),
          child: Row(
            children: [
              const Icon(Icons.info_outline_rounded, size: 16,
                  color: KiwiColors.kiwiPrimaryDark),
              const SizedBox(width: KiwiSpacing.sm),
              Expanded(
                child: Text(
                  'Your ${widget.curriculum?.toUpperCase() ?? ""} school chapters. '
                  'Practice each chapter to build mastery!',
                  style: TextStyle(
                    fontSize: tier.typography.chipSize,
                    color: KiwiColors.kiwiPrimaryDark,
                  ),
                ),
              ),
            ],
          ),
        ),
        for (int i = 0; i < chapters.length; i++) ...[
          _ChapterCard(
            chapter: chapters[i],
            index: i,
            tier: tier,
            onTap: () => _startChapter(chapters[i]),
          ),
          if (i < chapters.length - 1) const SizedBox(height: 10),
        ],
      ],
    );
  }

  Widget _buildProgressBar(int mastered, int total, KiwiTier tier) {
    final fraction = total > 0 ? mastered / total : 0.0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              '$mastered of $total topics mastered',
              style: TextStyle(
                fontSize: tier.typography.chipSize,
                fontWeight: FontWeight.w600,
                color: tier.colors.textPrimary.withOpacity(0.5),
              ),
            ),
            const Spacer(),
            Text(
              '${(fraction * 100).round()}%',
              style: TextStyle(
                fontSize: tier.typography.chipSize,
                fontWeight: FontWeight.w700,
                color: tier.colors.primary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: LinearProgressIndicator(
            value: fraction,
            minHeight: 6,
            backgroundColor: tier.colors.backgroundDark,
            valueColor: AlwaysStoppedAnimation<Color>(tier.colors.primary),
          ),
        ),
      ],
    );
  }

  void _startChapter(Map<String, dynamic> chapter) {
    final chapterName = chapter['name'] as String? ?? 'Chapter';
    final chapterId = chapter['id'] as String? ?? '';
    final cur = widget.curriculum ?? 'ncert';
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionScreenV2(
          topicId: chapterId,
          topicName: chapterName,
          userId: widget.userId,
          grade: widget.grade,
          companionService: widget.companionService,
          chapter: chapterName,
          curriculum: cur,
          onBackToHome: () {
            Navigator.of(context).pop();
            _load();
            _loadChapters();
          },
        ),
      ),
    );
  }
}

// =============================================================================
// Chapter card for school tab — engaging, colorful, progress-aware
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

  // Topic emojis for visual variety
  static const _topicEmojis = [
    '\u{1F522}', // numbers
    '\u{2795}',  // addition
    '\u{2796}',  // subtraction
    '\u{2716}',  // multiplication
    '\u{2797}',  // division
    '\u{1F4D0}', // geometry
    '\u{1F4CF}', // measurement
    '\u{1F4CA}', // data
    '\u{1F9E9}', // patterns/puzzles
    '\u{1F4B0}', // money
    '\u{23F0}',  // time
    '\u{1F354}', // fractions
    '\u{1F4C8}', // charts
    '\u{1F3AF}', // target/accuracy
    '\u{2B50}',  // star
    '\u{1F680}', // rocket
  ];

  static const _accentColors = [
    KiwiColors.kiwiPrimary, KiwiColors.sky,
    KiwiColors.indigo, KiwiColors.teal,
    KiwiColors.coral, KiwiColors.teal,
    KiwiColors.indigo, KiwiColors.coral,
  ];

  @override
  Widget build(BuildContext context) {
    final name = chapter['name'] as String? ?? 'Chapter ${index + 1}';
    final questionCount = chapter['question_count'] as int? ?? 0;
    final topics = (chapter['topics'] as List<dynamic>?)?.cast<String>() ?? [];
    final progress = (chapter['progress'] as num?)?.toDouble() ?? 0.0;
    final isComplete = progress >= 1.0;

    final accentColor = _accentColors[index % _accentColors.length];
    final emoji = _topicEmojis[index % _topicEmojis.length];

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: tier.shape.cardPadding,
        decoration: BoxDecoration(
          color: KiwiColors.cardBg,
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          border: Border.all(
            color: isComplete ? KiwiColors.kiwiGreen.withOpacity(0.3) : accentColor.withOpacity(0.15),
            width: isComplete ? 1.5 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: accentColor.withOpacity(0.06),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            // Emoji icon in colored circle
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [accentColor.withOpacity(0.15), accentColor.withOpacity(0.08)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(tier.shape.buttonRadius - 5),
              ),
              alignment: Alignment.center,
              child: Text(emoji, style: const TextStyle(fontSize: 22)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Chapter number + name
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: 1),
                        decoration: BoxDecoration(
                          color: accentColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(KiwiSpacing.sm),
                        ),
                        child: Text(
                          'Ch ${index + 1}',
                          style: TextStyle(
                            fontSize: tier.typography.chipSize - 2,
                            fontWeight: FontWeight.w700,
                            color: accentColor,
                            fontFamily: tier.typography.fontFamily,
                          ),
                        ),
                      ),
                      const SizedBox(width: KiwiSpacing.sm),
                      if (isComplete)
                        const Icon(Icons.check_circle, size: 14, color: KiwiColors.kiwiGreen),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    name,
                    style: TextStyle(
                      fontSize: tier.typography.bodySize,
                      fontWeight: FontWeight.w700,
                      color: tier.colors.textPrimary,
                      fontFamily: tier.typography.fontFamily,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (topics.isNotEmpty) ...[
                    const SizedBox(height: 3),
                    Text(
                      topics.take(3).join(' \u{2022} '),
                      style: TextStyle(
                        fontSize: tier.typography.chipSize - 2,
                        color: tier.colors.textPrimary.withOpacity(0.45),
                        fontFamily: tier.typography.fontFamily,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  // Progress bar
                  if (progress > 0 && !isComplete) ...[
                    const SizedBox(height: KiwiSpacing.sm),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(KiwiSpacing.xs),
                      child: LinearProgressIndicator(
                        value: progress,
                        minHeight: 4,
                        backgroundColor: accentColor.withOpacity(0.1),
                        valueColor: AlwaysStoppedAnimation<Color>(accentColor),
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: KiwiSpacing.sm),
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '$questionCount',
                  style: TextStyle(
                    fontSize: tier.typography.bodySize,
                    fontWeight: FontWeight.w800,
                    color: accentColor,
                    fontFamily: tier.typography.fontFamily,
                  ),
                ),
                Text(
                  'Qs',
                  style: TextStyle(
                    fontSize: tier.typography.chipSize - 2,
                    fontWeight: FontWeight.w500,
                    color: accentColor.withOpacity(0.5),
                    fontFamily: tier.typography.fontFamily,
                  ),
                ),
              ],
            ),
            const SizedBox(width: 4),
            Icon(Icons.play_circle_filled_rounded,
                size: 24, color: accentColor.withOpacity(0.6)),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Path stop card — visual timeline with topic icons and progress
// =============================================================================

class _PathStopCard extends StatelessWidget {
  final Map<String, dynamic> stop;
  final int index;
  final bool isFirst;
  final bool isLast;
  final bool isCurrent;
  final VoidCallback? onStart;
  final StudentLevels? studentLevels;
  final KiwiTier tier;

  const _PathStopCard({
    required this.stop,
    required this.index,
    required this.isFirst,
    required this.isLast,
    required this.isCurrent,
    required this.onStart,
    required this.tier,
    this.studentLevels,
  });

  // Use KiwiColors tokens instead of local constants
  static const _orangeStart = KiwiColors.kiwiPrimary;
  static const _tealDone = KiwiColors.kiwiGreen;

  // Topic-specific emojis for visual identity
  static const _topicEmojis = {
    'counting': '\u{1F522}',
    'arithmetic': '\u{2795}',
    'patterns': '\u{1F9E9}',
    'logic': '\u{1F9E0}',
    'spatial': '\u{1F4D0}',
    'shapes': '\u{1F4D0}',
    'word': '\u{1F4D6}',
    'puzzles': '\u{1F3B2}',
    'fractions': '\u{1F354}',
    'geometry': '\u{1F4CF}',
    'measurement': '\u{1F4CF}',
    'data': '\u{1F4CA}',
  };

  String _emojiForTopic(String topicId) {
    for (final entry in _topicEmojis.entries) {
      if (topicId.toLowerCase().contains(entry.key)) return entry.value;
    }
    return '\u{2B50}'; // default star
  }

  Color _levelBadgeColor(int level) {
    if (level >= 7) return KiwiColors.indigo;
    if (level >= 4) return KiwiColors.sky;
    return KiwiColors.kiwiGreenDark;
  }

  Color _levelBadgeBg(int level) {
    if (level >= 7) return KiwiColors.indigo.withOpacity(0.1);
    if (level >= 4) return KiwiColors.visualBlueBg;
    return KiwiColors.kiwiGreenLight;
  }

  @override
  Widget build(BuildContext context) {
    final mastery = (stop['mastery_label'] as String?) ?? 'learning';
    final isMastered = mastery == 'mastered';
    final topicName = (stop['topic_name'] as String?) ?? 'Topic';
    final topicId = (stop['topic_id'] as String?) ?? '';
    final qCount = (stop['questions_to_attempt'] as num?)?.toInt() ?? 5;

    int level = (stop['target_difficulty'] as num?)?.toInt() ?? 1;
    if (studentLevels != null) {
      final topicLevel = studentLevels!.topics.where((t) => t.topicId == topicId);
      if (topicLevel.isNotEmpty) {
        level = topicLevel.first.currentLevel;
      }
    }

    final emoji = _emojiForTopic(topicId);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline rail
          SizedBox(
            width: 36,
            child: Column(
              children: [
                Expanded(
                  flex: 1,
                  child: Container(
                    width: 3,
                    decoration: BoxDecoration(
                      gradient: isFirst
                          ? null
                          : LinearGradient(
                              begin: Alignment.topCenter,
                              end: Alignment.bottomCenter,
                              colors: isMastered
                                  ? [_tealDone, _tealDone]
                                  : [KiwiColors.pathLocked, KiwiColors.pathLocked],
                            ),
                      color: isFirst ? Colors.transparent : null,
                    ),
                  ),
                ),
                // Node
                Container(
                  width: isCurrent ? 32 : 26,
                  height: isCurrent ? 32 : 26,
                  decoration: BoxDecoration(
                    color: isMastered
                        ? _tealDone
                        : isCurrent ? _orangeStart : KiwiColors.pathLocked,
                    shape: BoxShape.circle,
                    boxShadow: isCurrent
                        ? [BoxShadow(color: _orangeStart.withOpacity(0.3), blurRadius: 10, spreadRadius: 2)]
                        : isMastered
                            ? [BoxShadow(color: _tealDone.withOpacity(0.2), blurRadius: 6)]
                            : null,
                  ),
                  alignment: Alignment.center,
                  child: isMastered
                      ? const Icon(Icons.check_rounded, color: Colors.white, size: 16)
                      : isCurrent
                          ? const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 18)
                          : Text(
                              '${index + 1}',
                              style: TextStyle(
                                fontSize: tier.typography.chipSize,
                                fontWeight: FontWeight.w800,
                                color: KiwiColors.textMuted,
                              ),
                            ),
                ),
                Expanded(
                  flex: 5,
                  child: Container(
                    width: 3,
                    color: isLast ? Colors.transparent : KiwiColors.pathLocked,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          // Card
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 10, top: 2),
              child: Container(
                padding: tier.shape.cardPadding,
                decoration: BoxDecoration(
                  color: isCurrent ? KiwiColors.cream : KiwiColors.cardBg,
                  borderRadius: BorderRadius.circular(tier.shape.cardRadius),
                  border: Border.all(
                    color: isCurrent ? _orangeStart.withOpacity(0.5) : KiwiColors.pathLocked,
                    width: isCurrent ? 1.5 : 1,
                  ),
                  boxShadow: isCurrent
                      ? [BoxShadow(color: _orangeStart.withOpacity(0.08), blurRadius: 12, offset: const Offset(0, 3))]
                      : null,
                ),
                child: Opacity(
                  opacity: (isMastered || isCurrent) ? 1.0 : 0.5,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          // Topic emoji
                          Text(emoji, style: TextStyle(fontSize: tier.typography.headlineSize)),
                          const SizedBox(width: KiwiSpacing.sm),
                          Expanded(
                            child: Text(
                              topicName,
                              style: TextStyle(
                                fontSize: tier.typography.bodySize,
                                fontWeight: FontWeight.w700,
                                color: KiwiColors.textDark,
                              ),
                            ),
                          ),
                          // Level badge
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.sm, vertical: 3),
                            decoration: BoxDecoration(
                              color: _levelBadgeBg(level),
                              borderRadius: BorderRadius.circular(tier.shape.chipRadius),
                            ),
                            child: Text(
                              'Lv $level',
                              style: TextStyle(
                                fontSize: tier.typography.chipSize,
                                fontWeight: FontWeight.w700,
                                color: _levelBadgeColor(level),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      // Status text
                      Row(
                        children: [
                          if (isMastered)
                            Icon(Icons.verified_rounded, size: 14, color: _tealDone),
                          if (isMastered) const SizedBox(width: 4),
                          Text(
                            isMastered
                                ? 'Mastered!'
                                : isCurrent
                                    ? '$qCount questions \u{2022} Let\'s go!'
                                    : 'Up next',
                            style: TextStyle(
                              fontSize: tier.typography.chipSize,
                              color: isMastered ? _tealDone : KiwiColors.textMuted,
                              fontWeight: isMastered ? FontWeight.w600 : FontWeight.w400,
                            ),
                          ),
                        ],
                      ),
                      // Start button for current topic
                      if (onStart != null) ...[
                        const SizedBox(height: 12),
                        GestureDetector(
                          onTap: onStart,
                          child: Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(vertical: 11),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [_orangeStart, KiwiColors.pathCurrent],
                              ),
                              borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
                              boxShadow: [
                                BoxShadow(
                                  color: _orangeStart.withOpacity(0.25),
                                  blurRadius: 6,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 18),
                                const SizedBox(width: KiwiSpacing.xs),
                                Text(
                                  'Start practice',
                                  style: TextStyle(
                                    fontSize: tier.typography.buttonSize,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.white,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ],
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

// =============================================================================
// Error view
// =============================================================================

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(KiwiSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.route_rounded, size: 48, color: KiwiColors.pathLocked),
            const SizedBox(height: KiwiSpacing.md),
            const Text(
              'Path is warming up!',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: KiwiSpacing.sm),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 13, color: KiwiColors.textMuted, height: 1.4),
            ),
            const SizedBox(height: KiwiSpacing.lg),
            GestureDetector(
              onTap: onRetry,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.xl, vertical: KiwiSpacing.sm),
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiPrimary,
                  borderRadius: BorderRadius.circular(KiwiSpacing.md),
                ),
                child: const Text(
                  'Try again',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Colors.white),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
