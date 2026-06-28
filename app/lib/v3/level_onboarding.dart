// Grade-first onboarding + a reusable level switcher.
//
// The whole app is scoped to ONE chosen level (L1-L8). Onboarding leads with
// the child's grade — which a parent always knows — and auto-recommends the
// matching level (with the exams it targets), so the user makes one easy
// choice instead of scanning eight cards. The same chooser is reused by the
// header chip + Profile to change level later.

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/level_service.dart';

const _orange = Color(0xFFFF6D00);
const _orangeD = Color(0xFFE65100);
const _ink = Color(0xFF1E2330);
const _muted = Color(0xFF7C8597);
const _line = Color(0xFFECEAE3);

const kPrefSelectedLevel = 'v3_selected_level';
const kPrefGrade = 'v3_grade';

/// Persist the chosen level locally (instant) + to the backend profile.
Future<void> saveSelectedLevel(LevelService svc, String userId,
    {required String level, int? grade}) async {
  final p = await SharedPreferences.getInstance();
  await p.setString(kPrefSelectedLevel, level);
  if (grade != null) await p.setInt(kPrefGrade, grade);
  try {
    await svc.setSettings(userId, selectedLevel: level, grade: grade);
  } catch (_) {/* offline — prefs still hold it; backend syncs next time */}
}

Map<String, dynamic>? recommendLevelForGrade(List<dynamic> levels, int g) {
  // exact band match first (and available)
  for (final l in levels) {
    final m = l as Map;
    final gmin = m['grade_min'], gmax = m['grade_max'];
    if (gmin is int && gmax is int && g >= gmin && g <= gmax && m['available'] == true) {
      return Map<String, dynamic>.from(m);
    }
  }
  // else the nearest available level by grade_min
  Map<String, dynamic>? best;
  int bestDist = 9999;
  for (final l in levels) {
    final m = l as Map;
    if (m['available'] != true) continue;
    final gmin = m['grade_min'] is int ? m['grade_min'] as int : 99;
    final d = (gmin - g).abs();
    if (d < bestDist) {
      bestDist = d;
      best = Map<String, dynamic>.from(m);
    }
  }
  return best;
}

String bandName(String? levelName) =>
    (levelName ?? '').replaceAll('Olympiad ', '').replaceAll('(', '').replaceAll(')', '');

// ===========================================================================
// First-run onboarding screen
// ===========================================================================
class LevelOnboarding extends StatefulWidget {
  final String userId;
  final LevelService svc;
  final void Function(String level, int? grade) onDone;
  const LevelOnboarding({super.key, required this.userId, required this.svc, required this.onDone});

  @override
  State<LevelOnboarding> createState() => _LevelOnboardingState();
}

class _LevelOnboardingState extends State<LevelOnboarding> {
  List<dynamic> _levels = [];
  bool _loading = true;
  int? _grade;
  String? _level; // chosen level code
  bool _showAll = false;

  @override
  void initState() {
    super.initState();
    widget.svc.getLevels().then((ls) {
      if (mounted) setState(() {
        _levels = ls;
        _loading = false;
      });
    }).catchError((_) {
      if (mounted) setState(() => _loading = false);
    });
  }

  void _pickGrade(int g) {
    final rec = recommendLevelForGrade(_levels, g);
    setState(() {
      _grade = g;
      _level = rec == null ? null : '${rec['level']}';
      _showAll = false;
    });
  }

  Map<String, dynamic>? get _chosen {
    for (final l in _levels) {
      if ('${(l as Map)['level']}' == _level) return Map<String, dynamic>.from(l);
    }
    return null;
  }

  Future<void> _start() async {
    if (_level == null) return;
    await saveSelectedLevel(widget.svc, widget.userId, level: _level!, grade: _grade);
    widget.onDone(_level!, _grade);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    return Scaffold(
      backgroundColor: const Color(0xFFFAFAF7),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
          children: [
            const Text('Welcome to Kiwimath 🥝',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: _ink)),
            const SizedBox(height: 4),
            const Text("Let's set things up so you only see what's right for you.",
                style: TextStyle(color: _muted, fontWeight: FontWeight.w700)),
            const SizedBox(height: 24),
            const Text('Which grade is the learner in?',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: _ink)),
            const SizedBox(height: 12),
            Wrap(spacing: 8, runSpacing: 8, children: [
              for (int g = 1; g <= 12; g++)
                ChoiceChip(
                  label: Text('Grade $g'),
                  selected: _grade == g,
                  onSelected: (_) => _pickGrade(g),
                  selectedColor: const Color(0xFFFFE9D6),
                  labelStyle: TextStyle(
                      fontWeight: FontWeight.w800,
                      color: _grade == g ? _orangeD : _ink),
                ),
            ]),
            if (_grade != null) ...[
              const SizedBox(height: 26),
              const Text('Your recommended level',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: _ink)),
              const SizedBox(height: 6),
              const Text('This is what the whole app will show. You can change it any time.',
                  style: TextStyle(color: _muted, fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 12),
              if (_chosen != null)
                LevelCard(level: _chosen!, selected: true, onTap: () {}),
              if (_chosen == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 10),
                  child: Text('No level is available for that grade yet — pick one below.',
                      style: TextStyle(color: _muted, fontWeight: FontWeight.w700)),
                ),
              const SizedBox(height: 6),
              TextButton.icon(
                onPressed: () => setState(() => _showAll = !_showAll),
                icon: Icon(_showAll ? Icons.expand_less : Icons.expand_more, size: 20),
                label: Text(_showAll ? 'Hide other levels' : 'Choose a different level'),
              ),
              if (_showAll)
                for (final l in _levels)
                  if ('${(l as Map)['level']}' != _level)
                    LevelCard(
                      level: Map<String, dynamic>.from(l),
                      selected: false,
                      onTap: (l)['available'] == true
                          ? () => setState(() => _level = '${(l)['level']}')
                          : null,
                    ),
            ],
            const SizedBox(height: 26),
            FilledButton(
              style: FilledButton.styleFrom(
                  backgroundColor: _orange, padding: const EdgeInsets.symmetric(vertical: 15)),
              onPressed: _level == null ? null : _start,
              child: const Text('Start learning →',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }
}

// ===========================================================================
// Reusable level card
// ===========================================================================
class LevelCard extends StatelessWidget {
  final Map<String, dynamic> level;
  final bool selected;
  final VoidCallback? onTap;
  const LevelCard({super.key, required this.level, required this.selected, this.onTap});

  @override
  Widget build(BuildContext context) {
    final available = level['available'] == true;
    final exams = (level['exams'] as List<dynamic>? ?? []).map((e) => '$e').toList();
    final grades = '${level['grades'] ?? ''}';
    final emoji = '${level['emoji'] ?? ''}';
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          padding: const EdgeInsets.all(15),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFFFFF6EE) : (available ? Colors.white : const Color(0xFFF7F7F4)),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: selected ? _orange : _line, width: selected ? 2 : 1),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Text(emoji.isEmpty ? '📘' : emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(bandName(level['level_name'] as String?),
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5, color: _ink)),
                  if (grades.isNotEmpty)
                    Text('Grades $grades',
                        style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 12.5)),
                ]),
              ),
              if (selected) const Icon(Icons.check_circle, color: _orange),
              if (!available)
                const Text('Soon', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 12)),
            ]),
            if ('${level['tagline'] ?? ''}'.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text('${level['tagline']}',
                  style: const TextStyle(color: _ink, fontWeight: FontWeight.w600, fontSize: 13.5)),
            ],
            if (exams.isNotEmpty) ...[
              const SizedBox(height: 9),
              Wrap(spacing: 6, runSpacing: 6, children: [
                for (final e in exams)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                    decoration: BoxDecoration(
                        color: const Color(0xFFF1F3F7), borderRadius: BorderRadius.circular(999)),
                    child: Text(e,
                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 11.5, color: _muted)),
                  ),
              ]),
            ],
          ]),
        ),
      ),
    );
  }
}

// ===========================================================================
// Level switcher (bottom sheet) — used by the header chip + Profile
// ===========================================================================
Future<Map<String, dynamic>?> showLevelChooser(
    BuildContext context, List<dynamic> levels, String? current) {
  return showModalBottomSheet<Map<String, dynamic>>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
    builder: (c) => DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      maxChildSize: 0.92,
      builder: (c, ctrl) => ListView(
        controller: ctrl,
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 24),
        children: [
          Center(
            child: Container(
              width: 40, height: 4,
              decoration: BoxDecoration(color: _line, borderRadius: BorderRadius.circular(4)),
            ),
          ),
          const SizedBox(height: 14),
          const Text('Choose your level',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: _ink)),
          const SizedBox(height: 4),
          const Text('The whole app will focus on this level.',
              style: TextStyle(color: _muted, fontWeight: FontWeight.w600)),
          const SizedBox(height: 14),
          for (final l in levels)
            LevelCard(
              level: Map<String, dynamic>.from(l as Map),
              selected: '${l['level']}' == current,
              onTap: l['available'] == true
                  ? () => Navigator.pop(c, Map<String, dynamic>.from(l))
                  : null,
            ),
        ],
      ),
    ),
  );
}
