import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/olympiad_worksheet.dart';
import '../services/api_client.dart';
import '../services/worksheet_cache.dart';
import '../theme/kiwi_theme.dart';
import 'worksheet_solve_screen.dart';

/// Worksheet list screen — redesigned with 3 views:
///   1. Topic-grouped (default) — worksheets grouped by dominant topic
///   2. Journey — horizontal swipeable cards with titles + topic icons
///   3. Grid — compact 10×10 calendar progress grid
///
/// Each worksheet card shows: title, subtitle (topics), difficulty badges,
/// download indicator (cloud/checkmark), and completion status.
class WorksheetListScreen extends StatefulWidget {
  final int grade;
  final void Function(int grade)? onGradeChanged;

  const WorksheetListScreen({
    super.key,
    required this.grade,
    this.onGradeChanged,
  });

  @override
  State<WorksheetListScreen> createState() => _WorksheetListScreenState();
}

enum _ViewMode { topics, grid }

class _WorksheetListScreenState extends State<WorksheetListScreen> {
  final _api = ApiClient();
  final _cache = WorksheetCache.instance;
  Map<int, WorksheetResult> _results = {};
  List<WorksheetMeta> _worksheets = [];
  bool _loading = true;
  bool _downloading = false;
  double _downloadProgress = 0.0;
  int _selectedGrade = 1;
  _ViewMode _viewMode = _ViewMode.topics;

  // Topic display config
  static const _topicConfig = <String, _TopicInfo>{
    'counting_observation': _TopicInfo('Counting & Observation', Icons.visibility_rounded, Color(0xFF42A5F5)),
    'arithmetic_missing_numbers': _TopicInfo('Arithmetic', Icons.calculate_rounded, Color(0xFFFF7043)),
    'logic_ordering': _TopicInfo('Logic & Reasoning', Icons.psychology_rounded, Color(0xFF7C4DFF)),
    'word_problems_stories': _TopicInfo('Word Problems', Icons.auto_stories_rounded, Color(0xFFEC407A)),
    'shapes_folding_symmetry': _TopicInfo('Shapes & Symmetry', Icons.category_rounded, Color(0xFF26C6DA)),
    'patterns_sequences': _TopicInfo('Patterns & Sequences', Icons.auto_awesome_rounded, Color(0xFFFFCA28)),
    'mixed': _TopicInfo('Mixed Challenge', Icons.shuffle_rounded, Color(0xFF66BB6A)),
  };

  @override
  void initState() {
    super.initState();
    _selectedGrade = widget.grade;
    _loadData();
  }

  @override
  void didUpdateWidget(covariant WorksheetListScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.grade != widget.grade) {
      _selectedGrade = widget.grade;
      _loadData();
    }
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
      await _cache.init();
      final futures = await Future.wait([
        _cache.getAllResults(_selectedGrade),
        _api.getOlympiadWorksheetList(_selectedGrade),
      ]);
      _results = futures[0] as Map<int, WorksheetResult>;
      _worksheets = futures[1] as List<WorksheetMeta>;
    } catch (e) {
      debugPrint('WorksheetList: load failed: $e');
      // Fallback: generate basic metadata
      if (_worksheets.isEmpty) {
        _worksheets = List.generate(100, (i) => WorksheetMeta(
          day: i + 1,
          title: 'Day ${i + 1}',
        ));
      }
    }
    if (mounted) setState(() => _loading = false);
  }

  int get _nextDay {
    for (int d = 1; d <= 100; d++) {
      if (!_results.containsKey(d)) return d;
    }
    return 1;
  }

  int get _completedCount => _results.length;
  int get _totalStars => _results.values.fold(0, (s, r) => s + r.stars);

  Future<void> _startDownloadAll() async {
    setState(() {
      _downloading = true;
      _downloadProgress = 0;
    });
    try {
      await for (final progress in _cache.downloadGrade(_selectedGrade)) {
        if (mounted) setState(() => _downloadProgress = progress);
      }
    } catch (e) {
      debugPrint('Download failed: $e');
    }
    if (mounted) setState(() => _downloading = false);
  }

  Future<void> _downloadSingle(int day) async {
    try {
      await _cache.downloadWorksheet(_selectedGrade, day);
      if (mounted) setState(() {});
    } catch (e) {
      debugPrint('Single download failed: $e');
    }
  }

  void _openWorksheet(int day) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => WorksheetSolveScreen(
          grade: _selectedGrade,
          day: day,
          onComplete: (result) {
            setState(() => _results[day] = result);
          },
        ),
      ),
    );
  }

  WorksheetMeta? _metaForDay(int day) {
    try {
      return _worksheets.firstWhere((w) => w.day == day);
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(_selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : CustomScrollView(
                slivers: [
                  // ── Header ─────────────────────────────────────────
                  SliverToBoxAdapter(child: _buildHeader(colors, typo)),

                  // ── Continue card ──────────────────────────────────
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: _buildContinueCard(colors, typo),
                    ),
                  ),

                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                  // ── View toggle ────────────────────────────────────
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: _buildViewToggle(colors, typo),
                    ),
                  ),

                  const SliverToBoxAdapter(child: SizedBox(height: 12)),

                  // ── Content based on view mode ─────────────────────
                  if (_viewMode == _ViewMode.topics) ..._buildTopicGroupView(colors, typo),
                  if (_viewMode == _ViewMode.grid) ..._buildGridView(colors, typo),

                  const SliverToBoxAdapter(child: SizedBox(height: 32)),
                ],
              ),
      ),
    );
  }

  // ── Header ─────────────────────────────────────────────────────────────

  Widget _buildHeader(KiwiTierColors colors, KiwiTierTypography typo) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'DPP',
                      style: TextStyle(
                        fontSize: typo.headlineSize + 2,
                        fontWeight: FontWeight.w800,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Daily Practice Problems',
                      style: TextStyle(
                        fontSize: typo.bodySize - 1,
                        color: colors.textSecondary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ],
                ),
              ),
              _buildDownloadAllButton(colors, typo),
            ],
          ),
          const SizedBox(height: 12),

          // Grade picker
          SizedBox(
            height: 42,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: 6,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (_, i) {
                final g = i + 1;
                final selected = g == _selectedGrade;
                return GestureDetector(
                  onTap: () {
                    HapticFeedback.lightImpact();
                    setState(() => _selectedGrade = g);
                    widget.onGradeChanged?.call(g);
                    _loadData();
                  },
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 18),
                    decoration: BoxDecoration(
                      color: selected ? colors.primary : colors.cardBg,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: selected ? colors.primaryDark : colors.topicCardBorder,
                        width: selected ? 2 : 1,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        'G$g',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                          color: selected ? Colors.white : colors.textPrimary,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 14),

          const SizedBox(height: 4),
        ],
      ),
    );
  }

  // ── Download All button ────────────────────────────────────────────────

  Widget _buildDownloadAllButton(KiwiTierColors colors, KiwiTierTypography typo) {
    final downloaded = _cache.downloadedDays(_selectedGrade);
    final isFullyDownloaded = downloaded.length >= 100;

    if (_downloading) {
      return SizedBox(
        width: 44,
        height: 44,
        child: Stack(
          alignment: Alignment.center,
          children: [
            CircularProgressIndicator(
              value: _downloadProgress,
              strokeWidth: 3,
              backgroundColor: const Color(0xFFE0E0E0),
              valueColor: AlwaysStoppedAnimation(colors.primary),
            ),
            Text(
              '${(_downloadProgress * 100).toInt()}',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: colors.primary,
              ),
            ),
          ],
        ),
      );
    }

    return GestureDetector(
      onTap: isFullyDownloaded ? null : _startDownloadAll,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isFullyDownloaded
              ? KiwiColors.kiwiGreenLight
              : colors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isFullyDownloaded
                ? KiwiColors.kiwiGreen
                : colors.primary.withOpacity(0.3),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isFullyDownloaded
                  ? Icons.download_done_rounded
                  : Icons.download_rounded,
              size: 18,
              color: isFullyDownloaded ? KiwiColors.kiwiGreenDark : colors.primary,
            ),
            const SizedBox(width: 4),
            Text(
              isFullyDownloaded
                  ? 'All Saved'
                  : downloaded.isEmpty
                      ? 'Download All'
                      : '${downloaded.length}/100',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: isFullyDownloaded
                    ? KiwiColors.kiwiGreenDark
                    : colors.primary,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Stats row ──────────────────────────────────────────────────────────

  Widget _buildStatsRow(KiwiTierColors colors, KiwiTierTypography typo) {
    return Row(
      children: [
        _statChip('\u{2705}', '$_completedCount/100', 'Completed', colors, typo),
        const SizedBox(width: 10),
        _statChip('\u{2B50}', '$_totalStars', 'Stars', colors, typo),
        const SizedBox(width: 10),
        _statChip(
          '\u{1F525}',
          _results.isEmpty
              ? '0%'
              : '${(_results.values.fold<double>(0, (s, r) => s + r.accuracy) / _results.length * 100).toInt()}%',
          'Accuracy',
          colors,
          typo,
        ),
      ],
    );
  }

  Widget _statChip(String emoji, String value, String label,
      KiwiTierColors colors, KiwiTierTypography typo) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: colors.topicCardBorder),
        ),
        child: Column(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 2),
            Text(
              value,
              style: TextStyle(
                fontSize: typo.bodySize + 1,
                fontWeight: FontWeight.w800,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Continue card ──────────────────────────────────────────────────────

  Widget _buildContinueCard(KiwiTierColors colors, KiwiTierTypography typo) {
    final day = _nextDay;
    final meta = _metaForDay(day);

    return GestureDetector(
      onTap: () => _openWorksheet(day),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [colors.primary, colors.primaryDark],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: colors.primary.withOpacity(0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Center(
                child: Text(
                  'D$day',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                    color: Colors.white,
                    fontFamily: typo.fontFamily,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    meta?.title ?? (_completedCount == 0 ? 'Start Your Journey!' : 'Continue Training'),
                    style: TextStyle(
                      fontSize: typo.bodySize + 2,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                      fontFamily: typo.fontFamily,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    meta?.subtitle ?? 'Day $day \u{2022} 12 questions',
                    style: TextStyle(
                      fontSize: typo.chipSize,
                      color: Colors.white.withOpacity(0.85),
                      fontFamily: typo.fontFamily,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 28),
            ),
          ],
        ),
      ),
    );
  }

  // ── View toggle ────────────────────────────────────────────────────────

  Widget _buildViewToggle(KiwiTierColors colors, KiwiTierTypography typo) {
    return Row(
      children: [
        _viewTab('Topics', Icons.category_rounded, _ViewMode.topics, colors, typo),
        const SizedBox(width: 8),
        _viewTab('Grid', Icons.grid_view_rounded, _ViewMode.grid, colors, typo),
      ],
    );
  }

  Widget _viewTab(String label, IconData icon, _ViewMode mode,
      KiwiTierColors colors, KiwiTierTypography typo) {
    final selected = _viewMode == mode;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          setState(() => _viewMode = mode);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: selected ? colors.primary : colors.cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? colors.primaryDark : colors.topicCardBorder,
              width: selected ? 2 : 1,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 16,
                color: selected ? Colors.white : colors.textMuted,
              ),
              const SizedBox(width: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: selected ? Colors.white : colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // VIEW 1: Topic-grouped
  // ══════════════════════════════════════════════════════════════════════

  List<Widget> _buildTopicGroupView(KiwiTierColors colors, KiwiTierTypography typo) {
    // Group worksheets by dominant topic
    final groups = <String, List<WorksheetMeta>>{};
    for (final ws in _worksheets) {
      final topic = ws.dominantTopic.isNotEmpty ? ws.dominantTopic : 'mixed';
      groups.putIfAbsent(topic, () => []).add(ws);
    }

    // Sort topics by number of worksheets (most first)
    final sortedTopics = groups.keys.toList()
      ..sort((a, b) => groups[b]!.length.compareTo(groups[a]!.length));

    final slivers = <Widget>[];
    for (final topic in sortedTopics) {
      final info = _topicConfig[topic] ?? _topicConfig['mixed']!;
      final worksheetsInGroup = groups[topic]!;

      // Topic header
      slivers.add(SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
          child: Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: info.color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(info.icon, size: 18, color: info.color),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      info.label,
                      style: TextStyle(
                        fontSize: typo.bodySize,
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    Text(
                      '${worksheetsInGroup.length} worksheets',
                      style: TextStyle(
                        fontSize: 11,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ));

      // Worksheet cards in this group
      slivers.add(SliverPadding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
        sliver: SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final ws = worksheetsInGroup[index];
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: _buildWorksheetCard(ws, info.color, colors, typo),
              );
            },
            childCount: worksheetsInGroup.length,
          ),
        ),
      ));
    }

    return slivers;
  }

  // ══════════════════════════════════════════════════════════════════════
  // VIEW 2: Journey (horizontal swipeable cards)
  // ══════════════════════════════════════════════════════════════════════

  List<Widget> _buildJourneyView(KiwiTierColors colors, KiwiTierTypography typo) {
    return [
      SliverToBoxAdapter(
        child: SizedBox(
          height: 220,
          child: PageView.builder(
            controller: PageController(viewportFraction: 0.85, initialPage: _nextDay - 1),
            itemCount: _worksheets.length,
            itemBuilder: (context, index) {
              final ws = _worksheets[index];
              final info = _topicConfig[ws.dominantTopic] ?? _topicConfig['mixed']!;
              final result = _results[ws.day];
              final isCompleted = result != null;
              final isDownloaded = _cache.isDownloaded(_selectedGrade, ws.day);

              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
                child: GestureDetector(
                  onTap: () => _openWorksheet(ws.day),
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: isCompleted
                            ? [const Color(0xFF66BB6A), const Color(0xFF43A047)]
                            : [info.color, info.color.withOpacity(0.7)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: info.color.withOpacity(0.25),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.25),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                'Day ${ws.day}',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                  color: Colors.white,
                                  fontFamily: typo.fontFamily,
                                ),
                              ),
                            ),
                            const Spacer(),
                            if (isCompleted)
                              Text(
                                '\u{2B50}' * result.stars,
                                style: const TextStyle(fontSize: 16),
                              ),
                            if (!isCompleted)
                              _downloadIndicator(ws.day, isDownloaded, Colors.white),
                          ],
                        ),
                        const Spacer(),
                        Text(
                          ws.title,
                          style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                            fontFamily: typo.fontFamily,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          ws.subtitle,
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.white.withOpacity(0.85),
                            fontFamily: typo.fontFamily,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            _journeyDiffBadge('${ws.warmupCount}', 'W', const Color(0xFF4CAF50)),
                            const SizedBox(width: 6),
                            _journeyDiffBadge('${ws.practiceCount}', 'P', const Color(0xFFFF9800)),
                            const SizedBox(width: 6),
                            _journeyDiffBadge('${ws.challengeCount}', 'C', const Color(0xFFE53935)),
                            const Spacer(),
                            if (isCompleted)
                              Text(
                                '${result.correctCount}/${result.totalCount}',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.white.withOpacity(0.9),
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
            },
          ),
        ),
      ),
      // Also show a compact list below the journey cards
      SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(
            'All Worksheets',
            style: TextStyle(
              fontSize: typo.bodySize + 1,
              fontWeight: FontWeight.w700,
              color: colors.textPrimary,
              fontFamily: typo.fontFamily,
            ),
          ),
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
        sliver: SliverList(
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final ws = _worksheets[index];
              final info = _topicConfig[ws.dominantTopic] ?? _topicConfig['mixed']!;
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: _buildCompactCard(ws, info, colors, typo),
              );
            },
            childCount: _worksheets.length,
          ),
        ),
      ),
    ];
  }

  Widget _journeyDiffBadge(String count, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        '$count$label',
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: Colors.white.withOpacity(0.95),
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // VIEW 3: Grid (10×10 progress calendar)
  // ══════════════════════════════════════════════════════════════════════

  List<Widget> _buildGridView(KiwiTierColors colors, KiwiTierTypography typo) {
    return [
      SliverPadding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        sliver: SliverGrid(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 10,
            mainAxisSpacing: 6,
            crossAxisSpacing: 6,
            childAspectRatio: 1.0,
          ),
          delegate: SliverChildBuilderDelegate(
            (context, index) {
              final day = index + 1;
              return _buildDayCell(day, colors, typo);
            },
            childCount: 100,
          ),
        ),
      ),
      // Legend
      SliverToBoxAdapter(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _legendDot(colors.primary.withOpacity(0.12), 'Current', colors, typo),
              const SizedBox(width: 16),
              _legendDot(const Color(0xFFFFF8E1), '\u{2B50} Done', colors, typo),
              const SizedBox(width: 16),
              _legendDot(const Color(0xFF90CAF9).withOpacity(0.2), 'Downloaded', colors, typo),
            ],
          ),
        ),
      ),
    ];
  }

  Widget _legendDot(Color color, String label, KiwiTierColors colors, KiwiTierTypography typo) {
    return Row(
      children: [
        Container(
          width: 14,
          height: 14,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: colors.topicCardBorder),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 10,
            color: colors.textMuted,
            fontFamily: typo.fontFamily,
          ),
        ),
      ],
    );
  }

  Widget _buildDayCell(int day, KiwiTierColors colors, KiwiTierTypography typo) {
    final result = _results[day];
    final isCompleted = result != null;
    final isCurrent = day == _nextDay;
    final isDownloaded = _cache.isDownloaded(_selectedGrade, day);

    Color bg;
    Color textColor;
    Color borderColor;
    Widget? overlay;

    if (isCompleted) {
      final stars = result.stars;
      bg = stars >= 3
          ? const Color(0xFFFFF8E1)
          : stars >= 2
              ? KiwiColors.kiwiGreenLight
              : const Color(0xFFF1F8E9);
      textColor = stars >= 3 ? const Color(0xFFE65100) : KiwiColors.kiwiGreenDark;
      borderColor = stars >= 3 ? const Color(0xFFFFB300) : KiwiColors.kiwiGreen;
      overlay = Positioned(
        bottom: 1,
        right: 1,
        child: Text('\u{2B50}' * stars.clamp(0, 3), style: const TextStyle(fontSize: 5)),
      );
    } else if (isCurrent) {
      bg = colors.primary.withOpacity(0.12);
      textColor = colors.primary;
      borderColor = colors.primary;
    } else {
      bg = colors.cardBg;
      textColor = colors.textMuted;
      borderColor = isDownloaded ? const Color(0xFF90CAF9) : colors.topicCardBorder;
      overlay = isDownloaded
          ? const Positioned(
              bottom: 1,
              right: 1,
              child: Icon(Icons.download_done, size: 8, color: Color(0xFF64B5F6)),
            )
          : null;
    }

    return GestureDetector(
      onTap: () => _openWorksheet(day),
      child: Stack(
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              color: bg,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: borderColor, width: isCurrent ? 2 : 1),
            ),
            child: Center(
              child: Text(
                '$day',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: isCompleted || isCurrent ? FontWeight.w800 : FontWeight.w500,
                  color: textColor,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),
          ),
          if (overlay != null) overlay,
        ],
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════
  // SHARED: Worksheet cards
  // ══════════════════════════════════════════════════════════════════════

  /// Rich worksheet card for topic-grouped view.
  Widget _buildWorksheetCard(WorksheetMeta ws, Color topicColor,
      KiwiTierColors colors, KiwiTierTypography typo) {
    final result = _results[ws.day];
    final isCompleted = result != null;
    final isDownloaded = _cache.isDownloaded(_selectedGrade, ws.day);

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(14),
      child: InkWell(
        onTap: () => _openWorksheet(ws.day),
        borderRadius: BorderRadius.circular(14),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: isCompleted ? KiwiColors.kiwiGreen.withOpacity(0.4) : colors.topicCardBorder,
            ),
          ),
          child: Row(
            children: [
              // Day badge with topic color
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  gradient: isCompleted
                      ? const LinearGradient(
                          colors: [Color(0xFF66BB6A), Color(0xFF43A047)])
                      : LinearGradient(
                          colors: [topicColor.withOpacity(0.15), topicColor.withOpacity(0.08)],
                        ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: isCompleted
                      ? const Icon(Icons.check_rounded, color: Colors.white, size: 24)
                      : Text(
                          '${ws.day}',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: topicColor,
                            fontFamily: typo.fontFamily,
                          ),
                        ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      ws.title,
                      style: TextStyle(
                        fontSize: typo.bodySize,
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      ws.subtitle.isNotEmpty ? ws.subtitle : 'Day ${ws.day}',
                      style: TextStyle(
                        fontSize: typo.chipSize,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (isCompleted) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Text(
                            '${result.correctCount}/${result.totalCount}',
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF2E7D32),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '\u{2B50}' * result.stars,
                            style: const TextStyle(fontSize: 11),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              // Difficulty badges + download
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  if (ws.warmupCount > 0)
                    _diffBadge('${ws.warmupCount} Warmup', const Color(0xFF4CAF50)),
                  if (ws.practiceCount > 0) ...[
                    const SizedBox(height: 3),
                    _diffBadge('${ws.practiceCount} Practice', const Color(0xFFFF9800)),
                  ],
                  if (ws.challengeCount > 0) ...[
                    const SizedBox(height: 3),
                    _diffBadge('${ws.challengeCount} Challenge', const Color(0xFFE53935)),
                  ],
                  const SizedBox(height: 6),
                  _downloadIndicator(ws.day, isDownloaded, colors.textMuted),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Compact card for journey list view.
  Widget _buildCompactCard(WorksheetMeta ws, _TopicInfo info,
      KiwiTierColors colors, KiwiTierTypography typo) {
    final result = _results[ws.day];
    final isCompleted = result != null;
    final isDownloaded = _cache.isDownloaded(_selectedGrade, ws.day);

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: () => _openWorksheet(ws.day),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: colors.topicCardBorder),
          ),
          child: Row(
            children: [
              // Topic color dot
              Container(
                width: 8,
                height: 32,
                decoration: BoxDecoration(
                  color: isCompleted ? KiwiColors.kiwiGreen : info.color,
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                '${ws.day}.',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w800,
                  color: colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  ws.title,
                  style: TextStyle(
                    fontSize: typo.chipSize + 1,
                    fontWeight: FontWeight.w600,
                    color: colors.textPrimary,
                    fontFamily: typo.fontFamily,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (isCompleted)
                Text('\u{2B50}' * result.stars, style: const TextStyle(fontSize: 12)),
              if (!isCompleted)
                _downloadIndicator(ws.day, isDownloaded, colors.textMuted),
              const SizedBox(width: 4),
              Icon(Icons.chevron_right_rounded, size: 18, color: colors.textMuted),
            ],
          ),
        ),
      ),
    );
  }

  // ── Shared small widgets ───────────────────────────────────────────────

  Widget _diffBadge(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }

  /// Per-worksheet download indicator — cloud icon (not downloaded) or checkmark (downloaded).
  /// Tapping cloud triggers a single worksheet download.
  Widget _downloadIndicator(int day, bool isDownloaded, Color iconColor) {
    if (isDownloaded) {
      return Icon(Icons.download_done_rounded, size: 16, color: KiwiColors.kiwiGreen);
    }
    return GestureDetector(
      onTap: () => _downloadSingle(day),
      child: Icon(Icons.cloud_download_outlined, size: 16, color: iconColor),
    );
  }
}

// ── Topic info helper ──────────────────────────────────────────────────────

class _TopicInfo {
  final String label;
  final IconData icon;
  final Color color;
  const _TopicInfo(this.label, this.icon, this.color);
}
