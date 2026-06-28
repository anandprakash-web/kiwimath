// Kiwimath Library — a fully owned, Kiwimath-themed book browser.
//
// This is OUR code end to end: catalog/wallet/entitlement calls go straight to
// the backend, covers are hand-painted in Dart (no network/asset dependency),
// and the Store/Library/filter UI is plain Flutter. Opening a book pushes our
// own immersive reader (book_reader.dart). The only third-party piece in the
// whole books feature is the EPUB *render engine* (epub.js via flutter_epub_viewer).
//
// Nothing here depends on KiwiReader's StoreScreen/LibraryScreen, so the app's
// look is 100% controlled by us (the "green default" surprise can't recur).

import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

import '../services/api_client.dart' show ApiClient;
import '../services/authed_http.dart' as http;
import 'book_reader.dart';
import 'html_book_reader.dart';

const Color _kBrand = Color(0xFFFF6F00); // Kiwimath orange
const Color _kInk = Color(0xFF1B1B1F);
const Color _kMuted = Color(0xFF6B7280);

// ===========================================================================
// Model
// ===========================================================================
class BookInfo {
  final String id;
  final String title;
  final String author;
  final String? subtitle;
  final String subject;
  final String gradeBand;
  final List<int> levels;
  final String format;
  final bool comingSoon;
  final bool isFree;
  final int? coins;
  final int? amountMinor;
  final String? currency;
  bool owned;

  BookInfo({
    required this.id,
    required this.title,
    required this.author,
    required this.subtitle,
    required this.subject,
    required this.gradeBand,
    required this.levels,
    required this.format,
    required this.comingSoon,
    required this.isFree,
    required this.coins,
    required this.amountMinor,
    required this.currency,
    this.owned = false,
  });

  factory BookInfo.fromJson(Map<String, dynamic> j) {
    final pricing = (j['pricing'] as Map?)?.cast<String, dynamic>();
    return BookInfo(
      id: '${j['id']}',
      title: '${j['title'] ?? 'Untitled'}',
      author: '${j['author'] ?? 'Kiwimath'}',
      subtitle: j['subtitle'] as String?,
      subject: '${j['subject'] ?? 'Mixed'}',
      gradeBand: '${j['gradeBand'] ?? ''}',
      levels: ((j['levels'] as List?) ?? const [])
          .map((e) => int.tryParse('$e') ?? 0)
          .where((e) => e > 0)
          .toList(),
      format: '${j['format'] ?? 'epub'}',
      comingSoon: j['comingSoon'] == true,
      isFree: pricing == null ? false : pricing['isFree'] == true,
      coins: pricing == null ? null : (pricing['coins'] as num?)?.toInt(),
      amountMinor: pricing == null ? null : (pricing['amountMinor'] as num?)?.toInt(),
      currency: pricing?['currency'] as String?,
    );
  }

  bool get isSchoolIssued => !comingSoon && coins == null && amountMinor == null && !isFree;

  /// What the action area should say.
  String get statusLabel {
    if (comingSoon) return 'Coming soon';
    if (owned) return 'Read';
    if (isFree || isSchoolIssued) return 'Get free';
    if (coins != null) return 'Unlock';
    return 'Buy';
  }
}

// ===========================================================================
// Backend client (all our endpoints — no KiwiReader providers involved)
// ===========================================================================
class BooksService {
  String? get _uid => FirebaseAuth.instance.currentUser?.uid;

  Future<List<BookInfo>> catalog() async {
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/catalog'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) return const [];
    final list = (jsonDecode(res.body)['books'] as List?) ?? const [];
    return list
        .map((e) => BookInfo.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }

  Future<Set<String>> ownedIds() async {
    final uid = _uid;
    if (uid == null) return {};
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/entitlements?user_id=$uid'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) return {};
    return ((jsonDecode(res.body)['owned'] as List?) ?? const [])
        .map((e) => '$e')
        .toSet();
  }

  Future<int> coins() async {
    final uid = _uid;
    if (uid == null) return 0;
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/economy/wallet?user_id=$uid'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) return 0;
    return (jsonDecode(res.body)['coins'] as num?)?.toInt() ?? 0;
  }

  /// Unlock a coin-priced book. Server enforces the price + records ownership.
  Future<UnlockResult> unlock(BookInfo b) async {
    final uid = _uid;
    if (uid == null) return const UnlockResult(false, 0, 'no_user');
    final price = b.coins;
    if (price == null) return const UnlockResult(false, 0, 'not_coin_priced');
    final res = await http
        .post(
          Uri.parse('${ApiClient.baseUrl}/v3/economy/spend'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'user_id': uid,
            'currency': 'coins',
            'amount': price,
            'sku': b.id,
            'reason': 'unlock_book',
            'idempotency_key': '$uid:${b.id}:unlock', // stable → no double-charge
          }),
        )
        .timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      return const UnlockResult(false, 0, 'error');
    }
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    final bal = (j['newBalance'] as num?)?.toInt() ?? 0;
    return UnlockResult(j['ok'] == true, bal, j['ok'] == true ? null : '${j['error'] ?? 'failed'}');
  }

  Future<bool> claimFree(String id) async {
    final uid = _uid;
    if (uid == null) return false;
    final res = await http
        .post(
          Uri.parse('${ApiClient.baseUrl}/v3/store/claim'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'user_id': uid, 'book_id': id}),
        )
        .timeout(const Duration(seconds: 12));
    return res.statusCode == 200;
  }
}

class UnlockResult {
  final bool ok;
  final int balance;
  final String? error;
  const UnlockResult(this.ok, this.balance, this.error);
}

// ===========================================================================
// Downloads — purchased books are downloaded to local storage, then read
// offline. A book only appears in "Downloads" once its bytes are on the device.
// ===========================================================================
class BookDownloads {
  static Future<Directory> _dir() async {
    final base = await getApplicationDocumentsDirectory();
    final d = Directory('${base.path}/kiwi_books');
    if (!d.existsSync()) d.createSync(recursive: true);
    return d;
  }

  static Future<String> _pathFor(String id) async => '${(await _dir()).path}/$id.html';

  static Future<String?> localPath(String id) async {
    final p = await _pathFor(id);
    return File(p).existsSync() ? p : null;
  }

  /// Which book ids are already downloaded on this device.
  static Future<Set<String>> downloadedIds() async {
    final d = await _dir();
    return d
        .listSync()
        .whereType<File>()
        .map((f) => f.uri.pathSegments.last)
        .where((n) => n.endsWith('.html'))
        .map((n) => n.substring(0, n.length - 5))
        .toSet();
  }

  /// Fetch the (entitlement-gated) bytes and save them locally. Returns the path.
  static Future<String?> download(String id) async {
    final uid = FirebaseAuth.instance.currentUser?.uid;
    if (uid == null) return null;
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/content/$id/bytes'))
        .timeout(const Duration(seconds: 120));
    if (res.statusCode != 200) return null;
    final p = await _pathFor(id);
    final tmp = File('$p.part')..writeAsBytesSync(res.bodyBytes); // atomic-ish
    tmp.renameSync(p);
    return p;
  }

  static Future<void> remove(String id) async {
    final f = File(await _pathFor(id));
    if (f.existsSync()) f.deleteSync();
  }
}

// ===========================================================================
// Hand-painted cover art (pure Dart — beautiful + zero external dependency)
// ===========================================================================
class _Palette {
  final Color base;
  final Color accent;
  final Color ink;
  const _Palette(this.base, this.accent, this.ink);
}

const _cream = Color(0xFFF4E9D2);
const _gold = Color(0xFFE7B14C);

_Palette _paletteFor(String subject) {
  switch (subject) {
    case 'Geometry':
      return const _Palette(Color(0xFF12302A), _gold, _cream);
    case 'Algebra':
      return const _Palette(Color(0xFF1C1B3C), _gold, _cream);
    case 'Number Theory':
      return const _Palette(Color(0xFF2A1430), _gold, _cream);
    case 'Combinatorics':
      return const _Palette(Color(0xFF0F2438), _gold, _cream);
    case 'Study Skills':
      return const _Palette(Color(0xFF2C2622), _gold, _cream);
    default:
      return const _Palette(Color(0xFF24202C), _gold, _cream);
  }
}

Color _darken(Color c, [double amount = 0.18]) {
  final h = HSLColor.fromColor(c);
  return h.withLightness((h.lightness - amount).clamp(0.0, 1.0)).toColor();
}

/// Friendly tier name for a book's level, shown as a badge so per-pillar-per-level
/// books ("RMO Number Theory" vs "IOQM Number Theory") read apart at a glance.
String _tierLabel(List<int> levels) {
  if (levels.isEmpty) return '';
  const names = {5: 'IOQM', 6: 'RMO', 7: 'INMO', 8: 'IMO'};
  final n = levels.first;
  return names[n] ?? 'L$n';
}

/// A premium, designed-looking cover painted entirely in Flutter.
class BookCoverArt extends StatelessWidget {
  final BookInfo book;
  final double radius;
  const BookCoverArt({super.key, required this.book, this.radius = 12});

  @override
  Widget build(BuildContext context) {
    final p = _paletteFor(book.subject);
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: AspectRatio(
        aspectRatio: 3 / 4,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [p.base, _darken(p.base)],
            ),
          ),
          child: CustomPaint(
            painter: _CoverPainter(book.subject, p.accent),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(14, 16, 14, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          book.subject.toUpperCase(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: p.accent,
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.6,
                          ),
                        ),
                      ),
                      if (_tierLabel(book.levels).isNotEmpty)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                          decoration: BoxDecoration(
                            border: Border.all(color: p.accent.withValues(alpha: 0.8)),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            _tierLabel(book.levels),
                            style: TextStyle(
                              color: p.accent,
                              fontSize: 8.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ),
                    ],
                  ),
                  const Spacer(),
                  Text(
                    book.title,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: p.ink,
                      fontSize: 17,
                      height: 1.15,
                      fontWeight: FontWeight.w800,
                      fontFamily: 'Georgia',
                    ),
                  ),
                  const SizedBox(height: 6),
                  Container(width: 26, height: 2, color: p.accent),
                  const SizedBox(height: 6),
                  Text(
                    book.author,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: p.ink.withValues(alpha: 0.82),
                      fontSize: 10.5,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.4,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Faint subject motif + frame, stroked in the accent colour.
class _CoverPainter extends CustomPainter {
  final String subject;
  final Color accent;
  _CoverPainter(this.subject, this.accent);

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.1
      ..color = accent.withValues(alpha: 0.20);

    // inner frame
    final frame = Rect.fromLTWH(7, 7, size.width - 14, size.height - 14);
    canvas.drawRRect(
        RRect.fromRectAndRadius(frame, const Radius.circular(6)), stroke);

    final cx = size.width * 0.5;
    final cy = size.height * 0.40;
    final r = size.width * 0.34;
    final dot = Paint()..color = accent.withValues(alpha: 0.55);

    switch (subject) {
      case 'Geometry':
        canvas.drawCircle(Offset(cx, cy), r, stroke);
        canvas.drawCircle(Offset(cx, cy), r * 0.72, stroke);
        final tri = Path()
          ..moveTo(cx, cy - r)
          ..lineTo(cx + r * 0.87, cy + r * 0.5)
          ..lineTo(cx - r * 0.87, cy + r * 0.5)
          ..close();
        canvas.drawPath(tri, stroke);
        canvas.drawLine(Offset(cx - r, cy), Offset(cx + r, cy), stroke);
        canvas.drawCircle(Offset(cx, cy), 2.4, dot);
        break;
      case 'Algebra':
        // a parabola + axes
        canvas.drawLine(Offset(cx - r, cy), Offset(cx + r, cy), stroke);
        canvas.drawLine(Offset(cx, cy - r), Offset(cx, cy + r), stroke);
        final par = Path()..moveTo(cx - r, cy - r * 0.9);
        for (double x = -1.0; x <= 1.0; x += 0.1) {
          par.lineTo(cx + x * r, cy + (x * x - 0.5) * r);
        }
        canvas.drawPath(par, stroke);
        break;
      case 'Number Theory':
        // a triangular lattice of dots
        for (int row = 0; row < 5; row++) {
          for (int i = 0; i <= row; i++) {
            final dx = cx + (i - row / 2) * (r * 0.42);
            final dy = cy - r * 0.7 + row * (r * 0.38);
            canvas.drawCircle(Offset(dx, dy), 2.6, dot);
          }
        }
        break;
      case 'Combinatorics':
        // a small graph: nodes on a circle + chords
        final pts = <Offset>[];
        for (int i = 0; i < 6; i++) {
          final a = i * math.pi / 3 - math.pi / 2;
          pts.add(Offset(cx + r * math.cos(a), cy + r * math.sin(a)));
        }
        for (int i = 0; i < pts.length; i++) {
          for (int j = i + 1; j < pts.length; j++) {
            if ((i + j).isEven) canvas.drawLine(pts[i], pts[j], stroke);
          }
        }
        for (final pt in pts) {
          canvas.drawCircle(pt, 3.0, dot);
        }
        break;
      case 'Study Skills':
        // an open book
        final left = Path()
          ..moveTo(cx, cy - r * 0.5)
          ..lineTo(cx - r, cy - r * 0.25)
          ..lineTo(cx - r, cy + r * 0.6)
          ..lineTo(cx, cy + r * 0.35)
          ..close();
        final right = Path()
          ..moveTo(cx, cy - r * 0.5)
          ..lineTo(cx + r, cy - r * 0.25)
          ..lineTo(cx + r, cy + r * 0.6)
          ..lineTo(cx, cy + r * 0.35)
          ..close();
        canvas.drawPath(left, stroke);
        canvas.drawPath(right, stroke);
        break;
      default:
        canvas.drawCircle(Offset(cx, cy), r, stroke);
        canvas.drawRect(
            Rect.fromCenter(center: Offset(cx, cy), width: r * 1.4, height: r * 1.4),
            stroke);
    }
  }

  @override
  bool shouldRepaint(covariant _CoverPainter old) =>
      old.subject != subject || old.accent != accent;
}

// ===========================================================================
// The Library tab body — Store + My Books, with a grade/level filter
// ===========================================================================
class BooksBrowseBody extends StatefulWidget {
  /// When set (e.g. "L3"), the Library opens pre-filtered to that level so it
  /// matches the app's chosen level. The user can still widen via the filter.
  final String? lockedLevel;
  const BooksBrowseBody({super.key, this.lockedLevel});

  @override
  State<BooksBrowseBody> createState() => _BooksBrowseBodyState();
}

class _BooksBrowseBodyState extends State<BooksBrowseBody> {
  final BooksService _svc = BooksService();
  List<BookInfo> _all = [];
  int _coins = 0;
  bool _loading = true;
  String? _error;
  final Set<int> _fLevels = {};
  final Set<String> _fSubjects = {};
  final Set<String> _downloaded = {}; // book ids with a local copy
  final Set<String> _downloading = {}; // book ids fetching right now

  @override
  void initState() {
    super.initState();
    // Open scoped to the app's chosen level (e.g. "L3" -> level 3).
    final ll = widget.lockedLevel;
    if (ll != null) {
      final n = int.tryParse(ll.replaceAll(RegExp(r'[^0-9]'), ''));
      if (n != null) _fLevels.add(n);
    }
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final books = await _svc.catalog();
      final owned = await _svc.ownedIds();
      final coins = await _svc.coins();
      final downloaded = await BookDownloads.downloadedIds();
      for (final b in books) {
        b.owned = owned.contains(b.id);
      }
      if (!mounted) return;
      setState(() {
        _all = books;
        _coins = coins;
        _downloaded
          ..clear()
          ..addAll(downloaded);
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Could not load the library.';
      });
    }
  }

  List<BookInfo> _apply(Iterable<BookInfo> src) {
    return src.where((b) {
      final levelOk = _fLevels.isEmpty || b.levels.any((lv) => _fLevels.contains(lv));
      final subjectOk = _fSubjects.isEmpty || _fSubjects.contains(b.subject);
      return levelOk && subjectOk;
    }).toList();
  }

  int get _activeFilters => _fLevels.length + _fSubjects.length;

  // ---- actions ----
  Future<void> _open(BookInfo b) async {
    // Read the downloaded copy if present (offline); else stream once.
    final local = await BookDownloads.localPath(b.id);
    if (!mounted) return;
    Navigator.of(context).push(MaterialPageRoute<void>(
      builder: (_) => b.format == 'html'
          ? HtmlBookReader(bookId: b.id, title: b.title, localPath: local)
          : BookReaderScreen(bookId: b.id, title: b.title),
    ));
  }

  // Store flow: Get (purchase, free) → Download → Read.
  Future<void> _onTap(BookInfo b) async {
    if (b.comingSoon) {
      _snack('“${b.title}” is coming soon.');
      return;
    }
    if (!b.owned) {
      if (b.coins != null) {
        await _confirmUnlock(b); // phase-2 paid path (no coin books in MVP)
        return;
      }
      final ok = await _svc.claimFree(b.id);
      if (!mounted) return;
      if (ok) {
        setState(() => b.owned = true);
        _snack('Added to your library — tap Download to read offline.');
      } else {
        _snack('Could not add this book.');
      }
      return;
    }
    if (!_downloaded.contains(b.id)) {
      await _download(b);
      return;
    }
    _open(b);
  }

  Future<void> _download(BookInfo b) async {
    if (_downloading.contains(b.id)) return;
    setState(() => _downloading.add(b.id));
    String? path;
    try {
      path = await BookDownloads.download(b.id);
    } catch (_) {
      path = null;
    }
    if (!mounted) return;
    setState(() {
      _downloading.remove(b.id);
      if (path != null) _downloaded.add(b.id);
    });
    if (path != null) {
      _open(b);
    } else {
      _snack('Download failed — check your connection and try again.');
    }
  }

  Future<void> _confirmUnlock(BookInfo b) async {
    final price = b.coins!;
    final enough = _coins >= price;
    final go = await showModalBottomSheet<bool>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 22),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(b.title,
                  style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
              const SizedBox(height: 4),
              Text(b.author, style: const TextStyle(color: _kMuted)),
              const SizedBox(height: 16),
              Row(children: [
                const Icon(Icons.monetization_on, color: _kBrand, size: 20),
                const SizedBox(width: 6),
                Text('$price coins',
                    style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                const Spacer(),
                Text('You have $_coins',
                    style: TextStyle(
                        color: enough ? _kMuted : Colors.redAccent,
                        fontWeight: FontWeight.w600)),
              ]),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  style: FilledButton.styleFrom(
                      backgroundColor: _kBrand,
                      padding: const EdgeInsets.symmetric(vertical: 14)),
                  onPressed: enough ? () => Navigator.pop(ctx, true) : null,
                  child: Text(enough ? 'Unlock & read' : 'Not enough coins'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
    if (go != true || !mounted) return;
    final res = await _svc.unlock(b);
    if (!mounted) return;
    if (res.ok) {
      setState(() {
        b.owned = true;
        _coins = res.balance;
      });
      _open(b);
    } else {
      _snack(res.error == 'insufficient'
          ? 'Not enough coins yet — keep practising!'
          : 'Could not unlock the book.');
    }
  }

  void _snack(String m) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text(m)));

  // ---- filter sheet ----
  Future<void> _openFilter() async {
    final subjects = (_all.map((b) => b.subject).toSet().toList())..sort();
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheet) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 18),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  const Text('Filter books',
                      style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                  const Spacer(),
                  if (_activeFilters > 0)
                    TextButton(
                      onPressed: () => setSheet(() {
                        _fLevels.clear();
                        _fSubjects.clear();
                      }),
                      child: const Text('Clear all'),
                    ),
                ]),
                const SizedBox(height: 8),
                const Text('Level', style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (int lv = 1; lv <= 8; lv++)
                      FilterChip(
                        label: Text('L$lv'),
                        selected: _fLevels.contains(lv),
                        selectedColor: _kBrand.withValues(alpha: 0.16),
                        checkmarkColor: _kBrand,
                        onSelected: (s) => setSheet(() =>
                            s ? _fLevels.add(lv) : _fLevels.remove(lv)),
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                const Text('Subject', style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    for (final s in subjects)
                      FilterChip(
                        label: Text(s),
                        selected: _fSubjects.contains(s),
                        selectedColor: _kBrand.withValues(alpha: 0.16),
                        checkmarkColor: _kBrand,
                        onSelected: (sel) => setSheet(() =>
                            sel ? _fSubjects.add(s) : _fSubjects.remove(s)),
                      ),
                  ],
                ),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                        backgroundColor: _kBrand,
                        padding: const EdgeInsets.symmetric(vertical: 14)),
                    onPressed: () => Navigator.pop(ctx),
                    child: const Text('Show books'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: _kBrand));
    }
    if (_error != null) {
      return _Retry(message: _error!, onRetry: _load);
    }
    final cs = Theme.of(context).colorScheme;
    final store = _apply(_all);
    final downloads = _apply(_all.where((b) => _downloaded.contains(b.id)));
    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          _filterBar(),
          Material(
            color: Theme.of(context).scaffoldBackgroundColor,
            child: TabBar(
              labelColor: cs.primary,
              indicatorColor: cs.primary,
              tabs: [
                const Tab(text: 'Store'),
                Tab(text: downloads.isEmpty ? 'Downloads' : 'Downloads (${downloads.length})'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                _grid(store, emptyText: 'No books match your filter.'),
                _grid(downloads,
                    emptyText: 'No downloads yet.\nGet a book from the Store, then tap Download.'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 10, 8, 4),
      child: Row(
        children: [
          Expanded(
            child: _activeFilters == 0
                ? const Text('Browse the Kiwimath library',
                    style: TextStyle(color: _kMuted, fontWeight: FontWeight.w600))
                : Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      for (final lv in (_fLevels.toList()..sort()))
                        _activeChip('L$lv', () => setState(() => _fLevels.remove(lv))),
                      for (final s in _fSubjects)
                        _activeChip(s, () => setState(() => _fSubjects.remove(s))),
                    ],
                  ),
          ),
          OutlinedButton.icon(
            onPressed: _openFilter,
            icon: const Icon(Icons.tune, size: 18),
            label: Text(_activeFilters == 0 ? 'Filter' : 'Filter ($_activeFilters)'),
            style: OutlinedButton.styleFrom(
              foregroundColor: _kBrand,
              side: const BorderSide(color: _kBrand),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _activeChip(String label, VoidCallback onRemove) {
    return InputChip(
      label: Text(label),
      onDeleted: onRemove,
      backgroundColor: _kBrand.withValues(alpha: 0.10),
      labelStyle: const TextStyle(color: _kBrand, fontWeight: FontWeight.w700, fontSize: 12),
      deleteIconColor: _kBrand,
      visualDensity: VisualDensity.compact,
    );
  }

  Widget _grid(List<BookInfo> books, {required String emptyText}) {
    if (books.isEmpty) {
      return RefreshIndicator(
        onRefresh: _load,
        color: _kBrand,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
          const SizedBox(height: 120),
          Icon(Icons.menu_book_outlined, size: 56, color: _kMuted.withValues(alpha: 0.5)),
          const SizedBox(height: 12),
          Center(
              child: Text(emptyText,
                  style: const TextStyle(color: _kMuted, fontWeight: FontWeight.w600))),
        ]),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      color: _kBrand,
      child: GridView.builder(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 20),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
          childAspectRatio: 0.56,
        ),
        itemCount: books.length,
        itemBuilder: (ctx, i) => _BookCard(
          book: books[i],
          downloaded: _downloaded.contains(books[i].id),
          downloading: _downloading.contains(books[i].id),
          onTap: () => _onTap(books[i]),
        ),
      ),
    );
  }
}

// ===========================================================================
// Card
// ===========================================================================
class _BookCard extends StatelessWidget {
  final BookInfo book;
  final bool downloaded;
  final bool downloading;
  final VoidCallback onTap;
  const _BookCard(
      {required this.book,
      required this.onTap,
      this.downloaded = false,
      this.downloading = false});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Stack(
              children: [
                Positioned.fill(
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.16),
                          blurRadius: 10,
                          offset: const Offset(0, 5),
                        ),
                      ],
                    ),
                    child: BookCoverArt(book: book),
                  ),
                ),
                if (book.comingSoon)
                  const Positioned(top: 8, left: 8, child: _Ribbon('SOON', Color(0xFF6B7280))),
                if (downloaded)
                  const Positioned(top: 8, left: 8, child: _Ribbon('SAVED', _kBrand)),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(book.title,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w800, color: _kInk, fontSize: 13.5)),
          Text(book.gradeBand.isEmpty ? book.subject : 'Grade ${book.gradeBand} · ${book.subject}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: _kMuted, fontSize: 11, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          _statusPill(),
        ],
      ),
    );
  }

  Widget _statusPill() {
    Color bg = const Color(0xFFFFF1E3);
    Color fg = _kBrand;
    String text;
    if (book.comingSoon) {
      bg = const Color(0xFFEFF1F4);
      fg = _kMuted;
      text = 'Coming soon';
    } else if (downloading) {
      text = 'Downloading…';
    } else if (downloaded) {
      text = 'Read now';
    } else if (book.owned) {
      text = 'Download';
    } else if (book.coins != null) {
      text = '${book.coins} coins';
    } else {
      bg = const Color(0xFFE8F5E9);
      fg = const Color(0xFF2E7D32);
      text = 'Get · Free';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (downloading) ...[
            SizedBox(
                width: 11,
                height: 11,
                child: CircularProgressIndicator(strokeWidth: 2, color: fg)),
            const SizedBox(width: 6),
          ],
          Text(text,
              style: TextStyle(color: fg, fontSize: 11, fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}

class _Ribbon extends StatelessWidget {
  final String text;
  final Color color;
  const _Ribbon(this.text, this.color);
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(6)),
        child: Text(text,
            style: const TextStyle(
                color: Colors.white, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 0.8)),
      );
}

class _Retry extends StatelessWidget {
  final String message;
  final Future<void> Function() onRetry;
  const _Retry({required this.message, required this.onRetry});
  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, style: const TextStyle(color: _kMuted)),
            const SizedBox(height: 10),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: _kBrand),
              onPressed: onRetry,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
}
