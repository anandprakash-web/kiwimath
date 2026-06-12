import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/pillar_progress.dart';
import '../services/pillar_api.dart';
import '../theme/kiwi_theme.dart';
import 'worksheet_solve_screen.dart';

/// Level Topic Screen — shows topics for a pillar + level.
///
/// Each topic card has:
///   - Topic name + tagline
///   - Question count
///   - "Start Practice" button
///
/// Tapping a topic fetches the worksheet and opens WorksheetSolveScreen.
class LevelTopicScreen extends StatefulWidget {
  final String userId;
  final PillarMeta pillar;
  final int level;
  final int grade;
  final List<Map<String, dynamic>> topics;

  const LevelTopicScreen({
    super.key,
    required this.userId,
    required this.pillar,
    required this.level,
    required this.grade,
    required this.topics,
  });

  @override
  State<LevelTopicScreen> createState() => _LevelTopicScreenState();
}

class _LevelTopicScreenState extends State<LevelTopicScreen> {
  String? _loadingTopic; // topic ID currently loading

  static const _levelNames = ['', 'Foundation', 'Explorer', 'Challenger', 'Advanced', 'Olympiad'];

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.grade);
    final colors = tier.colors;
    final typo = tier.typography;
    final pillarColor = Color(int.parse('FF${widget.pillar.colorHex}', radix: 16));
    final levelName = widget.level < _levelNames.length
        ? _levelNames[widget.level]
        : 'Level ${widget.level}';

    return Scaffold(
      backgroundColor: colors.background,
      appBar: AppBar(
        backgroundColor: colors.background,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_rounded, color: colors.textPrimary, size: 20),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${widget.pillar.emoji} $levelName',
              style: TextStyle(
                fontSize: typo.headlineSize,
                fontWeight: FontWeight.w800,
                color: colors.textPrimary,
                fontFamily: typo.fontFamily,
              ),
            ),
            Text(
              '${widget.pillar.name} \u{2022} Level ${widget.level}',
              style: TextStyle(
                fontSize: typo.chipSize - 2,
                color: colors.textMuted,
                fontFamily: typo.fontFamily,
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: ListView.separated(
          padding: EdgeInsets.all(KiwiSpacing.lg),
          itemCount: widget.topics.length,
          separatorBuilder: (_, __) => SizedBox(height: KiwiSpacing.md),
          itemBuilder: (context, index) {
            final topic = widget.topics[index];
            return _TopicCard(
              topic: topic,
              isLoading: _loadingTopic == topic['id'],
              pillarColor: pillarColor,
              colors: colors,
              typo: typo,
              tier: tier,
              onTap: () => _startTopic(topic),
            );
          },
        ),
      ),
    );
  }

  Future<void> _startTopic(Map<String, dynamic> topic) async {
    final topicId = topic['id'] as String;
    HapticFeedback.mediumImpact();
    setState(() => _loadingTopic = topicId);

    try {
      final worksheet = await PillarApi.fetchWorksheet(
        pillar: widget.pillar.id,
        level: widget.level,
        topic: topicId,
      );

      if (!mounted) return;
      setState(() => _loadingTopic = null);

      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => WorksheetSolveScreen(
            worksheet: worksheet,
            grade: widget.grade,
            userId: widget.userId,
          ),
        ),
      );
    } catch (e) {
      if (mounted) {
        setState(() => _loadingTopic = null);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('No questions available yet for this topic'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }
}

// =============================================================================
// Topic card
// =============================================================================
class _TopicCard extends StatelessWidget {
  final Map<String, dynamic> topic;
  final bool isLoading;
  final Color pillarColor;
  final KiwiTierColors colors;
  final KiwiTierTypography typo;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _TopicCard({
    required this.topic,
    required this.isLoading,
    required this.pillarColor,
    required this.colors,
    required this.typo,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final name = topic['name'] as String? ?? '';
    final tagline = topic['tagline'] as String? ?? '';
    final questionCount = topic['question_count'] as int? ?? 0;

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(tier.shape.cardRadius),
      child: InkWell(
        onTap: isLoading ? null : onTap,
        borderRadius: BorderRadius.circular(tier.shape.cardRadius),
        child: Container(
          padding: EdgeInsets.all(KiwiSpacing.lg),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(tier.shape.cardRadius),
            border: Border.all(color: colors.topicCardBorder),
            boxShadow: [
              BoxShadow(
                color: pillarColor.withOpacity(0.06),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Row(
            children: [
              // Color dot
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: pillarColor,
                  shape: BoxShape.circle,
                ),
              ),
              SizedBox(width: KiwiSpacing.md),

              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        fontSize: typo.topicNameSize,
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    if (tagline.isNotEmpty) ...[
                      SizedBox(height: KiwiSpacing.xs - 2),
                      Text(
                        tagline,
                        style: TextStyle(
                          fontSize: typo.chipSize - 1,
                          color: colors.textMuted,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                    ],
                    SizedBox(height: KiwiSpacing.xs),
                    Text(
                      '$questionCount questions',
                      style: TextStyle(
                        fontSize: typo.chipSize - 2,
                        fontWeight: FontWeight.w600,
                        color: pillarColor,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ],
                ),
              ),

              // Action
              if (isLoading)
                SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation(pillarColor),
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: pillarColor,
                    borderRadius: BorderRadius.circular(tier.shape.buttonRadius),
                  ),
                  child: Text(
                    'Start',
                    style: TextStyle(
                      fontSize: typo.chipSize - 2,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                      fontFamily: typo.fontFamily,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
