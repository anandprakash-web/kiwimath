// Kiwimath v3 — self-contained 4-tab app on the /v3 Level/Grade API.
//
// Tabs: Olympiad (Levels L1–L8) · School (Grades) · Progress · Profile.
// One economy: the wallet lives in the shell; practising updates it and every
// tab reads the same numbers (no disjoint). Talks only to /v3 via LevelService.

import 'dart:async';
import 'dart:convert';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_math_fork/flutter_math.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/contest_service.dart';
import '../services/level_service.dart';
import 'books_browse.dart';
import 'celebration.dart';
import 'challenge_screen.dart';
import 'contest_screens.dart';
import 'level_onboarding.dart';

const _orange = Color(0xFFFF6D00);
const _orangeD = Color(0xFFE65100);
const _ink = Color(0xFF1E2330);
const _muted = Color(0xFF7C8597);
const _line = Color(0xFFECEAE3);
const _green = Color(0xFF0FB17E);
const _blue = Color(0xFF3D7DF6);
const _tabTitles = ['Olympiad', 'School', 'Library', 'Progress', 'Profile'];

Color _pillarColor(String? p) {
  switch (p) {
    case 'NT':
      return _blue;
    case 'ALG':
      return const Color(0xFF8B5CF6);
    case 'GEO':
      return _green;
    case 'COM':
      return const Color(0xFFF59E0B);
    case 'LOGIC':
      return const Color(0xFFEC4899);
    default:
      return _muted;
  }
}

String _bandName(String? levelName) =>
    (levelName ?? '').replaceAll('Olympiad ', '').replaceAll('(', '').replaceAll(')', '');

int _asInt(dynamic v) => v is num ? v.toInt() : int.tryParse('$v') ?? 0;

// ===========================================================================
// Shell
// ===========================================================================
class KiwiV3Shell extends StatefulWidget {
  final String userId;
  const KiwiV3Shell({super.key, required this.userId});

  @override
  State<KiwiV3Shell> createState() => _KiwiV3ShellState();
}

class _KiwiV3ShellState extends State<KiwiV3Shell> {
  final LevelService _svc = LevelService();
  int _tab = 0;
  Map<String, dynamic> _wallet = {};
  List<dynamic> _levels = [];
  String? _level; // the chosen level — scopes the whole app; null until onboarded
  bool _bootstrapping = true;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    CelebrationPrefs.load(); // load the confetti/sound preferences once
    try {
      _levels = await _svc.getLevels();
    } catch (_) {/* offline — onboarding/switcher will show empty, handled */}
    // Selected level: prefs first (instant), then the backend profile.
    String? lvl;
    try {
      final p = await SharedPreferences.getInstance();
      lvl = p.getString(kPrefSelectedLevel);
    } catch (_) {}
    if (lvl == null) {
      try {
        final s = await _svc.getSettings(widget.userId);
        final sl = s['selected_level'];
        if (sl is String && sl.isNotEmpty) {
          lvl = sl;
          final p = await SharedPreferences.getInstance();
          await p.setString(kPrefSelectedLevel, sl);
        }
      } catch (_) {}
    }
    if (mounted) setState(() {
      _level = lvl;
      _bootstrapping = false;
    });
    _refreshWallet();
  }

  Map<String, dynamic>? get _levelMeta {
    for (final l in _levels) {
      if ('${(l as Map)['level']}' == _level) return Map<String, dynamic>.from(l);
    }
    return null;
  }

  String get _levelName => _bandName(_levelMeta?['level_name'] as String?);
  String get _levelGrades => '${_levelMeta?['grades'] ?? ''}';   // e.g. "5–6" — the level's band

  // School content is Grades 1-6; map the level's band into that range.
  int get _gradeForLevel {
    final g = _levelMeta?['grade_min'];
    return (g is int) ? g.clamp(1, 6) : 3;
  }

  void _onboarded(String level, int? grade) {
    if (mounted) setState(() => _level = level);
    _refreshWallet();
  }

  Future<void> _changeLevel() async {
    final picked = await showLevelChooser(context, _levels, _level);
    if (picked == null) return;
    final lvl = '${picked['level']}';
    await saveSelectedLevel(_svc, widget.userId, level: lvl);
    if (mounted) setState(() {
      _level = lvl;
      _tab = 0;
    });
  }

  Future<void> _refreshWallet() async {
    try {
      final w = await _svc.getWallet(widget.userId);
      if (mounted) setState(() => _wallet = w);
    } catch (_) {/* offline / first run — leave empty */}
  }

  void _onWallet(Map<String, dynamic> w) {
    if (mounted) setState(() => _wallet = w);
  }

  Widget _levelChip() {
    return InkWell(
      onTap: _changeLevel,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF1E3),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text('${_level ?? ''}',
              style: const TextStyle(color: _orangeD, fontWeight: FontWeight.w800, fontSize: 13)),
          const Icon(Icons.expand_more, size: 16, color: _orangeD),
        ]),
      ),
    );
  }

  Widget _chip(IconData icon, Object? value, Color c) {
    return Container(
      margin: const EdgeInsets.only(left: 8),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: _line),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 16, color: c),
        const SizedBox(width: 4),
        Text('${value ?? 0}',
            style: TextStyle(fontWeight: FontWeight.w800, color: c, fontSize: 13)),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_bootstrapping) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    // First run (or signed-in but never chose a level) → onboarding.
    if (_level == null) {
      return LevelOnboarding(userId: widget.userId, svc: _svc, onDone: _onboarded);
    }
    final tabs = [
      OlympiadTab(
          userId: widget.userId, svc: _svc, onWallet: _onWallet,
          level: _level!, levelName: _levelName, onChangeLevel: _changeLevel,
          wallet: _wallet),
      SchoolTab(
          userId: widget.userId, svc: _svc, onWallet: _onWallet,
          initialGrade: _gradeForLevel),
      BooksBrowseBody(lockedLevel: _level),
      ProgressTab(userId: widget.userId, svc: _svc, level: _level),
      ProfileTab(
          userId: widget.userId, wallet: _wallet, svc: _svc,
          level: _level!, levelName: _levelName, grades: _levelGrades, onChangeLevel: _changeLevel),
    ];
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFFFAFAF7),
        elevation: 0,
        title: Row(children: [
          Flexible(
            child: Text(_tabTitles[_tab],
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: _ink, fontWeight: FontWeight.w800)),
          ),
          const SizedBox(width: 10),
          _levelChip(),
        ]),
        actions: [
          _chip(Icons.local_fire_department, _wallet['streak_current'], _orange),
          _chip(Icons.monetization_on, _wallet['kiwi_coins'], _orangeD),
          const SizedBox(width: 10),
        ],
      ),
      body: IndexedStack(index: _tab, children: tabs),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.star_border), selectedIcon: Icon(Icons.star), label: 'Olympiad'),
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'School'),
          NavigationDestination(icon: Icon(Icons.menu_book_outlined), selectedIcon: Icon(Icons.menu_book), label: 'Library'),
          NavigationDestination(icon: Icon(Icons.bar_chart_outlined), selectedIcon: Icon(Icons.bar_chart), label: 'Progress'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}

// ===========================================================================
// Olympiad tab — Level picker → Topics → Practice
// ===========================================================================
class OlympiadTab extends StatelessWidget {
  final String userId;
  final LevelService svc;
  final void Function(Map<String, dynamic>) onWallet;
  final String level;
  final String levelName;
  final VoidCallback onChangeLevel;
  final Map<String, dynamic> wallet;
  const OlympiadTab({
    super.key,
    required this.userId,
    required this.svc,
    required this.onWallet,
    required this.level,
    required this.levelName,
    required this.onChangeLevel,
    required this.wallet,
  });

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<dynamic>>(
      future: svc.getLevelTopics(level),
      builder: (context, snap) {
        if (!snap.hasData) return _loadingOrError(snap, 'topics');
        final topics = snap.data!;
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
          children: [
            _hero(context),
            const SizedBox(height: 12),
            _CompeteBanner(userId: userId, level: level),
            const SizedBox(height: 10),
            _climbEntry(context),
            const SizedBox(height: 18),
            const Text('TOPICS', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, letterSpacing: 1, fontSize: 12)),
            const SizedBox(height: 10),
            if (topics.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Text('Topics for this level are coming soon.',
                    textAlign: TextAlign.center, style: TextStyle(color: _muted, fontWeight: FontWeight.w700)),
              )
            else
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 11,
                crossAxisSpacing: 11,
                childAspectRatio: 1.45,
                children: [for (final t in topics) _topicCard(context, t as Map<String, dynamic>)],
              ),
          ],
        );
      },
    );
  }

  Widget _hero(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFFF8A2B), _orange, _orangeD],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(22),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(
            child: Text(levelName,
                style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
          ),
          InkWell(
            onTap: onChangeLevel,
            borderRadius: BorderRadius.circular(999),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
              decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(999)),
              child: const Row(mainAxisSize: MainAxisSize.min, children: [
                Text('Change', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 12.5)),
                Icon(Icons.expand_more, size: 16, color: Colors.white),
              ]),
            ),
          ),
        ]),
        const SizedBox(height: 8),
        Row(children: [
          const Icon(Icons.local_fire_department, color: Colors.white, size: 19),
          const SizedBox(width: 5),
          Expanded(
            child: Text(_streakLine(),
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13.5)),
          ),
        ]),
      ]),
    );
  }

  // The streak nudge — the visible reason to come back tomorrow.
  String _streakLine() {
    final s = (wallet['streak_current'] as num?)?.toInt() ?? 0;
    final doneToday = wallet['practiced_today'] == true;
    if (s <= 0) return 'Start your streak — solve 1 today';
    if (doneToday) return '$s-day streak — nice! See you tomorrow';
    return '$s-day streak — solve 1 today to keep it';
  }

  // (The daily-contest banner is the top-level _CompeteBanner widget below —
  // it carries today's live state, so it can't be a const here.)

  // Entry to The Climb — the adaptive Challenge (separate from the ladder).
  Widget _climbEntry(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
              builder: (_) => ChallengeScreen(userId: userId, level: level, levelName: levelName))),
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: _line),
        ),
        child: Row(children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(color: const Color(0xFFFFF1E3), borderRadius: BorderRadius.circular(12)),
            child: const Icon(Icons.terrain, color: _orange),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('The Climb', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5)),
              Text('A 10-question adaptive challenge — find your peak',
                  style: TextStyle(color: _muted, fontWeight: FontWeight.w600, fontSize: 12.5)),
            ]),
          ),
          const Icon(Icons.chevron_right, color: _muted),
        ]),
      ),
    );
  }

  Widget _topicCard(BuildContext context, Map<String, dynamic> t) {
    final available = t['available'] == true;
    final color = _pillarColor(t['pillar'] as String?);
    return InkWell(
      onTap: available
          ? () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => PracticePage(
                  title: '${t['display_name']}',
                  userId: userId,
                  svc: svc,
                  onWallet: onWallet,
                  level: level,
                  topicKey: '${t['topic_key']}',
                ),
              ))
          : null,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: available ? Colors.white : const Color(0xFFF7F7F4),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: _line),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            width: 36, height: 36,
            decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(11)),
            child: Icon(Icons.calculate_outlined, size: 20, color: color),
          ),
          const Spacer(),
          Text('${t['display_name']}',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14.5, color: available ? _ink : const Color(0xFFAEB4C1))),
          const SizedBox(height: 4),
          Text(available ? 'Practice' : 'Coming soon',
              style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 12)),
        ]),
      ),
    );
  }
}

// The daily-contest banner. Shows today's *live* state — LIVE now / opens in Hh Mm /
// played today — so the 6 PM contest is a real reason to come back. Reads
// /v3/contest/today and ticks every 30s to keep the countdown honest; re-fetches
// when the open/close boundary passes. Falls back to a static label when offline.
class _CompeteBanner extends StatefulWidget {
  final String userId;
  final String level;
  const _CompeteBanner({required this.userId, required this.level});
  @override
  State<_CompeteBanner> createState() => _CompeteBannerState();
}

class _CompeteBannerState extends State<_CompeteBanner> {
  final _svc = ContestService();
  Map<String, dynamic>? _status;
  Timer? _tick;

  @override
  void initState() {
    super.initState();
    _load();
    _tick = Timer.periodic(const Duration(seconds: 30), (_) {
      if (!mounted) return;
      final s = _status;
      if (s != null) {
        final opens = DateTime.tryParse('${s['opens_at'] ?? ''}');
        final closes = DateTime.tryParse('${s['closes_at'] ?? ''}');
        final now = DateTime.now();
        final st = '${s['status']}';
        // The window just opened or closed → re-fetch the authoritative state.
        if ((st != 'live' && opens != null && now.isAfter(opens)) ||
            (st == 'live' && closes != null && now.isAfter(closes))) {
          _load();
          return;
        }
      }
      setState(() {}); // otherwise just repaint so the countdown text updates
    });
  }

  Future<void> _load() async {
    try {
      final s = await _svc.getContestToday(widget.userId, widget.level);
      if (mounted) setState(() => _status = s);
    } catch (_) {/* offline — keep the static fallback */}
  }

  @override
  void dispose() {
    _tick?.cancel();
    super.dispose();
  }

  String _fmt(Duration d) {
    final h = d.inHours;
    final m = d.inMinutes % 60;
    if (h > 0) return '${h}h ${m}m';
    if (m > 0) return '${m}m';
    return 'under a minute';
  }

  @override
  Widget build(BuildContext context) {
    final s = _status;
    String title = 'Compete';
    String subtitle = 'Daily Contest · 6 PM · Weekly League';
    bool live = false;
    IconData icon = Icons.emoji_events_outlined;

    if (s != null) {
      final attempted = s['attempted'] == true;
      final st = '${s['status']}';
      if (attempted) {
        title = 'Played today';
        subtitle = 'See the leaderboard & your league';
        icon = Icons.check_circle_outline;
      } else if (st == 'live') {
        title = 'Daily Contest is LIVE';
        subtitle = 'Play now · one attempt today';
        live = true;
        icon = Icons.bolt;
      } else {
        final opens = DateTime.tryParse('${s['opens_at'] ?? ''}');
        if (opens != null && opens.isAfter(DateTime.now())) {
          title = 'Daily Contest';
          subtitle = 'Opens in ${_fmt(opens.difference(DateTime.now()))}';
        } else if (st == 'closed') {
          title = 'Daily Contest';
          subtitle = 'Closed for today · back at 6 PM';
        }
      }
    }

    return InkWell(
      onTap: () => Navigator.push(
          context, MaterialPageRoute(builder: (_) => CompeteHubScreen(userId: widget.userId))),
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: live ? _orange : _line, width: live ? 1.4 : 1),
        ),
        child: Row(children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
                color: const Color(0xFFFFF1E3), borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: _orange),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                if (live) ...[
                  Container(
                    width: 8, height: 8,
                    decoration: const BoxDecoration(color: Color(0xFFE5484D), shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 6),
                ],
                Flexible(
                  child: Text(title,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5)),
                ),
              ]),
              Text(subtitle,
                  style: const TextStyle(color: _muted, fontWeight: FontWeight.w600, fontSize: 12.5)),
            ]),
          ),
          const Icon(Icons.chevron_right, color: _muted),
        ]),
      ),
    );
  }
}

class TopicsPage extends StatelessWidget {
  final String level;
  final String levelName;
  final String userId;
  final LevelService svc;
  final void Function(Map<String, dynamic>) onWallet;
  const TopicsPage(
      {super.key,
      required this.level,
      required this.levelName,
      required this.userId,
      required this.svc,
      required this.onWallet});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Level ${level.replaceAll('L', '')} · $levelName')),
      body: FutureBuilder<List<dynamic>>(
        future: svc.getLevelTopics(level),
        builder: (context, snap) {
          if (!snap.hasData) return _loadingOrError(snap, 'topics');
          final topics = snap.data!;
          return GridView.builder(
            padding: const EdgeInsets.all(14),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2, mainAxisSpacing: 11, crossAxisSpacing: 11, childAspectRatio: 1.45,
            ),
            itemCount: topics.length,
            itemBuilder: (context, i) {
              final t = topics[i] as Map<String, dynamic>;
              final available = t['available'] == true;
              final color = _pillarColor(t['pillar'] as String?);
              return InkWell(
                onTap: available
                    ? () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => PracticePage(
                            title: '${t['display_name']}',
                            userId: userId,
                            svc: svc,
                            onWallet: onWallet,
                            level: level,
                            topicKey: '${t['topic_key']}',
                          ),
                        ))
                    : null,
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: available ? Colors.white : const Color(0xFFF7F7F4),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: _line),
                  ),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Container(
                      width: 36, height: 36,
                      decoration: BoxDecoration(color: color.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(11)),
                      child: Icon(Icons.calculate_outlined, size: 20, color: color),
                    ),
                    const Spacer(),
                    Text('${t['display_name']}',
                        style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14.5,
                            color: available ? _ink : const Color(0xFFAEB4C1))),
                    const SizedBox(height: 4),
                    Text(available ? 'Practice' : 'Coming soon',
                        style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 12)),
                  ]),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

// ===========================================================================
// School tab — Board → Grade → sequenced Chapters → Practice
// ===========================================================================
class SchoolTab extends StatefulWidget {
  final String userId;
  final LevelService svc;
  final void Function(Map<String, dynamic>) onWallet;
  final int initialGrade;
  const SchoolTab({super.key, required this.userId, required this.svc, required this.onWallet, this.initialGrade = 3});

  @override
  State<SchoolTab> createState() => _SchoolTabState();
}

class _SchoolTabState extends State<SchoolTab> {
  List<dynamic> _boards = [];
  String _board = 'ncert';
  int _grade = 3;

  @override
  void initState() {
    super.initState();
    // Default the grade to the one that matches the chosen level (the app is
    // scoped to that level); the chips still let the learner adjust in-session.
    _grade = widget.initialGrade.clamp(1, 6);
    widget.svc.getBoards().then((b) {
      if (mounted) {
        setState(() {
          _boards = b;
          if (b.isNotEmpty) _board = '${(b.first as Map)['board']}';
        });
      }
    }).catchError((_) {});
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      SizedBox(
        height: 52,
        child: ListView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          children: _boards.map((b) {
            final m = b as Map<String, dynamic>;
            final on = '${m['board']}' == _board;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text('${m['name']}'),
                selected: on,
                onSelected: (_) => setState(() => _board = '${m['board']}'),
              ),
            );
          }).toList(),
        ),
      ),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Wrap(spacing: 6, children: [
          for (int g = 1; g <= 6; g++)
            ChoiceChip(label: Text('G$g'), selected: _grade == g, onSelected: (_) => setState(() => _grade = g)),
        ]),
      ),
      Expanded(
        child: FutureBuilder<Map<String, dynamic>>(
          future: widget.svc.getChapters(_board, _grade),
          builder: (context, snap) {
            if (!snap.hasData) return _loadingOrError(snap, 'chapters');
            final chapters = (snap.data!['chapters'] as List<dynamic>? ?? []);
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 24),
              itemCount: chapters.length,
              itemBuilder: (context, i) {
                final c = chapters[i] as Map<String, dynamic>;
                final name = '${c['display_name'] ?? c['name']}';
                return Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 9),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14), side: const BorderSide(color: _line)),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFFF0F1F5),
                      child: Text('${c['index'] ?? i + 1}',
                          style: const TextStyle(color: _muted, fontWeight: FontWeight.w800)),
                    ),
                    title: Text(name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
                    trailing: const Icon(Icons.chevron_right, color: Color(0xFFC9CFDA)),
                    onTap: () async {
                      try {
                        final data = await widget.svc.getChapterQuestions(_board, _grade, name);
                        if (!context.mounted) return;
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => PracticePage(
                              title: name,
                              userId: widget.userId,
                              svc: widget.svc,
                              onWallet: widget.onWallet,
                              questions: (data['questions'] as List<dynamic>? ?? []),
                            ),
                          ),
                        );
                      } catch (_) {}
                    },
                  ),
                );
              },
            );
          },
        ),
      ),
    ]);
  }
}

// ===========================================================================
// Practice — shared question flow (olympiad adaptive OR chapter list)
// ===========================================================================
/// Renders a string that mixes prose with inline LaTeX delimited by `$...$`
/// (olympiad statements/solutions). Falls back to raw text on a TeX error.
class MathText extends StatelessWidget {
  final String text;
  final double fontSize;
  final bool bold;
  const MathText(this.text, {super.key, this.fontSize = 16, this.bold = false});

  @override
  Widget build(BuildContext context) {
    final style = TextStyle(
      fontSize: fontSize,
      fontWeight: bold ? FontWeight.w800 : FontWeight.w600,
      height: 1.4,
      color: const Color(0xFF20232A),
    );
    final parts = <Widget>[];
    final re = RegExp(r'\$+([^$]+)\$+');
    var last = 0;
    for (final m in re.allMatches(text)) {
      if (m.start > last) parts.add(Text(text.substring(last, m.start), style: style));
      parts.add(Math.tex(
        m.group(1)!.trim(),
        textStyle: style,
        mathStyle: MathStyle.text,
        onErrorFallback: (_) => Text(m.group(0)!, style: style),
      ));
      last = m.end;
    }
    if (last < text.length) parts.add(Text(text.substring(last), style: style));
    if (parts.isEmpty) parts.add(Text(text, style: style));
    return Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 2, runSpacing: 4, children: parts);
  }
}

class PracticePage extends StatefulWidget {
  final String title;
  final String userId;
  final LevelService svc;
  final void Function(Map<String, dynamic>) onWallet;
  final String? level;
  final String? topicKey;
  final List<dynamic>? questions;
  const PracticePage({
    super.key,
    required this.title,
    required this.userId,
    required this.svc,
    required this.onWallet,
    this.level,
    this.topicKey,
    this.questions,
  });

  @override
  State<PracticePage> createState() => _PracticePageState();
}

class _PracticePageState extends State<PracticePage> {
  Map<String, dynamic>? _q;
  bool _loading = true;
  int? _picked;
  Map<String, dynamic>? _result;
  bool _showHint = false;
  bool _revealed = false;
  int _idx = 0;
  final List<String> _seen = [];
  final TextEditingController _input = TextEditingController();
  // Session history for back/forward navigation through already-seen questions.
  final List<Map<String, dynamic>> _history = [];
  int _pos = -1;
  // Session stats — meaningful progress for open-ended adaptive practice.
  int _answered = 0, _correct = 0, _streak = 0;

  // Per-(user, topic/chapter) key so the journey resumes instead of restarting.
  String get _pkey => widget.questions != null
      ? 'v3prog_${widget.userId}_chap_${widget.title}'
      : 'v3prog_${widget.userId}_oly_${widget.level}_${widget.topicKey}';

  @override
  void initState() {
    super.initState();
    _restore();
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _restore() async {
    try {
      final p = await SharedPreferences.getInstance();
      _seen.addAll(p.getStringList('${_pkey}_seen') ?? const []);
      _idx = p.getInt('${_pkey}_idx') ?? 0;
    } catch (_) {}
    _forward();
  }

  Future<void> _persist() async {
    try {
      final p = await SharedPreferences.getInstance();
      final keep = _seen.length > 150 ? _seen.sublist(_seen.length - 150) : _seen;
      await p.setStringList('${_pkey}_seen', keep);
      await p.setInt('${_pkey}_idx', _idx);
    } catch (_) {}
  }

  void _show(int pos) {
    setState(() {
      _pos = pos;
      _q = _history[pos];
      _picked = null;
      _result = null;
      _showHint = false;
      _revealed = false;
      _input.clear();
    });
  }

  void _back() {
    if (_pos > 0) _show(_pos - 1);
  }

  /// Advance: step through already-seen history first, else fetch a new question.
  Future<void> _forward() async {
    if (_pos + 1 < _history.length) {
      _show(_pos + 1);
      return;
    }
    setState(() {
      _loading = true;
      _picked = null;
      _result = null;
      _showHint = false;
      _revealed = false;
      _input.clear();
    });
    try {
      Map<String, dynamic>? q;
      if (widget.questions != null) {
        if (_idx < widget.questions!.length) {
          q = Map<String, dynamic>.from(widget.questions![_idx] as Map);
          _idx++;
        }
      } else {
        final ex = _seen.length > 120 ? _seen.sublist(_seen.length - 120) : _seen;
        q = await widget.svc.getNextQuestion(widget.level!, widget.topicKey!, userId: widget.userId, exclude: ex);
      }
      if (!mounted) return;
      if (q != null) {
        _history.add(q);
        if (q['id'] != null) _seen.add('${q['id']}');
        setState(() => _loading = false);
        _show(_history.length - 1);
      } else {
        setState(() {
          _loading = false;
          _q = null;
        });
      }
      _persist();
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  /// One submit path for both MCQ (index) and integer/fill (value).
  Future<void> _submit({int? index, String? value}) async {
    if (_result != null || _q == null) return;
    if (value != null && value.trim().isEmpty) return; // nothing typed
    setState(() => _picked = index);
    try {
      final res = await widget.svc.checkAnswer(
        userId: widget.userId,
        questionId: '${_q!['id']}',
        selectedIndex: index,
        selectedValue: value == null ? null : (num.tryParse(value.trim()) ?? value.trim()),
      );
      if (!mounted) return;
      setState(() {
        _result = res;
        _answered++;
        if (res['correct'] == true) {
          _correct++;
          _streak++;
        } else {
          _streak = 0;
        }
      });
      // A visible "you got it!" — bigger burst for the youngest learners.
      if (res['correct'] == true && mounted) {
        final lv = widget.level;
        final young = lv == null || lv == 'L1' || lv == 'L2' || lv == 'L3';
        celebrate(context, intensity: young ? 1.3 : 0.9);
      }
      final wallet = res['wallet'];
      if (wallet is Map<String, dynamic>) widget.onWallet(wallet);
      _persist();
    } catch (_) {/* keep UI responsive even if grading call fails */}
  }

  String _wrongText() {
    final cv = _result?['correct_value'];
    final diag = (_result?['diagnostic'] ?? '').toString();
    final ans = cv != null ? 'The answer is $cv.' : 'See the correct answer.';
    return 'Not quite — $ans${diag.isNotEmpty ? '  $diag' : ''}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _q == null
              ? const Center(child: Padding(padding: EdgeInsets.all(24), child: Text('No more questions here — great work!')))
              : _buildQuestion(context),
    );
  }

  Widget _buildQuestion(BuildContext context) {
    final q = _q!;
    final choices = (q['choices'] as List<dynamic>? ?? []);
    final correctAnswer = _result == null ? null : _asInt(_result!['correct_answer']);
    final letters = ['A', 'B', 'C', 'D', 'E', 'F'];
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        _practiceProgressHeader(),
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white, borderRadius: BorderRadius.circular(20), border: Border.all(color: _line),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            MathText('${q['stem'] ?? ''}', fontSize: 18, bold: true),
            const SizedBox(height: 6),
            if (_imageWidget(q) != null)
              Padding(padding: const EdgeInsets.symmetric(vertical: 6), child: _imageWidget(q)!),
            if (choices.length >= 2)
              for (int i = 0; i < choices.length; i++)
                _optionTile(i, '${choices[i]}', letters[i], correctAnswer)
            else if ('${q['interaction_mode']}' != 'proof')
              _numberInput(),
          ]),
        ),
        if (_result != null) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(13),
            decoration: BoxDecoration(
              color: (_result!['correct'] == true) ? const Color(0xFFE5F7F0) : const Color(0xFFFDECEC),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Text(
              (_result!['correct'] == true)
                  ? 'Correct!  +${(_result!['reward']?['xp']) ?? 0} XP · +${(_result!['reward']?['coins']) ?? 0} coins'
                  : _wrongText(),
              style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: (_result!['correct'] == true) ? const Color(0xFF0B7C5B) : const Color(0xFFC0392B)),
            ),
          ),
        ],
        const SizedBox(height: 12),
        // Hint text — rendered as math (olympiad hints can contain LaTeX).
        if (_showHint)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: MathText(_hintText(q), fontSize: 14.5),
          ),
        // Reveal full solution — proof cards always; graded questions after answering.
        if (!_revealed &&
            _hasSolution(q) &&
            ('${q['interaction_mode']}' == 'proof' || _result != null))
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => setState(() => _revealed = true),
              icon: const Icon(Icons.menu_book_outlined, size: 19),
              label: const Text('Reveal full solution'),
            ),
          ),
        if (_revealed) _solutionView(q),
        const SizedBox(height: 10),
        // Navigation: back (left) · hint or next (center) · forward (right).
        Row(children: [
          _navCircle(Icons.arrow_back_rounded, _pos > 0 ? _back : null),
          const SizedBox(width: 10),
          if (_result == null && !('${q['interaction_mode']}' == 'proof' && _revealed))
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => setState(() => _showHint = true),
                icon: const Icon(Icons.lightbulb_outline, size: 19),
                label: const Text('Hint'),
              ),
            )
          else
            Expanded(
              child: FilledButton(
                style: FilledButton.styleFrom(backgroundColor: _orange),
                onPressed: _forward,
                child: const Text('Next question'),
              ),
            ),
          if ((_result == null && '${q['interaction_mode']}' != 'proof') ||
              ('${q['interaction_mode']}' == 'proof' && !_revealed)) ...[
            const SizedBox(width: 10),
            _navCircle(Icons.arrow_forward_rounded, _forward),
          ],
        ]),
      ],
    );
  }

  Widget _navCircle(IconData icon, VoidCallback? onTap) {
    final enabled = onTap != null;
    return Material(
      color: enabled ? Colors.white : const Color(0xFFF1F2F5),
      shape: const CircleBorder(side: BorderSide(color: _line)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(11),
          child: Icon(icon, size: 22, color: enabled ? const Color(0xFF20232A) : const Color(0xFFC2C7D0)),
        ),
      ),
    );
  }

  bool _hasSolution(Map<String, dynamic> q) {
    final s = (q['solution_steps'] as List<dynamic>?) ?? const [];
    return s.isNotEmpty || '${q['solution'] ?? ''}'.trim().isNotEmpty;
  }

  Widget? _imageWidget(Map<String, dynamic> q) {
    final svg = '${q['visual_svg'] ?? ''}'.trim();
    if (svg.isNotEmpty) return Center(child: SvgPicture.string(svg, height: 160));
    final png = '${q['visual_png'] ?? ''}'.trim();
    if (png.startsWith('data:image')) {
      try {
        return Center(child: Image.memory(base64Decode(png.split(',').last), height: 190, fit: BoxFit.contain));
      } catch (_) {}
    }
    return null;
  }

  Widget _solutionView(Map<String, dynamic> q) {
    final steps = (q['solution_steps'] as List<dynamic>?) ?? const [];
    final sol = '${q['solution'] ?? ''}'.trim();
    return Container(
      margin: const EdgeInsets.only(top: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F6FF),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFD6E2F7)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('SOLUTION',
            style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: 0.8)),
        const SizedBox(height: 8),
        if (steps.isNotEmpty)
          for (int i = 0; i < steps.length; i++)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: MathText('${i + 1}. ${steps[i]}', fontSize: 14),
            ),
        if (steps.isEmpty && sol.isNotEmpty) MathText(sol, fontSize: 14),
      ]),
    );
  }

  Widget _practiceProgressHeader() {
    const labelStyle = TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 11.5, letterSpacing: 0.8);
    // CHAPTER mode: a finite set → a real "X of Y" position bar is meaningful.
    if (widget.questions != null) {
      final total = widget.questions!.length;
      final pos = (_pos + 1).clamp(0, total);
      final frac = total == 0 ? 0.0 : pos / total;
      return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const Text('CHAPTER PRACTICE', style: labelStyle),
          Text('$pos of $total', style: labelStyle),
        ]),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: Stack(children: [
            Container(height: 9, color: const Color(0xFFEDEFF3)),
            FractionallySizedBox(
              widthFactor: (frac < 0.02 ? 0.02 : frac).toDouble(),
              child: Container(
                height: 9,
                decoration: const BoxDecoration(gradient: LinearGradient(colors: [Color(0xFFFF8A2B), _orange])),
              ),
            ),
          ]),
        ),
      ]);
    }
    // ADAPTIVE mode: open-ended, no fixed end → show real session stats, not a fake bar.
    final acc = _answered > 0 ? (_correct * 100 / _answered).round() : 0;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('OLYMPIAD PRACTICE', style: labelStyle),
      const SizedBox(height: 8),
      Row(children: [
        _statChip(Icons.local_fire_department, '$_streak', const Color(0xFFFFF1E3), _orangeD),
        const SizedBox(width: 8),
        _statChip(Icons.check_circle_outline, '$_correct / $_answered', const Color(0xFFE5F7F0), const Color(0xFF0B7C5B)),
        const Spacer(),
        if (_answered > 0)
          Text('$acc% this session', style: const TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 12)),
      ]),
    ]);
  }

  Widget _statChip(IconData icon, String text, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 14, color: fg),
        const SizedBox(width: 4),
        Text(text, style: TextStyle(color: fg, fontWeight: FontWeight.w800, fontSize: 12.5)),
      ]),
    );
  }

  String _hintText(Map<String, dynamic> q) {
    final h = q['hint'];
    if (h is Map) return '${h['level_0'] ?? h.values.first}';
    if (h is String) return h;
    return 'Break it into smaller steps using the numbers given.';
  }

  Widget _numberInput() {
    final correct = _result?['correct'] == true;
    Color border = _line;
    if (_result != null) border = correct ? _green : const Color(0xFFEF4444);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        TextField(
          controller: _input,
          enabled: _result == null,
          keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true),
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => _submit(value: _input.text),
          style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
          decoration: InputDecoration(
            hintText: 'Type your answer',
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: border, width: 1.5)),
            focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: _orange, width: 2)),
            disabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: border, width: 1.5)),
          ),
        ),
        if (_result == null) ...[
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              style: FilledButton.styleFrom(
                  backgroundColor: _orange, padding: const EdgeInsets.symmetric(vertical: 13)),
              onPressed: () => _submit(value: _input.text),
              child: const Text('Check', style: TextStyle(fontWeight: FontWeight.w800)),
            ),
          ),
        ],
      ]),
    );
  }

  Widget _optionTile(int i, String text, String letter, int? correctAnswer) {
    Color border = _line;
    Color bg = Colors.white;
    if (_result != null) {
      if (i == correctAnswer) {
        border = _green;
        bg = const Color(0xFFE5F7F0);
      } else if (i == _picked) {
        border = const Color(0xFFEF4444);
        bg = const Color(0xFFFDECEC);
      }
    }
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: InkWell(
        onTap: () => _submit(index: i),
        child: Container(
          padding: const EdgeInsets.all(13),
          decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(14), border: Border.all(color: border, width: 1.5)),
          child: Row(children: [
            Container(
              width: 27, height: 27,
              decoration: BoxDecoration(color: const Color(0xFFF2F3F6), borderRadius: BorderRadius.circular(8)),
              alignment: Alignment.center,
              child: Text(letter, style: const TextStyle(fontWeight: FontWeight.w800, color: _muted)),
            ),
            const SizedBox(width: 12),
            Expanded(child: Text(text, style: const TextStyle(fontWeight: FontWeight.w700))),
          ]),
        ),
      ),
    );
  }
}

// ===========================================================================
// Progress tab — Academic Height + strand mastery (from /v3/me/progress)
// ===========================================================================
class ProgressTab extends StatelessWidget {
  final String userId;
  final LevelService svc;
  final String? level;
  const ProgressTab({super.key, required this.userId, required this.svc, this.level});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: svc.getProgress(userId, level: level),
      builder: (context, snap) {
        if (!snap.hasData) return _loadingOrError(snap, 'progress');
        final p = snap.data!;
        final scale = _asInt(p['scale_score']);
        final verdict = '${p['verdict'] ?? 'On track'}';
        final strands = (p['strands'] as List<dynamic>? ?? []);
        final logic = p['logic_puzzles'] as Map<String, dynamic>?;
        final frac = ((scale - 200) / 600).clamp(0.0, 1.0).toDouble();
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text('Progress', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20), border: Border.all(color: _line)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('ACADEMIC HEIGHT', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: 1)),
                const SizedBox(height: 4),
                Text(verdict, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: _verdictColor(p['band']))),
                const SizedBox(height: 16),
                SizedBox(
                  height: 28,
                  child: Stack(alignment: Alignment.center, children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(999),
                      child: Row(children: const [
                        Expanded(flex: 36, child: SizedBox(height: 14, child: ColoredBox(color: Color(0xFFFBD9BE)))),
                        Expanded(flex: 28, child: SizedBox(height: 14, child: ColoredBox(color: Color(0xFFA9E6CE)))),
                        Expanded(flex: 36, child: SizedBox(height: 14, child: ColoredBox(color: Color(0xFFBBD2FB)))),
                      ]),
                    ),
                    Align(
                      alignment: Alignment(2 * frac - 1, 0),
                      child: Container(
                        width: 4,
                        height: 26,
                        decoration: BoxDecoration(color: const Color(0xFF20232A), borderRadius: BorderRadius.circular(3)),
                      ),
                    ),
                  ]),
                ),
                const SizedBox(height: 8),
                Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: const [
                  Text('Building', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 11)),
                  Text('On track', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 11)),
                  Text('Ahead', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 11)),
                ]),
                const SizedBox(height: 12),
                Text('Scale score $scale of ${_asInt(p['scale_max'] ?? 800)}  ·  500 = typical for the grade',
                    style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 13)),
              ]),
            ),
            const SizedBox(height: 18),
            const Text('MASTERY — THE 4 PILLARS', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, letterSpacing: 0.8, fontSize: 12)),
            const SizedBox(height: 10),
            for (final s in strands) _strandRow(s as Map<String, dynamic>),
            if (logic != null) ...[
              const SizedBox(height: 8),
              const Text('Plus · Logic & Puzzles', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, letterSpacing: 0.8)),
              const SizedBox(height: 10),
              _strandRow(logic),
            ],
          ],
        );
      },
    );
  }

  Color _verdictColor(dynamic band) {
    if (band == 'building') return _orangeD;
    if (band == 'ahead') return _blue;
    return _green;
  }

  Widget _strandRow(Map<String, dynamic> s) {
    final pct = _asInt(s['pct']);
    final color = _pillarColor(s['pillar'] as String?);
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(children: [
        SizedBox(
          width: 46,
          height: 46,
          child: Stack(alignment: Alignment.center, children: [
            SizedBox(
              width: 46,
              height: 46,
              child: CircularProgressIndicator(
                value: (pct / 100).clamp(0.0, 1.0).toDouble(),
                strokeWidth: 5,
                backgroundColor: const Color(0xFFEEF0F4),
                color: color,
              ),
            ),
            Text('$pct%', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 12, color: color)),
          ]),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${s['name']}', style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
            const SizedBox(height: 2),
            Text(
              pct >= 75
                  ? 'Strong'
                  : pct >= 55
                      ? 'Growing'
                      : 'Keep practising',
              style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 12.5),
            ),
          ]),
        ),
      ]),
    );
  }
}

// ===========================================================================
// Profile tab — wallet + settings + sign out
// ===========================================================================
class ProfileTab extends StatefulWidget {
  final String userId;
  final Map<String, dynamic> wallet;
  final LevelService svc;
  final String level;
  final String levelName;
  final String grades;       // the level's grade band (derived in the shell — one source of truth)
  final VoidCallback onChangeLevel;
  const ProfileTab({super.key, required this.userId, required this.wallet, required this.svc,
      required this.level, required this.levelName, required this.grades, required this.onChangeLevel});

  @override
  State<ProfileTab> createState() => _ProfileTabState();
}

class _ProfileTabState extends State<ProfileTab> {
  String _name = 'Learner';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final p = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() => _name = p.getString('v3_child_name') ?? 'Learner');
  }

  // Name only — the level (and therefore the grade band) is changed via the
  // "Change level" tile, so grade can never drift out of sync with the level.
  Future<void> _edit() async {
    final nameCtrl = TextEditingController(text: _name);
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Edit name'),
        content: TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: 'Child name')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Save')),
        ],
      ),
    );
    if (ok == true) {
      final name = nameCtrl.text.trim().isEmpty ? 'Learner' : nameCtrl.text.trim();
      final p = await SharedPreferences.getInstance();
      await p.setString('v3_child_name', name);
      if (mounted) setState(() => _name = name);
    }
  }

  void _switch() {
    showDialog(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Switch learner'),
        content: const Text(
            'Each device is set up for one learner right now. To add another child, sign out and sign in with their own account — multi-child profiles under one account are coming soon.'),
        actions: [TextButton(onPressed: () => Navigator.pop(c), child: const Text('Got it'))],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final w = widget.wallet;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(children: [
          CircleAvatar(
            radius: 30,
            backgroundColor: _orange,
            child: Text(_name.isNotEmpty ? _name[0].toUpperCase() : 'K',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 24)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(_name, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 19)),
              Text('${widget.levelName} · ${(w['topics_mastered'] ?? 0)} topics mastered',
                  style: const TextStyle(color: _muted, fontWeight: FontWeight.w700)),
            ]),
          ),
        ]),
        const SizedBox(height: 16),
        Row(children: [
          _stat(Icons.monetization_on, '${w['kiwi_coins'] ?? 0}', 'Kiwi Coins', _orange),
          const SizedBox(width: 9),
          _stat(Icons.diamond, '${w['gems'] ?? 0}', 'Gems', const Color(0xFF8B5CF6)),
          const SizedBox(width: 9),
          _stat(Icons.star, '${w['xp_total'] ?? 0}', 'XP', _green),
        ]),
        const SizedBox(height: 18),
        _tile(Icons.workspace_premium_outlined,
            'Level · ${widget.level} · ${widget.levelName}', widget.onChangeLevel),
        _tile(Icons.edit_outlined, 'Edit name', _edit),
        _tile(Icons.group_outlined, 'Switch learner', _switch),
        _tile(Icons.shield_outlined, 'Parent dashboard', () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => _ParentPage(userId: widget.userId, svc: widget.svc, childName: _name,
                  level: widget.level, levelName: widget.levelName, grades: widget.grades),
            ),
          );
        }),
        _tile(Icons.notifications_none, 'Notifications', () {}),
        _tile(Icons.info_outline, 'About Kiwimath',
            () => showAboutDialog(context: context, applicationName: 'Kiwimath', applicationVersion: 'v1 · Level/Grade')),
        _switchTile(Icons.celebration_outlined, 'Celebrations', CelebrationPrefs.confetti,
            (v) { CelebrationPrefs.setConfetti(v); setState(() {}); }),
        _switchTile(Icons.volume_up_outlined, 'Sound effects', CelebrationPrefs.sound,
            (v) { CelebrationPrefs.setSound(v); setState(() {}); }),
        const SizedBox(height: 8),
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: _line)),
          child: ListTile(
            leading: const Icon(Icons.logout, color: Color(0xFFD8412F)),
            title: const Text('Sign out', style: TextStyle(color: Color(0xFFD8412F), fontWeight: FontWeight.w800)),
            onTap: () => FirebaseAuth.instance.signOut(),
          ),
        ),
      ],
    );
  }

  Widget _stat(IconData icon, String value, String label, Color c) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(color: const Color(0xFFF8F8F5), borderRadius: BorderRadius.circular(14)),
        child: Column(children: [
          Icon(icon, color: c, size: 20),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          Text(label, style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 11)),
        ]),
      ),
    );
  }

  Widget _tile(IconData icon, String title, VoidCallback onTap) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 9),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: _line)),
      child: ListTile(
        leading: Icon(icon, color: _orangeD),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
        trailing: const Icon(Icons.chevron_right, color: Color(0xFFC9CFDA)),
        onTap: onTap,
      ),
    );
  }

  Widget _switchTile(IconData icon, String title, bool value, ValueChanged<bool> onChanged) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 9),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: _line)),
      child: SwitchListTile(
        secondary: Icon(icon, color: _orangeD),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5)),
        value: value,
        activeColor: _orange,
        onChanged: onChanged,
      ),
    );
  }
}

// Parent dashboard — PIN gate then a parent-framed progress summary.
class _ParentPage extends StatefulWidget {
  final String userId;
  final LevelService svc;
  final String childName;
  final String level;      // the child's actual chosen level — the app's single source of truth
  final String levelName;
  final String grades;
  const _ParentPage({required this.userId, required this.svc, required this.childName,
      required this.level, required this.levelName, required this.grades});

  @override
  State<_ParentPage> createState() => _ParentPageState();
}

class _ParentPageState extends State<_ParentPage> {
  String _pin = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Parent dashboard')),
      body: _pin.length >= 4 ? _dashboard() : _gate(),
    );
  }

  Widget _gate() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Text('Enter your 4-digit PIN', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        const SizedBox(height: 16),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          for (int i = 0; i < 4; i++)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 7),
              width: 14,
              height: 14,
              decoration: BoxDecoration(shape: BoxShape.circle, color: i < _pin.length ? _orange : const Color(0xFFE2E6EE)),
            ),
        ]),
        const SizedBox(height: 24),
        Wrap(spacing: 14, runSpacing: 14, alignment: WrapAlignment.center, children: [
          for (final n in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'])
            SizedBox(
              width: 64,
              height: 54,
              child: OutlinedButton(
                onPressed: () => setState(() {
                  if (_pin.length < 4) _pin += n;
                }),
                child: Text(n, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
              ),
            ),
          SizedBox(
            width: 64,
            height: 54,
            child: OutlinedButton(
              onPressed: () => setState(() {
                if (_pin.isNotEmpty) _pin = _pin.substring(0, _pin.length - 1);
              }),
              child: const Icon(Icons.backspace_outlined),
            ),
          ),
        ]),
        const SizedBox(height: 12),
        const Text('A PIN, not a maths problem — so the kids cannot crack it.',
            style: TextStyle(color: _muted, fontSize: 12), textAlign: TextAlign.center),
      ]),
    );
  }

  Widget _dashboard() {
    // Academic Height is scoped to the child's ACTUAL chosen level (the app's
    // single source of truth), so the parent sees the same level the child is
    // practising — never a re-derived one that could disagree with the app.
    return FutureBuilder<Map<String, dynamic>>(
      future: widget.svc.getProgress(widget.userId, level: widget.level),
      builder: (context, snap) {
        if (!snap.hasData) return _loadingOrError(snap, 'progress');
        final p = snap.data!;
        final hasData = _asInt(p['scope_attempts']) > 0;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text('${widget.childName} · ${widget.levelName}',
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18), border: Border.all(color: _line)),
            child: hasData
              ? Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('ACADEMIC HEIGHT', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: 1)),
                  const SizedBox(height: 4),
                  Text('${p['verdict'] ?? 'On track'} for ${widget.levelName}',
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20)),
                  const SizedBox(height: 8),
                  Text('Scale score ${_asInt(p['scale_score'])} of 800 · Grade average ≈ 500',
                      style: const TextStyle(color: _muted, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  Text('Accuracy ${p['accuracy'] ?? 0}% · ${_asInt(p['topics_mastered'])} topics mastered · ${_asInt(p['streak'])}-day streak',
                      style: const TextStyle(color: _muted, fontWeight: FontWeight.w700)),
                ])
              : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('ACADEMIC HEIGHT', style: TextStyle(color: _muted, fontWeight: FontWeight.w800, fontSize: 12, letterSpacing: 1)),
                  const SizedBox(height: 6),
                  Text('No ${widget.levelName} practice yet',
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
                  const SizedBox(height: 6),
                  const Text('Once your child practises this level’s topics, their academic height shows here.',
                      style: TextStyle(color: _muted, fontWeight: FontWeight.w600, fontSize: 13)),
                ]),
          ),
          const SizedBox(height: 12),
          const Text('No coins or gems here — only real learning.',
              textAlign: TextAlign.center, style: TextStyle(color: _muted, fontSize: 12)),
        ]);
      },
    );
  }
}

// ===========================================================================
// Shared loading/error helper
// ===========================================================================
Widget _loadingOrError(AsyncSnapshot snap, String what) {
  if (snap.hasError) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text("Couldn't load $what.\nCheck your connection and try again.",
            textAlign: TextAlign.center, style: const TextStyle(color: _muted, fontWeight: FontWeight.w700)),
      ),
    );
  }
  return const Center(child: CircularProgressIndicator());
}
