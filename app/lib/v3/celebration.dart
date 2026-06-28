// A visible, joyful "you got it!" celebration — a confetti burst that pops over
// the screen when a young learner answers correctly. Self-contained (no extra
// package): an Overlay + CustomPainter particle system that removes itself.
//
// Sound is OFF by default and mutable (a parent didn't want Khan-style chimes),
// while the *visible* celebration stays on by default because that's what
// actually delights young kids. Both are toggled in Profile.

import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

class CelebrationPrefs {
  static const _kConfetti = 'v3_celebrate';
  static const _kSound = 'v3_sound';
  static bool confetti = true;   // visible celebration — on by default
  static bool sound = false;     // audible cue — off by default (mutable)

  static Future<void> load() async {
    final p = await SharedPreferences.getInstance();
    confetti = p.getBool(_kConfetti) ?? true;
    sound = p.getBool(_kSound) ?? false;
  }

  static Future<void> setConfetti(bool v) async {
    confetti = v;
    (await SharedPreferences.getInstance()).setBool(_kConfetti, v);
  }

  static Future<void> setSound(bool v) async {
    sound = v;
    (await SharedPreferences.getInstance()).setBool(_kSound, v);
  }
}

const _confettiColors = [
  Color(0xFFFF6D00), Color(0xFFFFC233), Color(0xFF12A99B),
  Color(0xFFFF5470), Color(0xFF2FA866), Color(0xFF7A5CFF), Color(0xFF3D7DF6),
];

/// Fire a celebration. `intensity` ~1.0 normal, higher = more confetti (young
/// learners L1–L3 get a bigger burst).
void celebrate(BuildContext context, {double intensity = 1.0}) {
  if (CelebrationPrefs.sound) {
    SystemSound.play(SystemSoundType.click);
  }
  if (!CelebrationPrefs.confetti) return;
  HapticFeedback.mediumImpact();
  final overlay = Overlay.maybeOf(context);
  if (overlay == null) return;
  late OverlayEntry entry;
  entry = OverlayEntry(
    builder: (_) => _ConfettiLayer(intensity: intensity, onDone: () => entry.remove()),
  );
  overlay.insert(entry);
}

class _Particle {
  double x, y, vx, vy, rot, rotV, size;
  Color color;
  int shape; // 0 rect, 1 circle
  _Particle(this.x, this.y, this.vx, this.vy, this.rot, this.rotV, this.size, this.color, this.shape);
}

class _ConfettiLayer extends StatefulWidget {
  final double intensity;
  final VoidCallback onDone;
  const _ConfettiLayer({required this.intensity, required this.onDone});
  @override
  State<_ConfettiLayer> createState() => _ConfettiLayerState();
}

class _ConfettiLayerState extends State<_ConfettiLayer> with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  late final List<_Particle> _ps;
  final _rng = Random();

  @override
  void initState() {
    super.initState();
    final n = (40 * widget.intensity).round();
    _ps = List.generate(n, (_) {
      final ang = -pi / 2 + (_rng.nextDouble() - 0.5) * 1.7; // mostly upward
      final speed = 0.55 + _rng.nextDouble() * 0.95;
      return _Particle(
        0.5 + (_rng.nextDouble() - 0.5) * 0.25, // x (fraction of width)
        0.46,                                   // y start (fraction of height)
        cos(ang) * speed,                       // vx
        sin(ang) * speed,                       // vy (negative = up)
        _rng.nextDouble() * pi,                 // rot
        (_rng.nextDouble() - 0.5) * 7,          // rotV
        6 + _rng.nextDouble() * 8,              // size px
        _confettiColors[_rng.nextInt(_confettiColors.length)],
        _rng.nextInt(2),
      );
    });
    _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))
      ..addListener(() {
        if (mounted) setState(() {});
      })
      ..forward().then((_) => widget.onDone());
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(size: Size.infinite, painter: _ConfettiPainter(_ps, _c.value)),
    );
  }
}

class _ConfettiPainter extends CustomPainter {
  final List<_Particle> ps;
  final double t;
  _ConfettiPainter(this.ps, this.t);

  @override
  void paint(Canvas canvas, Size size) {
    const g = 1.5; // gravity
    final paint = Paint();
    for (final p in ps) {
      final px = (p.x + p.vx * t) * size.width;
      final py = (p.y - p.vy * t + 0.5 * g * t * t) * size.height;
      final op = t < 0.7 ? 1.0 : (1.0 - (t - 0.7) / 0.3).clamp(0.0, 1.0);
      if (op <= 0) continue;
      paint.color = p.color.withValues(alpha: op);
      canvas.save();
      canvas.translate(px, py);
      canvas.rotate(p.rot + p.rotV * t);
      if (p.shape == 0) {
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromCenter(center: Offset.zero, width: p.size, height: p.size * 0.55),
            const Radius.circular(1.5),
          ),
          paint,
        );
      } else {
        canvas.drawCircle(Offset.zero, p.size * 0.4, paint);
      }
      canvas.restore();
    }
  }

  @override
  bool shouldRepaint(_ConfettiPainter old) => old.t != t;
}
