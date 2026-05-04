import 'package:flutter/material.dart';

import '../models/companion.dart';
import '../models/student_levels.dart';
import '../services/api_client.dart';
import '../services/companion_service.dart';
import '../theme/kiwi_theme.dart';
import 'question_screen_v2.dart';

/// Learning Path screen v4 — redesigned with dual-tab layout.
///
/// Two tabs at the top:
///   - **Curriculum** (chapters in sequence — NCERT/ICSE flow)
///   - **Olympiad** (8 Kangaroo topics with level progression)
///
/// Default tab = user's onboarded curriculum. For now (pre-curriculum-wiring),
/// defaults to Olympiad since that's what the backend returns.
///
/// Smart nudge: when a student hits level 4+ in their curriculum topics,
/// show a banner encouraging them to try Olympiad challenges.
class LearningPathScreen extends StatefulWidget {
  final String userId;
  final int grade;
  final CompanionService? companionService;
  final StudentLevels? studentLevels;

  /// When true, the screen is embedded inside a bottom-nav shell and should
  /// not show an AppBar back button.
  final bool embedded;

  /// User's selected curriculum from profile. Determines default tab.
  /// Values: 'ncert', 'icse', 'olympiad', or null (defaults to olympiad).
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

  // Chapters state (Curriculum tab)
  List<Map<String, dynamic>>? _chapters;
  bool _chaptersLoading = false;
  String? _chaptersError;

  /// 0 = Curriculum (chapters), 1 = Olympiad (topics)
  late int _activeTab;

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------

  static const _orangeStart = Color(0xFFFF6D00);
  static const _orangeEnd = Color(0xFFFF9100);
  static const _tealDone = Color(0xFF1D9E75);

  @override
  void initState() {
    super.initState();
    // Default tab: if curriculum is olympiad (or null/unset), show Olympiad first
    final cur = widget.curriculum ?? 'olympiad';
    _activeTab = (cur == 'olympiad') ? 1 : 0;
    _load();
    _loadChapters();
  }

  Future<void> _loadChapters() async {
    final cur = widget.curriculum;
    if (cur == null || cur == 'olympiad') return; // No chapters for Olympiad
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
      setState(() {
        _chaptersError = 'Could not load chapters. Try again later.';
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
      // Curriculum changed — update default tab + reload chapters
      final cur = widget.curriculum ?? 'olympiad';
      _activeTab = (cur == 'olympiad') ? 1 : 0;
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
      String friendlyError;
      final raw = e.toString();
      if (raw.contains('422') ||
          raw.contains('less_than_equal') ||
          raw.contains('validation')) {
        friendlyError =
            "We're still building the learning path for Grade ${widget.grade}. "
            "Try Smart Practice for now — it works great!";
      } else if (raw.contains('SocketException') ||
          raw.contains('Connection')) {
        friendlyError =
            "Hmm, can't reach our servers right now. Check your internet and try again.";
      } else {
        friendlyError =
            "Something didn't work quite right. Give it another try!";
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

  /// Check if any topic has level >= 4 (triggers the olympiad nudge).
  bool get _showOlympiadNudge {
    if (_activeTab != 0) return false; // only show on Curriculum tab
    final levels = widget.studentLevels;
    if (levels == null) return false;
    return levels.topics.any((t) => t.currentLevel >= 4);
  }

  /// Find the highest-level topic name for the nudge text.
  String get _nudgeTopicName {
    final levels = widget.studentLevels;
    if (levels == null) return '';
    final sorted = [...levels.topics]
      ..sort((a, b) => b.currentLevel.compareTo(a.currentLevel));
    return sorted.isNotEmpty ? sorted.first.topicName : '';
  }

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
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 0),
      child: Row(
        children: [
          Text(
            'Your path',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: tier.colors.textPrimary,
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
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
      child: Container(
        height: 36,
        decoration: BoxDecoration(
          color: tier.colors.backgroundDark,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            _buildTab(
              label: 'Chapters',
              index: 0,
              tier: tier,
            ),
            _buildTab(
              label: 'Olympiad',
              index: 1,
              tier: tier,
            ),
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
            color: isActive ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
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
              fontSize: 13,
              fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
              color: isActive
                  ? tier.colors.textPrimary
                  : tier.colors.textPrimary.withOpacity(0.5),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody(KiwiTier tier) {
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
          'No learning path yet. Try Smart Practice first!',
          style: TextStyle(
            fontSize: 14,
            color: tier.colors.textPrimary.withOpacity(0.5),
          ),
        ),
      );
    }

    final path = (data['path'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .toList();

    // First not-yet-mastered stop is the "current" one.
    int currentIdx = path.indexWhere(
      (s) => (s['mastery_label'] as String? ?? '') != 'mastered',
    );
    if (currentIdx < 0) currentIdx = 0;

    // Count mastered
    final masteredCount =
        path.where((s) => s['mastery_label'] == 'mastered').length;

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 4, 18, 28),
        children: [
          // Progress bar
          _buildProgressBar(masteredCount, path.length, tier),
          const SizedBox(height: 14),
          // Olympiad nudge (only on Curriculum tab when kid is doing well)
          if (_showOlympiadNudge) ...[
            _buildOlympiadNudge(tier),
            const SizedBox(height: 14),
          ],
          // Curriculum tab — real chapters from /v2/chapters API
          if (_activeTab == 0) ...[
            _buildCurriculumChapters(tier),
          ] else ...[
            // Olympiad tab — show the path stops
            for (int i = 0; i < path.length; i++)
              _PathStopCard(
                stop: path[i],
                index: i,
                isFirst: i == 0,
                isLast: i == path.length - 1,
                isCurrent: i == currentIdx,
                onStart: i == currentIdx ? () => _startStop(path[i]) : null,
                studentLevels: widget.studentLevels,
              ),
          ],
        ],
      ),
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
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: tier.colors.textPrimary.withOpacity(0.5),
              ),
            ),
            const Spacer(),
            Text(
              '${(fraction * 100).round()}%',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: _tealDone,
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
            valueColor: const AlwaysStoppedAnimation<Color>(_tealDone),
          ),
        ),
      ],
    );
  }

  Widget _buildOlympiadNudge(KiwiTier tier) {
    return GestureDetector(
      onTap: () => setState(() => _activeTab = 1),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFFFF3E0), Color(0xFFFFFBF5)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: _orangeStart.withOpacity(0.2)),
        ),
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: _orangeStart.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.stars_rounded,
                size: 18,
                color: _orangeStart,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'You\'re crushing $_nudgeTopicName!',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: tier.colors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Try Olympiad-level challenges too',
                    style: TextStyle(
                      fontSize: 11.5,
                      color: tier.colors.textPrimary.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              Icons.arrow_forward_ios_rounded,
              size: 14,
              color: _orangeStart,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCurriculumChapters(KiwiTier tier) {
    if (_chaptersLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 40),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (_chaptersError != null) {
      return _ErrorView(message: _chaptersError!, onRetry: _loadChapters);
    }
    final chapters = _chapters;
    if (chapters == null || chapters.isEmpty) {
      // Fallback for no data / olympiad users who switch to Chapters tab
      final curLabel = (widget.curriculum ?? 'NCERT').toUpperCase();
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        decoration: BoxDecoration(
          color: tier.colors.backgroundDark,
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          children: [
            Icon(Icons.menu_book_rounded, size: 40,
                color: tier.colors.textPrimary.withOpacity(0.3)),
            const SizedBox(height: 12),
            Text(
              '$curLabel chapters coming soon',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700,
                  color: tier.colors.textPrimary.withOpacity(0.7)),
            ),
            const SizedBox(height: 6),
            Text(
              'We\'re building chapter-wise content for your curriculum.\nTry Olympiad practice in the meantime!',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12.5,
                  color: tier.colors.textPrimary.withOpacity(0.5), height: 1.4),
            ),
          ],
        ),
      );
    }

    // Real chapters list
    return Column(
      children: [
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

  void _startChapter(Map<String, dynamic> chapter) {
    final chapterName = chapter['name'] as String? ?? 'Chapter';
    final chapterId = chapter['id'] as String? ?? '';
    final cur = widget.curriculum ?? 'ncert';
    // Navigate to question screen with chapter + curriculum for IRT-powered practice
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
// Chapter card for curriculum tab
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
    final name = chapter['name'] as String? ?? 'Chapter ${index + 1}';
    final questionCount = chapter['question_count'] as int? ?? 0;
    final topics = (chapter['topics'] as List<dynamic>?)?.cast<String>() ?? [];

    // Chapter number colors cycle through a palette
    final colors = [
      const Color(0xFF2E7D32),
      const Color(0xFF1565C0),
      const Color(0xFF6A1B9A),
      const Color(0xFFFF6D00),
      const Color(0xFFC62828),
      const Color(0xFF00838F),
    ];
    final accentColor = colors[index % colors.length];

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: accentColor.withOpacity(0.15)),
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
            // Chapter number badge
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: accentColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              alignment: Alignment.center,
              child: Text(
                '${index + 1}',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: accentColor,
                ),
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
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: tier.colors.textPrimary,
                    ),
                  ),
                  if (topics.isNotEmpty) ...[
                    const SizedBox(height: 3),
                    Text(
                      topics.take(3).join(', '),
                      style: TextStyle(
                        fontSize: 11.5,
                        color: tier.colors.textPrimary.withOpacity(0.5),
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ],
              ),
            ),
            // Question count + chevron
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '$questionCount Qs',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: accentColor.withOpacity(0.7),
                  ),
                ),
              ],
            ),
            const SizedBox(width: 4),
            Icon(Icons.chevron_right_rounded,
                size: 20, color: accentColor.withOpacity(0.4)),
          ],
        ),
      ),
    );
  }
}

// =============================================================================
// Path stop card with vertical timeline
// =============================================================================

class _PathStopCard extends StatelessWidget {
  final Map<String, dynamic> stop;
  final int index;
  final bool isFirst;
  final bool isLast;
  final bool isCurrent;
  final VoidCallback? onStart;
  final StudentLevels? studentLevels;

  const _PathStopCard({
    required this.stop,
    required this.index,
    required this.isFirst,
    required this.isLast,
    required this.isCurrent,
    required this.onStart,
    this.studentLevels,
  });

  static const _orangeStart = Color(0xFFFF6D00);
  static const _tealDone = Color(0xFF1D9E75);

  /// Level colors consistent with home screen.
  Color _levelBadgeColor(int level) {
    if (level >= 7) return const Color(0xFF7B1FA2); // purple
    if (level >= 4) return const Color(0xFF1976D2); // blue
    return const Color(0xFF388E3C); // green
  }

  Color _levelBadgeBg(int level) {
    if (level >= 7) return const Color(0xFFF3E5F5);
    if (level >= 4) return const Color(0xFFE3F2FD);
    return const Color(0xFFE8F5E9);
  }

  @override
  Widget build(BuildContext context) {
    final mastery = (stop['mastery_label'] as String?) ?? 'learning';
    final isMastered = mastery == 'mastered';
    final topicName = (stop['topic_name'] as String?) ?? 'Topic';
    final topicId = (stop['topic_id'] as String?) ?? '';
    final qCount = (stop['questions_to_attempt'] as num?)?.toInt() ?? 5;

    // Get level from StudentLevels if available
    int level = (stop['target_difficulty'] as num?)?.toInt() ?? 1;
    if (studentLevels != null) {
      final topicLevel = studentLevels!.topics.where(
        (t) => t.topicId == topicId,
      );
      if (topicLevel.isNotEmpty) {
        level = topicLevel.first.currentLevel;
      }
    }

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline rail
          SizedBox(
            width: 32,
            child: Column(
              children: [
                // Top connector
                Expanded(
                  flex: 1,
                  child: Container(
                    width: 2,
                    color: isFirst
                        ? Colors.transparent
                        : isMastered
                            ? _tealDone
                            : Colors.grey.shade300,
                  ),
                ),
                // Node
                Container(
                  width: isCurrent ? 28 : 24,
                  height: isCurrent ? 28 : 24,
                  decoration: BoxDecoration(
                    color: isMastered
                        ? _tealDone
                        : isCurrent
                            ? _orangeStart
                            : Colors.grey.shade300,
                    shape: BoxShape.circle,
                    boxShadow: isCurrent
                        ? [
                            BoxShadow(
                              color: _orangeStart.withOpacity(0.25),
                              blurRadius: 8,
                              spreadRadius: 2,
                            ),
                          ]
                        : null,
                  ),
                  alignment: Alignment.center,
                  child: isMastered
                      ? const Icon(Icons.check, color: Colors.white, size: 14)
                      : Text(
                          '${index + 1}',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: isCurrent
                                ? Colors.white
                                : Colors.grey.shade600,
                          ),
                        ),
                ),
                // Bottom connector
                Expanded(
                  flex: 5,
                  child: Container(
                    width: 2,
                    color: isLast ? Colors.transparent : Colors.grey.shade300,
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
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isCurrent
                        ? _orangeStart
                        : Colors.grey.shade200,
                    width: isCurrent ? 1.5 : 1,
                  ),
                ),
                child: Opacity(
                  opacity: (isMastered || isCurrent) ? 1.0 : 0.55,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              topicName,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: KiwiColors.textDark,
                              ),
                            ),
                          ),
                          // Level badge
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: _levelBadgeBg(level),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              'Lv $level',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: _levelBadgeColor(level),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        isMastered
                            ? 'Mastered'
                            : isCurrent
                                ? 'Next: $qCount questions recommended'
                                : 'Up next',
                        style: TextStyle(
                          fontSize: 12,
                          color: isMastered
                              ? _tealDone
                              : Colors.grey.shade600,
                          fontWeight: isMastered
                              ? FontWeight.w600
                              : FontWeight.w400,
                        ),
                      ),
                      // "Continue practice" button for current stop
                      if (onStart != null) ...[
                        const SizedBox(height: 10),
                        GestureDetector(
                          onTap: onStart,
                          child: Container(
                            width: double.infinity,
                            padding: const EdgeInsets.symmetric(vertical: 10),
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                colors: [_orangeStart, Color(0xFFFF9100)],
                              ),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            alignment: Alignment.center,
                            child: const Text(
                              'Continue practice',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
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
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.route_rounded,
              size: 48,
              color: Colors.grey.shade300,
            ),
            const SizedBox(height: 12),
            const Text(
              'Path is warming up!',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey.shade600,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 18),
            GestureDetector(
              onTap: onRetry,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 10,
                ),
                decoration: BoxDecoration(
                  color: KiwiColors.kiwiGreen,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Try again',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
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
