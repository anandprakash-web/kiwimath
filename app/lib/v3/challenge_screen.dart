// The Climb — adaptive Challenge (a sequential mini-CAT).
//
// A short, ability-adaptive test: each question is chosen at the edge of the
// learner's ability, and the result is a "Climb rating" (the same 200–800 scale
// the Progress tab shows) plus how high they reached. Separate from Practice
// (the skill-ladder moat) — this one measures and stretches.

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_math_fork/flutter_math.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../services/challenge_service.dart';

const _orange = Color(0xFFFF6D00);
const _orangeD = Color(0xFFE65100);
const _ink = Color(0xFF1E2330);
const _muted = Color(0xFF7C8597);
const _line = Color(0xFFECEAE3);
const _green = Color(0xFF0FB17E);
const _bg = Color(0xFFFAFAF7);

// ---------------------------------------------------------- shared renderers
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

// ============================================================= the screen
class ChallengeScreen extends StatefulWidget {
  final String userId;
  final String level;
  final String levelName;
  const ChallengeScreen({
    super.key,
    required this.userId,
    required this.level,
    required this.levelName,
  });
  @override
  State<ChallengeScreen> createState() => _ChallengeScreenState();
}

enum _Phase { loading, lobby, climb, result, error }

class _ChallengeScreenState extends State<ChallengeScreen> {
  final _svc = ChallengeService();
  final _input = TextEditingController();

  _Phase _phase = _Phase.loading;
  Map<String, dynamic> _me = {};
  Map<String, dynamic>? _q;          // current question
  String _sid = '';
  int _idx = 0, _total = 10;
  int? _picked;
  Map<String, dynamic>? _result;
  bool _busy = false;
  String _err = '';

  @override
  void initState() {
    super.initState();
    _loadLobby();
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _loadLobby() async {
    try {
      final me = await _svc.me(widget.userId, widget.level);
      if (!mounted) return;
      setState(() {
        _me = me;
        _phase = _Phase.lobby;
      });
    } catch (_) {
      if (mounted) setState(() => _phase = _Phase.lobby); // lobby still usable offline
    }
  }

  void _apply(Map<String, dynamic> res) {
    _q = (res['question'] as Map?)?.cast<String, dynamic>();
    _sid = '${res['session_id'] ?? _sid}';
    _idx = (res['index'] as num?)?.toInt() ?? _idx;
    _total = (res['total'] as num?)?.toInt() ?? _total;
    _picked = null;
    _input.clear();
  }

  Future<void> _begin() async {
    setState(() => _busy = true);
    try {
      final res = await _svc.start(widget.userId, widget.level);
      if (!mounted) return;
      if (res['error'] != null || res['question'] == null) {
        setState(() {
          _err = '${res['message'] ?? 'The Climb isn\'t ready for this level yet.'}';
          _phase = _Phase.error;
        });
        return;
      }
      setState(() {
        _apply(res);
        _phase = _Phase.climb;
      });
    } catch (e) {
      if (mounted) setState(() { _err = 'Could not start the climb.'; _phase = _Phase.error; });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  bool get _answered {
    final choices = (_q?['choices'] as List?) ?? [];
    return choices.isNotEmpty ? _picked != null : _input.text.trim().isNotEmpty;
  }

  Future<void> _submit() async {
    if (!_answered || _busy || _q == null) return;
    HapticFeedback.selectionClick();
    setState(() => _busy = true);
    final choices = (_q!['choices'] as List?) ?? [];
    try {
      final res = await _svc.answer(
        userId: widget.userId,
        sessionId: _sid,
        qid: '${_q!['id']}',
        selectedIndex: choices.isNotEmpty ? _picked : null,
        selectedValue: choices.isEmpty ? _input.text.trim() : null,
        timeMs: 0,
      );
      if (!mounted) return;
      if (res['done'] == true) {
        setState(() {
          _result = (res['result'] as Map?)?.cast<String, dynamic>();
          _result?['best_rating'] = res['best_rating'];
          _result?['is_personal_best'] = res['is_personal_best'];
          _phase = _Phase.result;
        });
      } else {
        setState(() => _apply(res));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Network hiccup — try that answer again.')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      appBar: AppBar(
        backgroundColor: _bg,
        elevation: 0,
        title: const Text('The Climb', style: TextStyle(color: _ink, fontWeight: FontWeight.w800)),
        iconTheme: const IconThemeData(color: _ink),
      ),
      body: switch (_phase) {
        _Phase.loading => const Center(child: CircularProgressIndicator()),
        _Phase.lobby => _lobby(),
        _Phase.climb => _climb(),
        _Phase.result => _resultView(),
        _Phase.error => _errorView(),
      },
    );
  }

  // ----------------------------------------------------------------- lobby
  Widget _lobby() {
    final best = (_me['best_rating'] as num?)?.toInt() ?? 0;
    final plays = (_me['plays'] as num?)?.toInt() ?? 0;
    final active = _me['active'] == true;
    return SafeArea(
      child: ListView(padding: const EdgeInsets.all(18), children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
                colors: [Color(0xFFFFA64D), _orange, _orangeD],
                begin: Alignment.topLeft, end: Alignment.bottomRight),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Icon(Icons.terrain, color: Colors.white, size: 30),
            const SizedBox(height: 10),
            Text('How high can you climb?',
                style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
            const SizedBox(height: 6),
            Text('10 questions that adapt to you — each one chosen right at your edge. '
                'Reach your peak for ${widget.levelName}.',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, height: 1.4)),
          ]),
        ),
        const SizedBox(height: 14),
        if (best > 0)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: _card(),
            child: Row(children: [
              const Icon(Icons.workspace_premium, color: _orange),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Your best climb', style: TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 12.5)),
                  Text('$best  ·  $plays ${plays == 1 ? 'climb' : 'climbs'}',
                      style: const TextStyle(color: _ink, fontWeight: FontWeight.w800, fontSize: 16)),
                ]),
              ),
            ]),
          ),
        const SizedBox(height: 18),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            style: FilledButton.styleFrom(
                backgroundColor: _orange,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
            onPressed: _busy ? null : _begin,
            child: Text(active ? 'Resume your climb' : (best > 0 ? 'Climb again' : 'Start the Climb'),
                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          ),
        ),
        const SizedBox(height: 10),
        const Text('Your rating sharpens the more you play.',
            textAlign: TextAlign.center,
            style: TextStyle(color: _muted, fontWeight: FontWeight.w600, fontSize: 12)),
      ]),
    );
  }

  // ----------------------------------------------------------------- climb
  Widget _climb() {
    final q = _q!;
    final choices = (q['choices'] as List?) ?? [];
    final shown = _idx + 1;
    return SafeArea(
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
          child: Row(children: [
            Text('Climbing · $shown of $_total',
                style: const TextStyle(fontWeight: FontWeight.w800, color: _muted, fontSize: 12.5)),
            const Spacer(),
            const Icon(Icons.terrain, size: 16, color: _orange),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: shown / _total,
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
                    keyboardType: const TextInputType.numberWithOptions(signed: true, decimal: true),
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
              onPressed: (_answered && !_busy) ? _submit : null,
              child: Text(shown < _total ? 'Next' : 'Finish climb',
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
        onTap: _busy ? null : () => setState(() => _picked = i),
        borderRadius: BorderRadius.circular(13),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(13),
            border: Border.all(color: sel ? _orange : _line, width: 1.5),
            color: sel ? const Color(0xFFFFF1E3) : Colors.white,
          ),
          child: Text(text,
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5, color: sel ? _orangeD : _ink)),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------- result
  Widget _resultView() {
    final r = _result ?? {};
    final rating = (r['rating'] as num?)?.toInt() ?? 0;
    final band = '${r['band'] ?? ''}';
    final emoji = '${r['band_emoji'] ?? ''}';
    final correct = (r['correct'] as num?)?.toInt() ?? 0;
    final of = (r['of'] as num?)?.toInt() ?? _total;
    final peak = (r['peak_rating'] as num?)?.toInt() ?? rating;
    final isPB = r['is_personal_best'] == true;
    final frac = ((rating - 200) / 600).clamp(0.0, 1.0);

    return SafeArea(
      child: ListView(padding: const EdgeInsets.all(18), children: [
        if (isPB)
          Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(color: const Color(0xFFE9F8F1), borderRadius: BorderRadius.circular(13)),
            child: Row(children: const [
              Icon(Icons.celebration, color: _green, size: 18),
              SizedBox(width: 8),
              Text('New personal best!', style: TextStyle(color: _green, fontWeight: FontWeight.w800)),
            ]),
          ),
        Container(
          height: 220,
          decoration: BoxDecoration(borderRadius: BorderRadius.circular(22), color: const Color(0xFFFFF6EC)),
          clipBehavior: Clip.antiAlias,
          child: Stack(children: [
            Positioned.fill(child: CustomPaint(painter: _ClimbPainter(frac))),
            Padding(
              padding: const EdgeInsets.all(18),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('YOUR CLIMB RATING',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 11.5, letterSpacing: 1.2)),
                const SizedBox(height: 2),
                Text('$rating',
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 52, height: 1.0)),
                Text('$emoji $band'.trim(),
                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 15)),
              ]),
            ),
          ]),
        ),
        const SizedBox(height: 14),
        Row(children: [
          Expanded(child: _stat('Solved', '$correct / $of')),
          const SizedBox(width: 12),
          Expanded(child: _stat('Highest cleared', '$peak')),
        ]),
        const SizedBox(height: 18),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            style: FilledButton.styleFrom(
                backgroundColor: _orange,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
            onPressed: _busy ? null : _begin,
            child: const Text('Climb again', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: TextButton(
            onPressed: () => Navigator.of(context).maybePop(),
            child: const Text('Done', style: TextStyle(color: _muted, fontWeight: FontWeight.w800)),
          ),
        ),
        const SizedBox(height: 6),
        const Text('Ratings are an early signal and sharpen as you play.',
            textAlign: TextAlign.center,
            style: TextStyle(color: _muted, fontWeight: FontWeight.w600, fontSize: 11.5)),
      ]),
    );
  }

  Widget _stat(String label, String value) {
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: _card(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(color: _muted, fontWeight: FontWeight.w700, fontSize: 12)),
        const SizedBox(height: 3),
        Text(value, style: const TextStyle(color: _ink, fontWeight: FontWeight.w800, fontSize: 18)),
      ]),
    );
  }

  Widget _errorView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.terrain_outlined, color: _muted, size: 40),
          const SizedBox(height: 12),
          Text(_err, textAlign: TextAlign.center,
              style: const TextStyle(color: _muted, fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          TextButton(onPressed: () => Navigator.of(context).maybePop(), child: const Text('Go back')),
        ]),
      ),
    );
  }
}

// A mountain filled up to the achieved altitude (rating fraction) — shows "how
// high you climbed" behind the rating number.
class _ClimbPainter extends CustomPainter {
  final double frac; // 0..1
  _ClimbPainter(this.frac);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width, h = size.height;
    final mtn = Path()
      ..moveTo(0, h)
      ..lineTo(w * 0.16, h * 0.58)
      ..lineTo(w * 0.30, h * 0.74)
      ..lineTo(w * 0.50, h * 0.26)
      ..lineTo(w * 0.68, h * 0.64)
      ..lineTo(w * 0.84, h * 0.44)
      ..lineTo(w, h * 0.70)
      ..lineTo(w, h)
      ..close();
    canvas.drawPath(mtn, Paint()..color = const Color(0xFFFFE3C2)); // unclimbed
    final yLine = h * (1 - frac);
    canvas.save();
    canvas.clipRect(Rect.fromLTRB(0, yLine, w, h));
    final shader = const LinearGradient(
      colors: [Color(0xFFFFA64D), _orange, _orangeD],
      begin: Alignment.topCenter, end: Alignment.bottomCenter,
    ).createShader(Rect.fromLTWH(0, 0, w, h));
    canvas.drawPath(mtn, Paint()..shader = shader);
    canvas.restore();
    canvas.drawLine(Offset(0, yLine), Offset(w, yLine),
        Paint()..color = Colors.white.withValues(alpha: 0.7)..strokeWidth = 2);
  }

  @override
  bool shouldRepaint(_ClimbPainter old) => old.frac != frac;
}
