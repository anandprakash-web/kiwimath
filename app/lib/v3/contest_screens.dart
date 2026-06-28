import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_math_fork/flutter_math.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../services/contest_service.dart';
import '../services/level_service.dart';

const _orange = Color(0xFFFF6D00);
const _orangeD = Color(0xFFE65100);
const _ink = Color(0xFF20232A);
const _muted = Color(0xFF8A93A2);
const _green = Color(0xFF1FA971);
const _greenL = Color(0xFFE7F7EF);
const _red = Color(0xFFE5484D);
const _bg = Color(0xFFFAFAF7);
const _line = Color(0xFFECEEF2);

// ----------------------------------------------------------- shared renderers
Widget _stem(String s, {double size = 18}) {
  if (!s.contains(r'$')) {
    return Text(s,
        style: TextStyle(fontSize: size, height: 1.35, color: _ink, fontWeight: FontWeight.w700));
  }
  final parts = s.split(r'$');
  final spans = <InlineSpan>[];
  for (var i = 0; i < parts.length; i++) {
    if (parts[i].isEmpty) continue;
    if (i.isEven) {
      spans.add(TextSpan(
          text: parts[i],
          style: TextStyle(fontSize: size, color: _ink, fontWeight: FontWeight.w700)));
    } else {
      spans.add(WidgetSpan(
        alignment: PlaceholderAlignment.middle,
        child: Math.tex(parts[i],
            textStyle: TextStyle(fontSize: size, color: _ink),
            onErrorFallback: (e) => Text('\$${parts[i]}\$', style: TextStyle(fontSize: size))),
      ));
    }
  }
  return Text.rich(TextSpan(children: spans), style: const TextStyle(height: 1.4));
}

Widget _figure(Map<String, dynamic> q) {
  final svg = q['visual_svg'];
  if (svg is String && svg.trim().isNotEmpty) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: SvgPicture.string(svg, height: 160, fit: BoxFit.contain),
    );
  }
  final png = q['visual_png'];
  if (png is String && png.contains(',')) {
    try {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Image.memory(base64Decode(png.split(',').last), height: 180, fit: BoxFit.contain),
      );
    } catch (_) {}
  }
  return const SizedBox.shrink();
}

BoxDecoration _card() => BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: _line),
    );

// =================================================================== HUB
class CompeteHubScreen extends StatefulWidget {
  final String userId;
  const CompeteHubScreen({super.key, required this.userId});
  @override
  State<CompeteHubScreen> createState() => _CompeteHubState();
}

class _CompeteHubState extends State<CompeteHubScreen> {
  final _lvl = LevelService();
  final _svc = ContestService();
  List<Map<String, dynamic>> _levels = [];
  String? _level;
  Map<String, dynamic>? _status;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final raw = await _lvl.getLevels();
      final avail = raw
          .whereType<Map>()
          .map((e) => e.cast<String, dynamic>())
          .where((e) => e['available'] == true)
          .toList();
      _levels = avail;
      _level = avail.isNotEmpty ? '${avail.first['level']}' : null;
      await _loadStatus();
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _loadStatus() async {
    if (_level == null) return;
    try {
      _status = await _svc.getContestToday(widget.userId, _level!);
    } catch (_) {
      _status = null;
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        elevation: 0,
        foregroundColor: _ink,
        title: const Text('Compete', style: TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: _orange))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (_levels.length > 1) _levelChips(),
                const SizedBox(height: 8),
                _contestCard(),
                const SizedBox(height: 14),
                _leagueCard(),
              ],
            ),
    );
  }

  Widget _levelChips() {
    return SizedBox(
      height: 40,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: _levels.map((l) {
          final code = '${l['level']}';
          final sel = code == _level;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text('${l['level_name'] ?? code}'),
              selected: sel,
              selectedColor: const Color(0xFFFFF1E3),
              labelStyle: TextStyle(
                  color: sel ? _orangeD : _muted, fontWeight: FontWeight.w700, fontSize: 12.5),
              onSelected: (_) {
                setState(() => _level = code);
                _loadStatus();
              },
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _contestCard() {
    final st = _status?['status'] ?? '...';
    final attempted = _status?['attempted'] == true;
    String tag;
    if (attempted) {
      tag = 'Done today';
    } else if (st == 'live') {
      tag = 'Live now';
    } else if (st == 'upcoming') {
      tag = 'Opens 6 PM';
    } else {
      tag = 'Back tomorrow';
    }
    return InkWell(
      onTap: _level == null
          ? null
          : () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) =>
                      DailyContestScreen(userId: widget.userId, level: _level!),
                ),
              ).then((_) => _loadStatus()),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: const LinearGradient(
              colors: [Color(0xFFFF8A2B), _orange, _orangeD]),
        ),
        padding: const EdgeInsets.all(18),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.bolt, color: Colors.white),
            const SizedBox(width: 6),
            const Text('Daily Olympiad',
                style: TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18)),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                  color: Colors.white24, borderRadius: BorderRadius.circular(20)),
              child: Text(tag,
                  style: const TextStyle(
                      color: Colors.white, fontWeight: FontWeight.w800, fontSize: 11.5)),
            ),
          ]),
          const SizedBox(height: 8),
          const Text('The day\'s biggest points. One attempt.',
              style: TextStyle(color: Colors.white70, fontSize: 13)),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                  color: Colors.white, borderRadius: BorderRadius.circular(14)),
              child: Text(attempted ? 'View result' : 'Enter contest',
                  style: const TextStyle(color: _orangeD, fontWeight: FontWeight.w800)),
            ),
          ),
        ]),
      ),
    );
  }

  Widget _leagueCard() {
    return InkWell(
      onTap: _level == null
          ? null
          : () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => LeagueScreen(userId: widget.userId, level: _level!),
                ),
              ),
      child: Container(
        decoration: _card(),
        padding: const EdgeInsets.all(16),
        child: Row(children: [
          const Icon(Icons.emoji_events, color: _orange),
          const SizedBox(width: 10),
          const Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Weekly League',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: _ink)),
              Text('Climb your cohort — top 7 promote',
                  style: TextStyle(color: _muted, fontSize: 12.5)),
            ]),
          ),
          const Icon(Icons.chevron_right, color: _muted),
        ]),
      ),
    );
  }
}

// =========================================================== DAILY CONTEST
enum _Phase { loading, lobby, quiz, submitting, results }

class DailyContestScreen extends StatefulWidget {
  final String userId;
  final String level;
  const DailyContestScreen({super.key, required this.userId, required this.level});
  @override
  State<DailyContestScreen> createState() => _DailyContestState();
}

class _DailyContestState extends State<DailyContestScreen> {
  final _svc = ContestService();
  _Phase _phase = _Phase.loading;
  Map<String, dynamic> _contest = {};
  List<dynamic> _questions = [];
  int _idx = 0;
  final Map<String, Map<String, dynamic>> _answers = {};
  int _qStart = 0;
  int? _picked;
  final _input = TextEditingController();
  Map<String, dynamic>? _result;
  Map<String, dynamic>? _board;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final c = await _svc.getContestToday(widget.userId, widget.level);
      _contest = c;
      if (c['attempted'] == true) {
        _result = (c['result'] as Map?)?.cast<String, dynamic>();
        await _loadBoard();
        if (mounted) setState(() => _phase = _Phase.results);
      } else {
        if (mounted) setState(() => _phase = _Phase.lobby);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = '$e';
          _phase = _Phase.lobby;
        });
      }
    }
  }

  Future<void> _loadBoard() async {
    try {
      _board = await _svc.contestLeaderboard(widget.level);
    } catch (_) {}
  }

  void _start() {
    _questions = (_contest['questions'] as List?) ?? [];
    _idx = 0;
    _picked = null;
    _input.clear();
    _qStart = DateTime.now().millisecondsSinceEpoch;
    setState(() => _phase = _Phase.quiz);
  }

  void _record() {
    final q = (_questions[_idx] as Map).cast<String, dynamic>();
    final qid = '${q['id']}';
    final a = <String, dynamic>{
      'qid': qid,
      'time_ms': DateTime.now().millisecondsSinceEpoch - _qStart,
    };
    final choices = q['choices'] as List?;
    if (choices != null && choices.isNotEmpty) {
      a['selected_index'] = _picked;
    } else {
      a['selected_value'] = _input.text.trim();
    }
    _answers[qid] = a;
  }

  bool get _answered {
    final q = (_questions[_idx] as Map).cast<String, dynamic>();
    final choices = q['choices'] as List?;
    if (choices != null && choices.isNotEmpty) return _picked != null;
    return _input.text.trim().isNotEmpty;
  }

  Future<void> _next() async {
    _record();
    if (_idx + 1 < _questions.length) {
      setState(() {
        _idx++;
        _picked = null;
        _input.clear();
        _qStart = DateTime.now().millisecondsSinceEpoch;
      });
    } else {
      await _submit();
    }
  }

  Future<void> _submit() async {
    setState(() => _phase = _Phase.submitting);
    try {
      _result = await _svc.submitContest(
        userId: widget.userId,
        level: widget.level,
        answers: _answers.values.toList(),
      );
      await _loadBoard();
    } catch (e) {
      _error = '$e';
    }
    if (mounted) setState(() => _phase = _Phase.results);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        elevation: 0,
        foregroundColor: _ink,
        title: const Text('Daily Olympiad', style: TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: switch (_phase) {
        _Phase.loading => const Center(child: CircularProgressIndicator(color: _orange)),
        _Phase.submitting =>
          const Center(child: CircularProgressIndicator(color: _orange)),
        _Phase.lobby => _lobby(),
        _Phase.quiz => _quiz(),
        _Phase.results => _results(),
      },
    );
  }

  Widget _lobby() {
    final st = _contest['status'] ?? 'upcoming';
    final live = st == 'live' && ((_contest['questions'] as List?)?.isNotEmpty ?? false);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.bolt, size: 54, color: _orange),
          const SizedBox(height: 10),
          Text(
            live
                ? 'Ready when you are'
                : (st == 'upcoming' ? 'Opens at 6 PM' : 'Come back tomorrow'),
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: _ink),
          ),
          const SizedBox(height: 6),
          Text('${_contest['n_questions'] ?? 8} questions · one attempt',
              style: const TextStyle(color: _muted)),
          if (_error != null) ...[
            const SizedBox(height: 10),
            Text(_error!, style: const TextStyle(color: _red, fontSize: 12)),
          ],
          const SizedBox(height: 22),
          if (live)
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                style: FilledButton.styleFrom(
                    backgroundColor: _orange,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                onPressed: _start,
                child: const Text('Start contest',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              ),
            ),
        ]),
      ),
    );
  }

  Widget _quiz() {
    final q = (_questions[_idx] as Map).cast<String, dynamic>();
    final choices = (q['choices'] as List?) ?? [];
    final total = _questions.length;
    return SafeArea(
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Row(children: [
            Text('Question ${_idx + 1} of $total',
                style: const TextStyle(fontWeight: FontWeight.w800, color: _muted, fontSize: 12.5)),
            const Spacer(),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (_idx + 1) / total,
              minHeight: 6,
              backgroundColor: _line,
              valueColor: const AlwaysStoppedAnimation(_orange),
            ),
          ),
        ),
        Expanded(
          child: ListView(padding: const EdgeInsets.all(16), children: [
            Container(
              decoration: _card(),
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _stem('${q['stem']}'),
                _figure(q),
                const SizedBox(height: 10),
                if (choices.isNotEmpty)
                  ...List.generate(choices.length, (i) => _choice(i, '${choices[i]}'))
                else
                  TextField(
                    controller: _input,
                    keyboardType:
                        TextInputType.numberWithOptions(signed: true, decimal: true),
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(
                      hintText: 'Type your answer',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(13)),
                    ),
                  ),
              ]),
            ),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: FilledButton(
              style: FilledButton.styleFrom(
                  backgroundColor: _orange,
                  disabledBackgroundColor: const Color(0xFFE4E6EC),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
              onPressed: _answered ? _next : null,
              child: Text(_idx + 1 < _questions.length ? 'Next' : 'Submit',
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
            ),
          ),
        ),
      ]),
    );
  }

  Widget _choice(int i, String text) {
    final sel = _picked == i;
    return Padding(
      padding: const EdgeInsets.only(top: 9),
      child: InkWell(
        onTap: () => setState(() => _picked = i),
        borderRadius: BorderRadius.circular(13),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(13),
            border: Border.all(color: sel ? _orange : _line, width: 1.5),
            color: sel ? const Color(0xFFFFF1E3) : Colors.white,
          ),
          child: Text(text,
              style: TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 14.5,
                  color: sel ? _orangeD : _ink)),
        ),
      ),
    );
  }

  Widget _results() {
    final r = _result ?? {};
    final score = r['score'] ?? 0;
    final lp = r['lp'] ?? score;
    final correct = r['correct'] ?? 0;
    final of = r['of'] ?? (_contest['n_questions'] ?? 8);
    final rank = r['rank'];
    final rows = (_board?['rows'] as List?) ?? [];
    return ListView(padding: const EdgeInsets.all(16), children: [
      Container(
        decoration: BoxDecoration(
            color: _greenL, borderRadius: BorderRadius.circular(20)),
        padding: const EdgeInsets.all(20),
        child: Column(children: [
          Text(rank == 1 ? '🥇' : (rank == 2 ? '🥈' : (rank == 3 ? '🥉' : '✓')),
              style: const TextStyle(fontSize: 34)),
          const SizedBox(height: 4),
          Text(rank != null ? 'You placed #$rank' : 'Submitted',
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: _ink)),
          Text('$correct of $of correct', style: const TextStyle(color: _muted)),
          const SizedBox(height: 12),
          Wrap(spacing: 10, children: [
            _pill('+$lp LP', _green, _greenL),
            _pill('Score $score', _orangeD, const Color(0xFFFFF1E3)),
          ]),
        ]),
      ),
      const SizedBox(height: 18),
      const Text('Today\'s leaderboard',
          style: TextStyle(fontWeight: FontWeight.w800, color: _muted, fontSize: 12.5)),
      const SizedBox(height: 6),
      Container(
        decoration: _card(),
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Column(
          children: rows.take(10).map((e) {
            final row = (e as Map).cast<String, dynamic>();
            return _boardRow('${row['rank']}', '${row['name']}', '${row['score']}',
                me: '${row['name']}' == '${_contest['name'] ?? ''}');
          }).toList(),
        ),
      ),
    ]);
  }

  Widget _pill(String text, Color fg, Color bg) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(20)),
        child: Text(text, style: TextStyle(color: fg, fontWeight: FontWeight.w800, fontSize: 12.5)),
      );

  Widget _boardRow(String rank, String name, String pts, {bool me = false}) => Container(
        margin: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
        decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: me ? const Color(0xFFFFF1E3) : Colors.transparent),
        child: Row(children: [
          SizedBox(
              width: 26,
              child: Text(rank,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontWeight: FontWeight.w800, color: _muted))),
          const SizedBox(width: 8),
          Expanded(
              child: Text(name,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13.5, color: _ink))),
          Text(pts, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13.5, color: _ink)),
        ]),
      );
}

// ================================================================= LEAGUE
class LeagueScreen extends StatefulWidget {
  final String userId;
  final String level;
  const LeagueScreen({super.key, required this.userId, required this.level});
  @override
  State<LeagueScreen> createState() => _LeagueState();
}

class _LeagueState extends State<LeagueScreen> {
  final _svc = ContestService();
  Map<String, dynamic>? _st;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      _st = await _svc.leagueMe(widget.userId, widget.level);
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final st = _st ?? {};
    final rows = (st['rows'] as List?) ?? [];
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        elevation: 0,
        foregroundColor: _ink,
        title: Text('${st['tier'] ?? 'League'} League',
            style: const TextStyle(fontWeight: FontWeight.w800)),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: _orange))
          : ListView(padding: const EdgeInsets.all(16), children: [
              Container(
                decoration: BoxDecoration(
                    color: const Color(0xFFFFF3E0), borderRadius: BorderRadius.circular(16)),
                padding: const EdgeInsets.all(14),
                child: Row(children: [
                  const Icon(Icons.emoji_events, color: _orange, size: 30),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Top ${st['promote_zone'] ?? 7} promote to ${st['promote_to'] ?? ''}',
                          style: const TextStyle(fontWeight: FontWeight.w800, color: _ink, fontSize: 13.5)),
                      Text('${st['cohort_size'] ?? rows.length} players · ends ${st['ends'] ?? ''}',
                          style: const TextStyle(color: _muted, fontSize: 12)),
                    ]),
                  ),
                ]),
              ),
              const SizedBox(height: 12),
              Container(
                decoration: _card(),
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Column(children: rows.map((e) => _row((e as Map).cast<String, dynamic>())).toList()),
              ),
            ]),
    );
  }

  Widget _row(Map<String, dynamic> r) {
    final zone = r['zone'];
    final me = r['me'] == true;
    Color stripe = Colors.transparent;
    if (zone == 'promote') stripe = _green;
    if (zone == 'relegate') stripe = _red;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 9),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        color: me ? const Color(0xFFFFF1E3) : Colors.transparent,
        border: me ? Border.all(color: _orange) : null,
      ),
      child: Row(children: [
        Container(width: 4, height: 26, decoration: BoxDecoration(color: stripe, borderRadius: BorderRadius.circular(3))),
        const SizedBox(width: 8),
        SizedBox(
            width: 24,
            child: Text('${r['rank']}',
                textAlign: TextAlign.center,
                style: const TextStyle(fontWeight: FontWeight.w800, color: _muted))),
        const SizedBox(width: 6),
        Expanded(
            child: Text('${r['name']}',
                style: TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 13.5,
                    color: me ? _orangeD : _ink))),
        Text('${r['lp']}',
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13.5, color: _ink)),
      ]),
    );
  }
}
