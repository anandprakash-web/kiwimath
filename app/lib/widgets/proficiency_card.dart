import 'package:flutter/material.dart';

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
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
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
                    borderRadius: BorderRadius.circular(16),
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
                          color: Colors.grey[800],
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
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  Text(
                    nextLevel,
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: progress / 100.0,
                  minHeight: 10,
                  backgroundColor: Colors.grey[200],
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '$progress% to $nextLevel',
                style: TextStyle(fontSize: 11, color: Colors.grey[500]),
              ),
            ],

            const SizedBox(height: 16),

            // Description
            Text(
              description,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[700],
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
                  color: Colors.grey[800],
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
                                fontSize: 13, color: Colors.grey[700]),
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
                  color: Colors.grey[800],
                ),
              ),
              const SizedBox(height: 8),
              ...nextSteps.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.arrow_forward,
                            size: 14, color: Colors.blue[400]),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            item,
                            style: TextStyle(
                                fontSize: 13, color: Colors.grey[700]),
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
        color = Colors.green;
        break;
      case 'declining':
        icon = Icons.trending_down;
        color = Colors.red;
        break;
      default:
        icon = Icons.trending_flat;
        color = Colors.orange;
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
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
                  style: TextStyle(fontSize: 12, color: Colors.grey[700]),
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
            color: Colors.grey[800],
          ),
        ),
        const SizedBox(height: 12),
        _CompetencyBar(
          label: 'Knowing',
          subtitle: 'Recall & Compute',
          data: competency['knowing'] ?? {},
          color: Colors.blue,
        ),
        const SizedBox(height: 8),
        _CompetencyBar(
          label: 'Applying',
          subtitle: 'Use & Solve',
          data: competency['applying'] ?? {},
          color: Colors.green,
        ),
        const SizedBox(height: 8),
        _CompetencyBar(
          label: 'Reasoning',
          subtitle: 'Analyze & Justify',
          data: competency['reasoning'] ?? {},
          color: Colors.purple,
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
                      color: Colors.grey[800])),
              Text(subtitle,
                  style: TextStyle(fontSize: 10, color: Colors.grey[500])),
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
              backgroundColor: Colors.grey[200],
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
              color: Colors.grey[700],
            ),
          ),
        ),
      ],
    );
  }
}
