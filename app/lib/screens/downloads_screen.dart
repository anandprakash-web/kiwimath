import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../theme/kiwi_theme.dart';
import '../services/worksheet_cache.dart';

/// Downloads management screen — Spotify-style offline content manager.
///
/// Shows per-grade download status, storage usage, and lets parents
/// batch-download or delete cached worksheets.
class DownloadsScreen extends StatefulWidget {
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;

  const DownloadsScreen({
    super.key,
    required this.selectedGrade,
    required this.onGradeChanged,
  });

  @override
  State<DownloadsScreen> createState() => _DownloadsScreenState();
}

class _DownloadsScreenState extends State<DownloadsScreen> {
  final _cache = WorksheetCache.instance;
  double _cacheSizeMb = 0.0;
  bool _loadingSize = true;

  /// Per-grade download progress (-1 = idle, 0..1 = downloading).
  final Map<int, double> _downloadProgress = {};

  @override
  void initState() {
    super.initState();
    _loadCacheSize();
  }

  Future<void> _loadCacheSize() async {
    final size = await _cache.cacheSizeMb();
    if (mounted) setState(() { _cacheSizeMb = size; _loadingSize = false; });
  }

  Future<void> _downloadGrade(int grade) async {
    setState(() => _downloadProgress[grade] = 0.0);
    try {
      await for (final progress in _cache.downloadGrade(grade)) {
        if (!mounted) return;
        setState(() => _downloadProgress[grade] = progress);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Download failed: $e')),
        );
      }
    }
    if (mounted) {
      setState(() => _downloadProgress.remove(grade));
      _loadCacheSize();
    }
  }

  Future<void> _deleteGrade(int grade) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) {
        final tier = KiwiTier.forGrade(grade);
        return AlertDialog(
          backgroundColor: tier.colors.cardBg,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          ),
          title: Text(
            'Delete Grade $grade cache?',
            style: TextStyle(
              fontFamily: tier.typography.fontFamily,
              fontWeight: FontWeight.w700,
            ),
          ),
          content: Text(
            'This removes downloaded worksheets for Grade $grade. '
            'Your stars and results are kept.',
            style: TextStyle(
              fontFamily: tier.typography.fontFamily,
              color: tier.colors.textSecondary,
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text('Delete', style: TextStyle(color: Colors.red.shade600)),
            ),
          ],
        );
      },
    );
    if (confirm == true) {
      await _cache.deleteGrade(grade);
      if (mounted) {
        setState(() {});
        _loadCacheSize();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return CustomScrollView(
      slivers: [
        // ── Header ─────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [colors.buttonGradientStart, colors.buttonGradientEnd],
                        ),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(Icons.download_rounded, color: Colors.white, size: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Offline Downloads',
                            style: TextStyle(
                              fontSize: typo.headlineSize,
                              fontWeight: typo.headlineWeight,
                              fontFamily: typo.fontFamily,
                              color: colors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Practice without internet',
                            style: TextStyle(
                              fontSize: 13,
                              color: colors.textMuted,
                              fontFamily: typo.fontFamily,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 16),

                // ── Storage usage card ───────────────────────────
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: colors.cardBg,
                    borderRadius: BorderRadius.circular(shape.cardRadius),
                    border: Border.all(color: colors.topicCardBorder),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.storage_rounded, color: colors.primary, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Storage Used',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: colors.textSecondary,
                                fontFamily: typo.fontFamily,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _loadingSize
                                  ? 'Calculating...'
                                  : '${_cacheSizeMb.toStringAsFixed(1)} MB',
                              style: TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                                color: colors.textPrimary,
                                fontFamily: typo.fontFamily,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (_cacheSizeMb > 0)
                        TextButton.icon(
                          onPressed: () async {
                            for (int g = 1; g <= 6; g++) {
                              await _cache.deleteGrade(g);
                            }
                            if (mounted) {
                              setState(() {});
                              _loadCacheSize();
                            }
                          },
                          icon: Icon(Icons.delete_sweep_rounded, size: 18, color: Colors.red.shade400),
                          label: Text(
                            'Clear All',
                            style: TextStyle(
                              color: Colors.red.shade400,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),
                Text(
                  'Download by Grade',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: colors.textPrimary,
                    fontFamily: typo.fontFamily,
                  ),
                ),
                const SizedBox(height: 4),
              ],
            ),
          ),
        ),

        // ── Grade cards ────────────────────────────────────────
        SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          sliver: SliverList(
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                final grade = index + 1;
                return _GradeDownloadCard(
                  grade: grade,
                  downloadedDays: _cache.downloadedDays(grade),
                  downloadProgress: _downloadProgress[grade],
                  onDownload: () => _downloadGrade(grade),
                  onDelete: () => _deleteGrade(grade),
                );
              },
              childCount: 6,
            ),
          ),
        ),

        // ── Bottom info ────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimaryLight,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline_rounded, color: colors.primary, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Each grade (~100 worksheets) uses about 8-12 MB. '
                      'Your stars and results are never deleted.',
                      style: TextStyle(
                        fontSize: 12,
                        color: colors.textSecondary,
                        fontFamily: typo.fontFamily,
                        height: 1.4,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Grade Download Card
// ═══════════════════════════════════════════════════════════════════════════════

class _GradeDownloadCard extends StatelessWidget {
  final int grade;
  final Set<int> downloadedDays;
  final double? downloadProgress; // null = idle, 0..1 = in progress
  final VoidCallback onDownload;
  final VoidCallback onDelete;

  const _GradeDownloadCard({
    required this.grade,
    required this.downloadedDays,
    this.downloadProgress,
    required this.onDownload,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(grade);
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    final total = 100;
    final downloaded = downloadedDays.length;
    final isComplete = downloaded >= total;
    final isDownloading = downloadProgress != null;
    final fillRatio = downloaded / total;

    // Pick gradient from the topic palette for visual variety.
    final gradColors = KiwiColors.topicGradients[grade % KiwiColors.topicGradients.length];

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Container(
        decoration: BoxDecoration(
          color: colors.cardBg,
          borderRadius: BorderRadius.circular(shape.cardRadius),
          border: Border.all(color: colors.topicCardBorder),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Row(
                children: [
                  // Grade badge
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: gradColors,
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Center(
                      child: Text(
                        'G$grade',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),

                  // Title + status
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Grade $grade',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: colors.textPrimary,
                            fontFamily: typo.fontFamily,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          isComplete
                              ? '✓ All $total worksheets downloaded'
                              : downloaded > 0
                                  ? '$downloaded of $total worksheets'
                                  : 'Not downloaded',
                          style: TextStyle(
                            fontSize: 12,
                            color: isComplete
                                ? KiwiColors.kiwiGreenDark
                                : colors.textMuted,
                            fontFamily: typo.fontFamily,
                            fontWeight: isComplete ? FontWeight.w600 : FontWeight.w400,
                          ),
                        ),
                      ],
                    ),
                  ),

                  // Action buttons
                  if (isDownloading)
                    SizedBox(
                      width: 48,
                      height: 48,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          CircularProgressIndicator(
                            value: downloadProgress,
                            strokeWidth: 3,
                            color: gradColors[0],
                            backgroundColor: colors.topicCardBorder,
                          ),
                          Text(
                            '${(downloadProgress! * 100).toInt()}%',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                              color: colors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    )
                  else if (isComplete)
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.check_circle_rounded, color: KiwiColors.kiwiGreen, size: 28),
                        const SizedBox(width: 8),
                        GestureDetector(
                          onTap: () {
                            HapticFeedback.lightImpact();
                            onDelete();
                          },
                          child: Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: Colors.red.shade50,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Icon(Icons.delete_outline_rounded, color: Colors.red.shade400, size: 20),
                          ),
                        ),
                      ],
                    )
                  else
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (downloaded > 0)
                          GestureDetector(
                            onTap: () {
                              HapticFeedback.lightImpact();
                              onDelete();
                            },
                            child: Container(
                              width: 36,
                              height: 36,
                              decoration: BoxDecoration(
                                color: Colors.red.shade50,
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Icon(Icons.delete_outline_rounded, color: Colors.red.shade400, size: 18),
                            ),
                          ),
                        if (downloaded > 0) const SizedBox(width: 8),
                        GestureDetector(
                          onTap: () {
                            HapticFeedback.lightImpact();
                            onDownload();
                          },
                          child: Container(
                            height: 36,
                            padding: const EdgeInsets.symmetric(horizontal: 16),
                            decoration: BoxDecoration(
                              gradient: LinearGradient(colors: gradColors),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.download_rounded, color: Colors.white, size: 18),
                                const SizedBox(width: 6),
                                Text(
                                  downloaded > 0 ? 'Resume' : 'Download',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                ],
              ),

              // Progress bar
              if (downloaded > 0 || isDownloading) ...[
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: isDownloading ? downloadProgress! : fillRatio,
                    minHeight: 6,
                    color: isComplete ? KiwiColors.kiwiGreen : gradColors[0],
                    backgroundColor: colors.topicCardBorder,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
