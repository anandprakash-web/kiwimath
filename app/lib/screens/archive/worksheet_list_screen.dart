import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/olympiad_worksheet.dart';
import '../services/api_client.dart';
import '../services/worksheet_cache.dart';
import '../theme/kiwi_theme.dart';
import 'worksheet_solve_screen.dart';

/// DPP (Daily Practice Problems) list screen — clean two-view layout:
///   1. Topics (default) — worksheets grouped by dominant topic
///   2. Grid — compact 10x10 calendar progress grid
///
/// Each worksheet card shows: numbered badge, title, subtitle,
/// download indicator (cloud/checkmark), chevron, and completion status.
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
    'counting_observation': _TopicInfo('Counting & Observation', Icons.visibility_rounded, KiwiColors.sky),
    'arithmetic_missing_numbers': _TopicInfo('Arithmetic', Icons.calculate_rounded, KiwiColors.sunset),
    'logic_ordering': _TopicInfo('Logic & Reasoning', Icons.psychology_rounded, KiwiColors.indigo),
    'word_problems_stories': _TopicInfo('Word Problems', Icons.auto_stories_rounded, KiwiColors.coral),
    'shapes_folding_symmetry': _TopicInfo('Shapes & Symmetry', Icons.category_rounded, KiwiColors.teal),
    'patterns_sequences': _TopicInfo('Patterns & Sequences', Icons.auto_awesome_rounded, KiwiColors.amber),
    'mixed': _TopicInfo('Mixed Challenge', Icons.shuffle_rounded, KiwiColors.correct),
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

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(_selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : CustomScrollView(
                slivers: [
                  // ── Header ─────────────────────────────────────────
                  SliverToBoxAdapter(child: _buildHeader(colors, typo)),

                  // ── View toggle ────────────────────────────────────
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: _buildViewToggle(colors, typo, shape),
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
                      borderRadius: BorderRadius.circular(KiwiSpacing.xl),
                      border: Border.all(
                        color: selected ? colors.primaryDark : colors.topicCardBorder,
                        width: selected ? 2 : 1,
                      ),
                    ),
                    child: Center(
                      child: Text(
                        'G$g',
                        style: TextStyle(
                          fontSize: typo.bodySize,
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
              backgroundColor: KiwiColors.pathLocked,
              valueColor: AlwaysStoppedAnimation(colors.primary),
            ),
            Text(
              '${(_downloadProgress * 100).toInt()}',
              style: TextStyle(
                fontSize: typo.chipSize - 2,
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
        padding: const EdgeInsets.symmetric(horizontal: KiwiSpacing.md, vertical: KiwiSpacing.sm),
        decoration: BoxDecoration(
          color: isFullyDownloaded
              ? KiwiColors.kiwiGreenLight
              : colors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(shape.buttonRadius),
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
                fontSize: typo.chipSize,
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

  // (Stats row and Continue card removed for cleaner design)

  // ── View toggle ────────────────────────────────────────────────────────

  Widget _buildViewToggle(KiwiTierColors colors, KiwiTierTypography typo, KiwiTierShape shape) {
    Widget pill(String label, _ViewMode mode) {
      final selected = _viewMode == mode;
      return Expanded(
        child: GestureDetector(
          onTap: () {
            HapticFeedback.lightImpact();
            setState(() => _viewMode = mode);
          },
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(vertical: KiwiSpacing.sm + 2),
            decoration: BoxDecoration(
              color: selected ? colors.primary : Colors.transparent,
              borderRadius: BorderRadius.circular(shape.chipRadius - 6),
            ),
            child: Center(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: typo.topicNameSize,
                  fontWeight: FontWeight.w700,
                  color: selected ? Colors.white : colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.buttonRadius),
        border: Border.all(color: colors.topicCardBorder),
      ),
      child: Row(
        children: [
          pill('Topics', _ViewMode.topics),
          pill('Grid', _ViewMode.grid),
        ],
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
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: info.color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(KiwiSpacing.sm + 2),
                ),
                child: Icon(info.icon, size: 22, color: info.color),
              ),
              const SizedBox(width: 12),
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
                        fontSize: typo.chipSize - 1,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.cloud_download_outlined, size: 18, color: colors.textMuted),
              const SizedBox(width: 8),
              Icon(Icons.chevron_right_rounded, size: 20, color: colors.textMuted),
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
                child: _buildWorksheetCard(ws, info.color, colors, typo, shape),
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
              _legendDot(KiwiColors.visualYellowBg, '\u{2B50} Done', colors, typo),
              const SizedBox(width: KiwiSpacing.lg),
              _legendDot(KiwiColors.visualBlueBg, 'Downloaded', colors, typo),
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
            borderRadius: BorderRadius.circular(KiwiSpacing.xs),
            border: Border.all(color: colors.topicCardBorder),
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: typo.chipSize - 2,
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
          ? KiwiColors.visualYellowBg
          : stars >= 2
              ? KiwiColors.kiwiGreenLight
              : KiwiColors.correctBg;
      textColor = stars >= 3 ? KiwiColors.kiwiPrimaryDark : KiwiColors.kiwiGreenDark;
      borderColor = stars >= 3 ? KiwiColors.gemGold : KiwiColors.kiwiGreen;
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
      borderColor = isDownloaded ? KiwiColors.visualBlueBorder : colors.topicCardBorder;
      overlay = isDownloaded
          ? const Positioned(
              bottom: 1,
              right: 1,
              child: Icon(Icons.download_done, size: 8, color: KiwiColors.visualBlueBorder),
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
              borderRadius: BorderRadius.circular(KiwiSpacing.sm),
              border: Border.all(color: borderColor, width: isCurrent ? 2 : 1),
            ),
            child: Center(
              child: Text(
                '$day',
                style: TextStyle(
                  fontSize: typo.chipSize - 1,
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
      KiwiTierColors colors, KiwiTierTypography typo, KiwiTierShape shape) {
    final result = _results[ws.day];
    final isCompleted = result != null;
    final isDownloaded = _cache.isDownloaded(_selectedGrade, ws.day);

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(shape.cardRadius),
      child: InkWell(
        onTap: () => _openWorksheet(ws.day),
        borderRadius: BorderRadius.circular(shape.cardRadius),
        child: Container(
          padding: shape.cardPadding,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(shape.cardRadius),
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
                          colors: [KiwiColors.correct, KiwiColors.kiwiGreen])
                      : LinearGradient(
                          colors: [topicColor.withOpacity(0.15), topicColor.withOpacity(0.08)],
                        ),
                  borderRadius: BorderRadius.circular(shape.buttonRadius),
                ),
                child: Center(
                  child: isCompleted
                      ? const Icon(Icons.check_rounded, color: Colors.white, size: 24)
                      : Text(
                          '${ws.day}',
                          style: TextStyle(
                            fontSize: typo.headlineSize,
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
                            style: TextStyle(
                              fontSize: typo.chipSize - 1,
                              fontWeight: FontWeight.w700,
                              color: KiwiColors.kiwiGreenDark,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '\u{2B50}' * result.stars,
                            style: TextStyle(fontSize: typo.chipSize - 1),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              _downloadIndicator(ws.day, isDownloaded, colors.textMuted),
              const SizedBox(width: 8),
              Icon(Icons.chevron_right_rounded, size: 20, color: colors.textMuted),
            ],
          ),
        ),
      ),
    );
  }

  // ── Shared small widgets ───────────────────────────────────────────────

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
