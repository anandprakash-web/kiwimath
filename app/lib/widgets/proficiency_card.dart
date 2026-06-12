import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';

/// Displays the student's proficiency level with visual progress indicator.
class ProficiencyCard extends StatelessWidget {
  final Map<String, dynamic> proficiency;
  final Map<String, dynamic>? competency;
  final Map<String, dynamic>? growth;

  const ProficiencyCard({
    super.key,
    required this.proficiency,
    this.competency,
    this.growth,
  });

  Color _hexToColor(String hex) {
    hex = hex.replaceAll('#', '');
    return Color(int.parse('FF$hex', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    final level = proficiency['level'] ?? 1;
    final name = proficiency['name'] ?? 'Explorer';
    final emoji = proficiency['emoji'] ?? '🌱';
    final color = _hexToColor(proficiency['color'] ?? 'EF4444');
    final scaleScore = proficiency['scale_score'] ?? 500;
    final description = proficiency['description'] ?? '';
    final progress = proficiency['progress_in_level'] ?? 0;
    final nextLevel = proficiency['next_level_name'];
    final canDo = List<String>.from(proficiency['can_do'] ?? []);
    final nextSteps = List<String>.from(proficiency['next_steps'] ?? []);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(KiwiSpacing.lg)),
      child: Padding(
        padding: EdgeInsets.all(KiwiSpacing.xl - 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header: Level badge + name + scale score
            Row(
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(KiwiSpacing.lg),
                  ),
                  child: Center(
                    child: Text(emoji, style: const TextStyle(fontSize: 28)),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            'Level $level',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: color,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              name,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: color,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Scale Score: $scaleScore',
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: KiwiColors.textDark,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Progress bar to next level
            if (nextLevel != null) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    name,
                    style: TextStyle(fontSize: 12, color: KiwiColors.textMuted),
                  ),
                  Text(
                    nextLevel,
                    style: TextStyle(fontSize: 12, color: KiwiColors.textMuted),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: progress / 100.0,
                  minHeight: 10,
                  backgroundColor: KiwiColors.pathLocked,
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '$progress% to $nextLevel',
                style: TextStyle(fontSize: 11, color: KiwiColors.textMuted),
              ),
            ],

            const SizedBox(height: 16),

            // Description
            Text(
              description,
              style: TextStyle(
                fontSize: 14,
                color: KiwiColors.textMid,
                height: 1.4,
              ),
            ),

            // Growth indicator
            if (growth != null && growth!['has_growth_data'] == true) ...[
              const SizedBox(height: 16),
              _GrowthIndicator(growth: growth!),
            ],

            // Competency breakdown
            if (competency != null) ...[
              const SizedBox(height: 20),
              _CompetencyBreakdown(competency: competency!),
            ],

            // What your child can do
            if (canDo.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(
                'What your child can do:',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textDark,
                ),
              ),
              const SizedBox(height: 8),
              ...canDo.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.check_circle, size: 16, color: color),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            item,
                            style: TextStyle(
                                fontSize: 13, color: KiwiColors.textMid),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],

            // Next steps
            if (nextSteps.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Recommended next steps:',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textDark,
                ),
              ),
              const SizedBox(height: 8),
              ...nextSteps.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.arrow_forward,
                            size: 14, color: KiwiColors.sky),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            item,
                            style: TextStyle(
                                fontSize: 13, color: KiwiColors.textMid),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    );
  }
}

class _GrowthIndicator extends StatelessWidget {
  final Map<String, dynamic> growth;

  const _GrowthIndicator({required this.growth});

  @override
  Widget build(BuildContext context) {
    final trajectory = growth['trajectory'] ?? 'steady';
    final scaleChange = growth['scale_score_change'] ?? 0;
    final message = growth['message'] ?? '';

    IconData icon;
    Color color;

    switch (trajectory) {
      case 'improving':
        icon = Icons.trending_up;
        color = KiwiColors.kiwiGreen;
        break;
      case 'declining':
        icon = Icons.trending_down;
        color = KiwiColors.coral;
        break;
      default:
        icon = Icons.trending_flat;
        color = KiwiColors.amber;
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(KiwiSpacing.md),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  scaleChange > 0
                      ? '+$scaleChange points'
                      : '$scaleChange points',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
                Text(
                  message,
                  style: TextStyle(fontSize: 12, color: KiwiColors.textMid),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CompetencyBreakdown extends StatelessWidget {
  final Map<String, dynamic> competency;

  const _CompetencyBreakdown({required this.competency});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Competency Breakdown',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: KiwiColors.textDark,
          ),
        ),
        const SizedBox(height: 12),
        _CompetencyBar(
          label: 'Knowing',
          subtitle: 'Recall & Compute',
          data: competency['knowing'] ?? {},
          color: KiwiColors.sky,
        ),
        const SizedBox(height: 8),
        _CompetencyBar(
          label: 'Applying',
          subtitle: 'Use & Solve',
          data: competency['applying'] ?? {},
          color: KiwiColors.kiwiGreen,
        ),
        const SizedBox(height: 8),
        _CompetencyBar(
          label: 'Reasoning',
          subtitle: 'Analyze & Justify',
          data: competency['reasoning'] ?? {},
          color: KiwiColors.indigo,
        ),
      ],
    );
  }
}

class _CompetencyBar extends StatelessWidget {
  final String label;
  final String subtitle;
  final Map<String, dynamic> data;
  final Color color;

  const _CompetencyBar({
    required this.label,
    required this.subtitle,
    required this.data,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final accuracy = (data['accuracy'] ?? 0).toDouble();
    final total = data['total'] ?? 0;
    final mastery = data['mastery'] ?? 'not_enough_data';

    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: KiwiColors.textDark)),
              Text(subtitle,
                  style: TextStyle(fontSize: 10, color: KiwiColors.textMuted)),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: total > 0 ? accuracy / 100.0 : 0,
              minHeight: 8,
              backgroundColor: KiwiColors.pathLocked,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ),
        const SizedBox(width: 8),
        SizedBox(
          width: 44,
          child: Text(
            total > 0 ? '${accuracy.round()}%' : '--',
            textAlign: TextAlign.right,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: KiwiColors.textMid,
            ),
          ),
        ),
      ],
    );
  }
}
