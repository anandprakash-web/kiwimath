import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import '../services/api_client.dart';
import '../theme/kiwi_theme.dart';

/// Wavebook screen — live class worksheet MCQs, G3+ only.
///
/// Shows topics grouped by the student's grade level:
///   - G3/G4 → Level 3 content
///   - G5/G6 → Level 4 content
///
/// Each topic is downloadable individually. Two view modes: Topics (default) and Grid.
class WavebookScreen extends StatefulWidget {
  final int selectedGrade;
  final void Function(int grade) onGradeChanged;

  const WavebookScreen({
    super.key,
    required this.selectedGrade,
    required this.onGradeChanged,
  });

  @override
  State<WavebookScreen> createState() => _WavebookScreenState();
}

enum _WbViewMode { topics, grid }

class _WavebookScreenState extends State<WavebookScreen> {
  final _api = ApiClient();
  List<Map<String, dynamic>> _topics = [];
  bool _loading = true;
  String? _error;
  _WbViewMode _viewMode = _WbViewMode.topics;
  String? _downloadingTopic;

  // Grade band selector: 0 = G3-4, 1 = G5-6
  int _gradeBand = 0;

  int get _effectiveGrade => _gradeBand == 0 ? 3 : 5;

  @override
  void initState() {
    super.initState();
    // Set initial grade band based on student's actual grade
    _gradeBand = widget.selectedGrade >= 5 ? 1 : 0;
    _loadTopics();
  }

  @override
  void didUpdateWidget(covariant WavebookScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.selectedGrade != widget.selectedGrade) {
      _gradeBand = widget.selectedGrade >= 5 ? 1 : 0;
      _loadTopics();
    }
  }

  Future<void> _loadTopics() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _api.getWavebookTopics(_effectiveGrade);
      final topics = (data['topics'] as List<dynamic>?)
              ?.map((t) => t as Map<String, dynamic>)
              .toList() ??
          [];
      setState(() {
        _topics = topics;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Could not load worksheets';
        _loading = false;
      });
    }
  }

  Future<void> _downloadTopic(String topicName) async {
    setState(() => _downloadingTopic = topicName);
    try {
      final content = await _api.downloadWavebookTopic(_effectiveGrade, topicName);
      final dir = await getApplicationDocumentsDirectory();
      final safe = topicName.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]'), '_');
      final file = File('${dir.path}/wavebook_g${_effectiveGrade}_$safe.json');
      await file.writeAsString(content);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Downloaded: $topicName')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Download failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _downloadingTopic = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.selectedGrade);
    final colors = tier.colors;
    final typo = tier.typography;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
              child: Text(
                'Worksheet',
                style: TextStyle(
                  fontSize: typo.headlineSize,
                  fontWeight: FontWeight.w800,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
              child: Text(
                'Olympiad MCQs from live class worksheets',
                style: TextStyle(
                  fontSize: 13,
                  color: colors.textSecondary,
                  fontFamily: typo.fontFamily,
                ),
              ),
            ),

            // ── Grade band pills ──────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  _gradePill(0, 'Grade 3-4', colors, typo),
                  const SizedBox(width: 8),
                  _gradePill(1, 'Grade 5-6', colors, typo),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // ── Topics / Grid toggle ──────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Container(
                height: 36,
                decoration: BoxDecoration(
                  color: colors.cardBg,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: colors.topicCardBorder),
                ),
                child: Row(
                  children: [
                    _viewToggle(_WbViewMode.topics, 'Topics', colors, typo),
                    _viewToggle(_WbViewMode.grid, 'Grid', colors, typo),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // ── Content ───────────────────────────────────────
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _error != null
                      ? Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.cloud_off, size: 48, color: colors.textMuted),
                              const SizedBox(height: 12),
                              Text(_error!, style: TextStyle(color: colors.textMuted)),
                              const SizedBox(height: 12),
                              TextButton(
                                onPressed: _loadTopics,
                                child: const Text('Retry'),
                              ),
                            ],
                          ),
                        )
                      : _viewMode == _WbViewMode.topics
                          ? _buildTopicsList(colors, typo)
                          : _buildGrid(colors, typo),
            ),
          ],
        ),
      ),
    );
  }

  Widget _gradePill(int index, String label, KiwiTierColors colors, KiwiTierTypography typo) {
    final selected = _gradeBand == index;
    return GestureDetector(
      onTap: () {
        if (_gradeBand != index) {
          HapticFeedback.lightImpact();
          setState(() => _gradeBand = index);
          _loadTopics();
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected ? KiwiColors.kiwiPrimary : colors.cardBg,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? KiwiColors.kiwiPrimary : colors.topicCardBorder,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: selected ? Colors.white : colors.textSecondary,
            fontFamily: typo.fontFamily,
          ),
        ),
      ),
    );
  }

  Widget _viewToggle(_WbViewMode mode, String label, KiwiTierColors colors, KiwiTierTypography typo) {
    final selected = _viewMode == mode;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          HapticFeedback.lightImpact();
          setState(() => _viewMode = mode);
        },
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.all(3),
          decoration: BoxDecoration(
            color: selected ? KiwiColors.kiwiPrimary : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 12,
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

  // ── Topic list view ─────────────────────────────────────

  static const _topicIcons = <String, IconData>{
    'knowing': Icons.tag_rounded,
    'factor': Icons.grid_view_rounded,
    'multipl': Icons.calculate_rounded,
    'division': Icons.calculate_rounded,
    'decimal': Icons.more_horiz_rounded,
    'area': Icons.crop_square_rounded,
    'perimet': Icons.crop_square_rounded,
    'metric': Icons.straighten_rounded,
    'set': Icons.join_inner_rounded,
    'pattern': Icons.auto_awesome_rounded,
    'symmetr': Icons.flip_rounded,
    'clock': Icons.access_time_rounded,
    'time': Icons.access_time_rounded,
    'day': Icons.calendar_today_rounded,
    'blood': Icons.people_rounded,
    'mental': Icons.psychology_rounded,
    'paper': Icons.content_cut_rounded,
    'pie': Icons.pie_chart_rounded,
    'data': Icons.bar_chart_rounded,
    'net': Icons.view_in_ar_rounded,
    'integer': Icons.exposure_rounded,
    'fraction': Icons.pie_chart_outline_rounded,
    'percent': Icons.percent_rounded,
    'profit': Icons.trending_up_rounded,
    'ratio': Icons.balance_rounded,
    'quadri': Icons.pentagon_rounded,
    'polygon': Icons.pentagon_rounded,
    'angle': Icons.architecture_rounded,
    'line': Icons.linear_scale_rounded,
    'geometr': Icons.change_history_rounded,
    'algebra': Icons.functions_rounded,
    'average': Icons.equalizer_rounded,
    'counting': Icons.visibility_rounded,
    'magic': Icons.auto_fix_high_rounded,
    'money': Icons.payments_rounded,
    'speed': Icons.speed_rounded,
    'age': Icons.cake_rounded,
    'mirror': Icons.flip_rounded,
    'cube': Icons.view_in_ar_rounded,
    'dice': Icons.casino_rounded,
    'direction': Icons.explore_rounded,
    'logic': Icons.psychology_rounded,
    'puzzle': Icons.extension_rounded,
    'test': Icons.quiz_rounded,
    'number': Icons.tag_rounded,
    'addition': Icons.add_rounded,
    'subtract': Icons.remove_rounded,
  };

  IconData _iconForTopic(String topic) {
    final lower = topic.toLowerCase();
    for (final entry in _topicIcons.entries) {
      if (lower.contains(entry.key)) return entry.value;
    }
    return Icons.school_rounded;
  }

  Widget _buildTopicsList(KiwiTierColors colors, KiwiTierTypography typo) {
    if (_topics.isEmpty) {
      return Center(
        child: Text('No worksheets available', style: TextStyle(color: colors.textMuted)),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      itemCount: _topics.length,
      itemBuilder: (context, index) {
        final topic = _topics[index];
        final name = topic['topic'] as String;
        final isDownloading = _downloadingTopic == name;

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: colors.cardBg,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: colors.topicCardBorder),
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            leading: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimaryLight,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                _iconForTopic(name),
                color: KiwiColors.kiwiPrimaryDark,
                size: 20,
              ),
            ),
            title: Text(
              name,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            subtitle: Text(
              'Warmup · Practice · Challenge',
              style: TextStyle(
                fontSize: 11,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Download button
                GestureDetector(
                  onTap: isDownloading ? null : () => _downloadTopic(name),
                  child: isDownloading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Icon(
                          Icons.download_rounded,
                          color: KiwiColors.kiwiPrimary,
                          size: 22,
                        ),
                ),
                const SizedBox(width: 8),
                Icon(
                  Icons.chevron_right_rounded,
                  color: colors.textMuted,
                  size: 22,
                ),
              ],
            ),
            onTap: () => _openTopic(name),
          ),
        );
      },
    );
  }

  // ── Grid view ───────────────────────────────────────────

  Widget _buildGrid(KiwiTierColors colors, KiwiTierTypography typo) {
    if (_topics.isEmpty) {
      return Center(
        child: Text('No worksheets available', style: TextStyle(color: colors.textMuted)),
      );
    }

    return GridView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 0.9,
      ),
      itemCount: _topics.length,
      itemBuilder: (context, index) {
        final topic = _topics[index];
        final name = topic['topic'] as String;
        // Shorten long names for grid view
        final shortName = name.length > 18 ? '${name.substring(0, 16)}...' : name;

        return GestureDetector(
          onTap: () => _openTopic(name),
          child: Container(
            decoration: BoxDecoration(
              color: colors.cardBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: colors.topicCardBorder),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: KiwiColors.kiwiPrimaryLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(
                    _iconForTopic(name),
                    color: KiwiColors.kiwiPrimaryDark,
                    size: 20,
                  ),
                ),
                const SizedBox(height: 8),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 6),
                  child: Text(
                    shortName,
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: colors.textPrimary,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ── Open topic detail (navigate to solve screen) ────────

  void _openTopic(String topicName) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => _WavebookTopicDetail(
          grade: _effectiveGrade,
          topicName: topicName,
          tier: KiwiTier.forGrade(widget.selectedGrade),
        ),
      ),
    );
  }
}

// ═══════════════════════════════════════════════════════════
// Topic detail — shows questions for a single topic
// ═══════════════════════════════════════════════════════════

class _WavebookTopicDetail extends StatefulWidget {
  final int grade;
  final String topicName;
  final KiwiTier tier;

  const _WavebookTopicDetail({
    required this.grade,
    required this.topicName,
    required this.tier,
  });

  @override
  State<_WavebookTopicDetail> createState() => _WavebookTopicDetailState();
}

class _WavebookTopicDetailState extends State<_WavebookTopicDetail> {
  final _api = ApiClient();
  List<dynamic> _questions = [];
  bool _loading = true;
  int _currentIndex = 0;
  int? _selectedChoice;
  bool _answered = false;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  Future<void> _loadQuestions() async {
    try {
      final data = await _api.getWavebookQuestions(widget.grade, widget.topicName);
      setState(() {
        _questions = data['questions'] as List<dynamic>? ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  void _selectChoice(int index) {
    if (_answered) return;
    setState(() {
      _selectedChoice = index;
      _answered = true;
    });
  }

  void _nextQuestion() {
    if (_currentIndex < _questions.length - 1) {
      setState(() {
        _currentIndex++;
        _selectedChoice = null;
        _answered = false;
      });
    } else {
      // Finished all questions — show snackbar before popping
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Worksheet complete!')),
      );
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = widget.tier.colors;
    final typo = widget.tier.typography;

    if (_loading) {
      return Scaffold(
        backgroundColor: colors.background,
        appBar: AppBar(
          title: Text(widget.topicName),
          backgroundColor: colors.background,
          elevation: 0,
        ),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_questions.isEmpty) {
      return Scaffold(
        backgroundColor: colors.background,
        appBar: AppBar(
          title: Text(widget.topicName),
          backgroundColor: colors.background,
          elevation: 0,
        ),
        body: const Center(child: Text('No questions found')),
      );
    }

    final q = _questions[_currentIndex] as Map<String, dynamic>;
    final stem = q['stem'] as String? ?? '';
    final choices = (q['choices'] as List<dynamic>?)?.cast<String>() ?? [];
    final correctAnswer = q['correct_answer'] as int? ?? 0;
    final difficulty = q['difficulty_tier'] as String? ?? 'practice';

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        title: Text(widget.topicName),
        backgroundColor: colors.background,
        foregroundColor: colors.textPrimary,
        elevation: 0,
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: _difficultyColor(difficulty).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '${_currentIndex + 1} / ${_questions.length}',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: _difficultyColor(difficulty),
                    fontFamily: typo.fontFamily,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Difficulty badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _difficultyColor(difficulty).withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                difficulty[0].toUpperCase() + difficulty.substring(1),
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: _difficultyColor(difficulty),
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Question stem
            Text(
              stem,
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: colors.textPrimary,
                height: 1.5,
                fontFamily: typo.fontFamily,
              ),
            ),
            const SizedBox(height: 24),

            // Choices
            ...List.generate(choices.length, (i) {
              final isCorrect = i == correctAnswer;
              final isSelected = _selectedChoice == i;
              Color borderColor = colors.topicCardBorder;
              Color bgColor = colors.cardBg;

              if (_answered) {
                if (isCorrect) {
                  borderColor = KiwiColors.kiwiGreen;
                  bgColor = KiwiColors.kiwiGreenLight;
                } else if (isSelected && !isCorrect) {
                  borderColor = KiwiColors.coral;
                  bgColor = KiwiColors.wrongBg;
                }
              } else if (isSelected) {
                borderColor = KiwiColors.kiwiPrimary;
                bgColor = KiwiColors.kiwiPrimaryLight;
              }

              return GestureDetector(
                onTap: () => _selectChoice(i),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: bgColor,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: borderColor, width: 1.5),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 28,
                        height: 28,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isSelected ? borderColor.withOpacity(0.15) : Colors.transparent,
                          border: Border.all(color: borderColor),
                        ),
                        child: Center(
                          child: Text(
                            String.fromCharCode(65 + i), // A, B, C, D
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: borderColor,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          choices[i],
                          style: TextStyle(
                            fontSize: 14,
                            color: colors.textPrimary,
                            fontFamily: typo.fontFamily,
                          ),
                        ),
                      ),
                      if (_answered && isCorrect)
                        const Icon(Icons.check_circle, color: KiwiColors.kiwiGreen, size: 22),
                      if (_answered && isSelected && !isCorrect)
                        const Icon(Icons.cancel, color: KiwiColors.coral, size: 22),
                    ],
                  ),
                ),
              );
            }),

            const Spacer(),

            // Next button
            if (_answered)
              SizedBox(
                width: double.infinity,
                child: Container(
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
                    ),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: ElevatedButton(
                    onPressed: _nextQuestion,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    child: Text(
                      _currentIndex < _questions.length - 1 ? 'Next' : 'Finish',
                      style: const TextStyle(
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

  Color _difficultyColor(String tier) {
    switch (tier) {
      case 'warmup':
        return KiwiColors.kiwiGreen;
      case 'practice':
        return KiwiColors.kiwiPrimary;
      case 'challenge':
        return KiwiColors.indigo;
      default:
        return KiwiColors.kiwiPrimary;
    }
  }
}
