// Kiwimath immersive book reader — our own Kindle-style reading UI built
// directly on flutter_epub_viewer (epub.js). The page is the whole screen; a
// tap in the centre reveals a top bar (back · contents · Aa) and a bottom bar
// (a scrubber to jump anywhere + progress). Tap the left/right thirds to turn.
//
// All chrome is our Flutter code — full control, Kiwimath-themed. The engine
// only renders the EPUB. Position is remembered per book by CFI (precise).

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_epub_viewer/flutter_epub_viewer.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart' show ApiClient;
import '../services/authed_http.dart' as http;

const Color _kBrand = Color(0xFFFF6F00);

enum _ReaderTheme { light, sepia, dark }

class BookReaderScreen extends StatefulWidget {
  final String bookId;
  final String title;
  const BookReaderScreen({super.key, required this.bookId, required this.title});

  @override
  State<BookReaderScreen> createState() => _BookReaderScreenState();
}

class _BookReaderScreenState extends State<BookReaderScreen> {
  final EpubController _controller = EpubController();
  File? _file;
  bool _loading = true;
  String? _error;

  // chrome + viewer
  bool _chrome = false;          // top/bottom bars visible
  bool _located = false;         // epub.js locations ready (safe to seek)
  bool _ready = false;           // book has painted (hide the loading veil)
  Widget? _viewer;               // built once per (flow,theme); reused otherwise
  final ValueNotifier<double> _progress = ValueNotifier<double>(0);
  List<EpubChapter> _flatChapters = [];

  // settings
  int _fontPx = 18;
  EpubFlow _flow = EpubFlow.paginated;
  _ReaderTheme _theme = _ReaderTheme.light;
  int _marginLevel = 1;          // 0 narrow · 1 normal · 2 wide
  int _lineLevel = 1;            // 0 compact · 1 normal · 2 relaxed

  // position (precise, by CFI)
  String? _resumeCfi;            // seek here once locations load
  String? _curCfi;               // latest location
  int _lastSaveMs = 0;
  String? _returnCfi;            // "back to my spot" target after a jump
  String? _navChapterId;         // chapter last opened from the contents list
  String? _scrubFrom;            // where the reader was when a scrub began

  // tap detection
  Offset? _downPt;
  int _downMs = 0;
  double? _dragValue;            // scrubber while dragging

  String get _posKey => 'kiwi_reader.cfi.${widget.bookId}';
  static const _fontKey = 'kiwi_reader.fontPx';
  static const _flowKey = 'kiwi_reader.flow';
  static const _themeKey = 'kiwi_reader.theme';
  static const _marginKey = 'kiwi_reader.margin';
  static const _lineKey = 'kiwi_reader.line';

  @override
  void initState() {
    super.initState();
    _applyImmersion(reading: true); // start full-screen
    _init();
  }

  Future<void> _init() async {
    try {
      final p = await SharedPreferences.getInstance();
      _fontPx = (p.getInt(_fontKey) ?? 18).clamp(12, 40);
      _flow = p.getString(_flowKey) == 'scrolled'
          ? EpubFlow.scrolled
          : EpubFlow.paginated;
      switch (p.getString(_themeKey)) {
        case 'dark':
          _theme = _ReaderTheme.dark;
          break;
        case 'sepia':
          _theme = _ReaderTheme.sepia;
          break;
        default:
          _theme = _ReaderTheme.light;
      }
      _marginLevel = (p.getInt(_marginKey) ?? 1).clamp(0, 2);
      _lineLevel = (p.getInt(_lineKey) ?? 1).clamp(0, 2);
      _resumeCfi = p.getString(_posKey);

      final res = await http
          .get(Uri.parse(
              '${ApiClient.baseUrl}/v3/store/content/${widget.bookId}/bytes'))
          .timeout(const Duration(seconds: 45));
      if (res.statusCode != 200) throw StateError('bytes ${res.statusCode}');
      final dir = Directory.systemTemp.createTempSync('kiwi_book_');
      _file = File('${dir.path}/book.epub')..writeAsBytesSync(res.bodyBytes);
      if (!mounted) return;
      setState(() => _loading = false);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'Could not open this book. Please try again.';
      });
    }
  }

  @override
  void dispose() {
    _applyImmersion(reading: false); // restore the system bars for the app
    _savePosition();
    _progress.dispose();
    try {
      _file?.parent.deleteSync(recursive: true);
    } catch (_) {/* best-effort */}
    super.dispose();
  }

  // ---- persistence --------------------------------------------------------
  Future<void> _savePosition() async {
    if (_curCfi == null) return;
    try {
      final p = await SharedPreferences.getInstance();
      await p.setString(_posKey, _curCfi!);
    } catch (_) {}
  }

  void _savePositionThrottled() {
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _lastSaveMs < 2500) return;
    _lastSaveMs = now;
    _savePosition();
  }

  Future<void> _saveSettings() async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.setInt(_fontKey, _fontPx);
      await p.setString(
          _flowKey, _flow == EpubFlow.scrolled ? 'scrolled' : 'paginated');
      await p.setString(_themeKey, _theme.name);
      await p.setInt(_marginKey, _marginLevel);
      await p.setInt(_lineKey, _lineLevel);
    } catch (_) {}
  }

  // ---- reading controls ---------------------------------------------------
  void _turn(double x) {
    if (_chrome) {
      _setChrome(false); // any page tap hides the bars
      return;
    }
    if (_flow == EpubFlow.paginated && x < 0.30) {
      _controller.prev();
    } else if (_flow == EpubFlow.paginated && x > 0.70) {
      _controller.next();
    } else {
      _setChrome(true); // centre (or any scroll-mode tap) shows bars
    }
  }

  // Reading is fully immersive (system bars hidden); the bars return with the
  // reader chrome. The page truly fills the screen — the point of a reader.
  void _setChrome(bool v) {
    setState(() => _chrome = v);
    _applyImmersion(reading: !v);
  }

  void _applyImmersion({required bool reading}) {
    if (reading) {
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    } else {
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.manual,
          overlays: SystemUiOverlay.values);
    }
  }

  void _setFont(int px) {
    setState(() => _fontPx = px.clamp(12, 40));
    _controller.setFontSize(fontSize: _fontPx.toDouble());
    _saveSettings();
  }

  // Flow / theme / margins / spacing are build-time settings → re-create the
  // viewer (runtime switching is unreliable), keeping the reader's place via CFI.
  void _recreate() {
    _resumeCfi = _curCfi;
    _located = false;
    _viewer = null;
    setState(() {});
    _saveSettings();
  }

  void _setFlow(EpubFlow flow) {
    if (flow == _flow) return;
    _flow = flow;
    _recreate();
  }

  void _setTheme(_ReaderTheme t) {
    if (t == _theme) return;
    _theme = t;
    _recreate();
  }

  void _setMargin(int m) {
    if (m == _marginLevel) return;
    _marginLevel = m;
    _recreate();
  }

  void _setLine(int l) {
    if (l == _lineLevel) return;
    _lineLevel = l;
    _recreate();
  }

  void _seek() {
    if (_located && _resumeCfi != null && _resumeCfi!.isNotEmpty) {
      _controller.display(cfi: _resumeCfi!);
      _resumeCfi = null;
    }
  }

  // Jump-then-return: remember where the reader was, offer a one-tap "Back to
  // my spot" pill for a while. The key win for reference reading.
  void _offerReturn(String? from) {
    if (from == null || from.isEmpty) return;
    setState(() => _returnCfi = from);
    Future.delayed(const Duration(seconds: 25), () {
      if (mounted && _returnCfi == from) setState(() => _returnCfi = null);
    });
  }

  void _jumpTo(String cfi) {
    _offerReturn(_curCfi);
    _controller.display(cfi: cfi);
  }

  void _goBack() {
    final to = _returnCfi;
    if (to == null) return;
    _controller.display(cfi: to);
    setState(() => _returnCfi = null);
  }

  // ---- theme helpers ------------------------------------------------------
  Color get _pageBg => switch (_theme) {
        _ReaderTheme.light => const Color(0xFFFBF7EF),
        _ReaderTheme.sepia => const Color(0xFFFBF0D9),
        _ReaderTheme.dark => const Color(0xFF15171A),
      };
  Color get _chromeBg => switch (_theme) {
        _ReaderTheme.dark => const Color(0xFF22252A),
        _ => Colors.white,
      };
  Color get _onChrome => switch (_theme) {
        _ReaderTheme.dark => const Color(0xFFE8E6E1),
        _ => const Color(0xFF1B1B1F),
      };

  // One CSS path for every theme so margins + line spacing apply uniformly.
  EpubTheme _epubTheme() {
    final (bg, fg, head, link) = switch (_theme) {
      _ReaderTheme.light => ('#FBF7EF', '#23211C', '#111111', '#B45309'),
      _ReaderTheme.sepia => ('#FBF0D9', '#5B4636', '#3D2E22', '#8A5A2B'),
      _ReaderTheme.dark => ('#15171A', '#D7D3CB', '#FFFFFF', '#FFB870'),
    };
    final pad = const [12, 26, 46][_marginLevel];
    final lh = const ['1.4', '1.65', '2.0'][_lineLevel];
    return EpubTheme.custom(customCss: {
      'body': {
        'background': '$bg !important',
        'color': '$fg !important',
        'padding-left': '${pad}px !important',
        'padding-right': '${pad}px !important',
        'line-height': '$lh !important',
      },
      'p, div, span, li, td': {'color': '$fg !important', 'line-height': '$lh !important'},
      'h1, h2, h3, h4, h5, h6': {'color': '$head !important'},
      'a': {'color': '$link !important'},
    });
  }

  String? get _navChapterTitle {
    if (_navChapterId == null) return null;
    for (final c in _flatChapters) {
      if (c.id == _navChapterId) {
        final t = c.title.trim();
        return t.isEmpty ? null : t;
      }
    }
    return null;
  }

  // ---- the EPUB viewer (built once per flow+theme) ------------------------
  Widget _buildViewer() => EpubViewer(
        key: ValueKey('epub-${_flow.name}-${_theme.name}-$_marginLevel-$_lineLevel'),
        epubSource: EpubSource.fromFile(_file!),
        epubController: _controller,
        displaySettings: EpubDisplaySettings(
          flow: _flow,
          snap: _flow == EpubFlow.paginated,
          useSnapAnimationAndroid: false,
          fontSize: _fontPx,
          theme: _epubTheme(),
          allowScriptedContent: true,
        ),
        onEpubLoaded: () {
          if (mounted) setState(() => _ready = true); // hide the loading veil
        },
        onChaptersLoaded: (chapters) {
          final flat = <EpubChapter>[];
          void walk(List<EpubChapter> cs) {
            for (final c in cs) {
              flat.add(c);
              if (c.subitems.isNotEmpty) walk(c.subitems);
            }
          }

          walk(chapters);
          if (mounted) setState(() => _flatChapters = flat);
        },
        onLocationLoaded: () {
          _located = true;
          _seek();
        },
        onRelocated: (loc) {
          _curCfi = loc.startCfi;
          _progress.value = loc.progress;
          _savePositionThrottled();
        },
        onTouchDown: (x, y) {
          _downPt = Offset(x, y);
          _downMs = DateTime.now().millisecondsSinceEpoch;
        },
        onTouchUp: (x, y) {
          final start = _downPt;
          _downPt = null;
          if (start == null) return;
          final moved = (Offset(x, y) - start).distance;
          final held = DateTime.now().millisecondsSinceEpoch - _downMs;
          if (moved < 0.04 && held < 350) _turn(x); // a real tap
        },
      );

  // ---- chrome -------------------------------------------------------------
  void _openChapters() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: _chromeBg,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(18))),
      builder: (ctx) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.6,
        maxChildSize: 0.92,
        builder: (ctx, scroll) => Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 8),
              child: Row(
                children: [
                  Text('Contents',
                      style: TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 17,
                          color: _onChrome)),
                  const Spacer(),
                  IconButton(
                      onPressed: () => Navigator.pop(ctx),
                      icon: Icon(Icons.close, color: _onChrome)),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: _flatChapters.isEmpty
                  ? Center(
                      child: Text('Loading chapters…',
                          style: TextStyle(color: _onChrome.withValues(alpha: 0.6))))
                  : ListView.builder(
                      controller: scroll,
                      itemCount: _flatChapters.length,
                      itemBuilder: (ctx, i) {
                        final c = _flatChapters[i];
                        final cur = c.id == _navChapterId;
                        return ColoredBox(
                          color: cur
                              ? _kBrand.withValues(alpha: 0.10)
                              : Colors.transparent,
                          child: ListTile(
                            leading: cur
                                ? const Icon(Icons.menu_book, color: _kBrand, size: 20)
                                : null,
                            title: Text(
                                c.title.trim().isEmpty ? '—' : c.title.trim(),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                    color: cur ? _kBrand : _onChrome,
                                    fontWeight:
                                        cur ? FontWeight.w700 : FontWeight.w500,
                                    fontSize: 14.5)),
                            onTap: () {
                              setState(() => _navChapterId = c.id);
                              _setChrome(false);
                              _jumpTo(c.href);
                              Navigator.pop(ctx);
                            },
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openSearch() async {
    final cfi = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => _SearchScreen(
          controller: _controller,
          bg: _pageBg,
          chromeBg: _chromeBg,
          onChrome: _onChrome,
        ),
      ),
    );
    if (cfi != null && cfi.isNotEmpty && mounted) {
      _setChrome(false);
      _jumpTo(cfi); // search result jump gets the "back to my spot" pill too
    }
  }

  void _openSettings() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: _chromeBg,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(18))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheet) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 22),
            child: SingleChildScrollView(
              child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Display',
                    style: TextStyle(
                        fontWeight: FontWeight.w800, fontSize: 17, color: _onChrome)),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Text('Font size',
                        style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                    const Spacer(),
                    _circleBtn(Icons.remove, _fontPx > 12, () {
                      _setFont(_fontPx - 2);
                      setSheet(() {});
                    }),
                    SizedBox(
                        width: 44,
                        child: Text('$_fontPx',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                                fontWeight: FontWeight.w700, color: _onChrome))),
                    _circleBtn(Icons.add, _fontPx < 40, () {
                      _setFont(_fontPx + 2);
                      setSheet(() {});
                    }),
                  ],
                ),
                const SizedBox(height: 18),
                Text('Theme',
                    style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _themeSwatch('Light', const Color(0xFFFBF7EF), const Color(0xFF1B1B1F),
                        _ReaderTheme.light, setSheet),
                    const SizedBox(width: 10),
                    _themeSwatch('Sepia', const Color(0xFFFBF0D9), const Color(0xFF5B4636),
                        _ReaderTheme.sepia, setSheet),
                    const SizedBox(width: 10),
                    _themeSwatch('Dark', const Color(0xFF15171A), const Color(0xFFE8E6E1),
                        _ReaderTheme.dark, setSheet),
                  ],
                ),
                const SizedBox(height: 18),
                Text('Layout',
                    style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _modeChip('Pages', Icons.menu_book_outlined, EpubFlow.paginated, setSheet),
                    const SizedBox(width: 10),
                    _modeChip('Scroll', Icons.swap_vert, EpubFlow.scrolled, setSheet),
                  ],
                ),
                const SizedBox(height: 18),
                Text('Margins',
                    style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                const SizedBox(height: 8),
                _segRow(const ['Narrow', 'Normal', 'Wide'], _marginLevel, (i) {
                  _setMargin(i);
                  setSheet(() {});
                }),
                const SizedBox(height: 18),
                Text('Line spacing',
                    style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                const SizedBox(height: 8),
                _segRow(const ['Compact', 'Normal', 'Relaxed'], _lineLevel, (i) {
                  _setLine(i);
                  setSheet(() {});
                }),
              ],
            )),
          ),
        ),
      ),
    );
  }

  Widget _segRow(List<String> labels, int selected, void Function(int) onSelect) {
    return Row(
      children: [
        for (int i = 0; i < labels.length; i++) ...[
          if (i > 0) const SizedBox(width: 10),
          Expanded(
            child: InkWell(
              onTap: () => onSelect(i),
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: selected == i ? _kBrand.withValues(alpha: 0.12) : null,
                  border: Border.all(
                      color: selected == i
                          ? _kBrand
                          : _onChrome.withValues(alpha: 0.25),
                      width: selected == i ? 2 : 1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(labels[i],
                    style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: selected == i ? _kBrand : _onChrome,
                        fontSize: 13)),
              ),
            ),
          ),
        ],
      ],
    );
  }

  Widget _circleBtn(IconData icon, bool on, VoidCallback tap) => IconButton(
        onPressed: on ? tap : null,
        icon: Icon(icon, color: on ? _onChrome : _onChrome.withValues(alpha: 0.3)),
      );

  Widget _themeSwatch(String label, Color bg, Color fg, _ReaderTheme t,
          void Function(void Function()) setSheet) =>
      Expanded(
        child: InkWell(
          onTap: () {
            _setTheme(t);
            setSheet(() {});
          },
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: bg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                  color: _theme == t ? _kBrand : Colors.black.withValues(alpha: 0.12),
                  width: _theme == t ? 2.5 : 1),
            ),
            alignment: Alignment.center,
            child: Text('Aa',
                style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 17)),
          ),
        ),
      );

  Widget _modeChip(String label, IconData icon, EpubFlow flow,
      void Function(void Function()) setSheet) {
    final sel = _flow == flow;
    return Expanded(
      child: InkWell(
        onTap: () {
          _setFlow(flow);
          setSheet(() {});
        },
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: sel ? _kBrand.withValues(alpha: 0.12) : null,
            border: Border.all(
                color: sel ? _kBrand : _onChrome.withValues(alpha: 0.25),
                width: sel ? 2 : 1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            children: [
              Icon(icon, color: sel ? _kBrand : _onChrome),
              const SizedBox(height: 4),
              Text(label,
                  style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: sel ? _kBrand : _onChrome)),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator(color: _kBrand)),
      );
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(),
        body: Center(child: Text(_error!)),
      );
    }
    _viewer ??= _buildViewer();
    return Scaffold(
      backgroundColor: _pageBg,
      body: Stack(
        children: [
          Positioned.fill(child: _viewer!),
          // loading veil until epub.js has painted (no blank flash)
          if (!_ready)
            Positioned.fill(
              child: ColoredBox(
                color: _pageBg,
                child: const Center(
                    child: CircularProgressIndicator(color: _kBrand)),
              ),
            ),
          // top bar
          AnimatedPositioned(
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
            left: 0,
            right: 0,
            top: _chrome ? 0 : -120,
            child: _topBar(),
          ),
          // bottom bar
          AnimatedPositioned(
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
            left: 0,
            right: 0,
            bottom: _chrome ? 0 : -140,
            child: _bottomBar(),
          ),
          // "back to my spot" pill — appears after a contents/scrubber jump
          if (_returnCfi != null)
            Positioned(
              right: 16,
              bottom: _chrome ? 96 : 26,
              child: SafeArea(
                child: Material(
                  color: const Color(0xFF1B1B1F),
                  borderRadius: BorderRadius.circular(999),
                  elevation: 4,
                  child: InkWell(
                    onTap: _goBack,
                    borderRadius: BorderRadius.circular(999),
                    child: const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 14, vertical: 9),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.undo, color: Colors.white, size: 16),
                          SizedBox(width: 6),
                          Text('Back to my spot',
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13)),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _topBar() => Material(
        color: _chromeBg,
        elevation: 2,
        child: SafeArea(
          bottom: false,
          child: SizedBox(
            height: 52,
            child: Row(
              children: [
                IconButton(
                    onPressed: () => Navigator.of(context).maybePop(),
                    icon: Icon(Icons.arrow_back, color: _onChrome)),
                Expanded(
                  child: Text(widget.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                          color: _onChrome,
                          fontWeight: FontWeight.w700,
                          fontSize: 15)),
                ),
                IconButton(
                    onPressed: _openChapters,
                    tooltip: 'Contents',
                    icon: Icon(Icons.list, color: _onChrome)),
                IconButton(
                    onPressed: _openSearch,
                    tooltip: 'Search',
                    icon: Icon(Icons.search, color: _onChrome)),
                IconButton(
                    onPressed: _openSettings,
                    tooltip: 'Display',
                    icon: Text('Aa',
                        style: TextStyle(
                            color: _onChrome,
                            fontWeight: FontWeight.w800,
                            fontSize: 17))),
                const SizedBox(width: 4),
              ],
            ),
          ),
        ),
      );

  Widget _bottomBar() => Material(
        color: _chromeBg,
        elevation: 2,
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(18, 8, 18, 4),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // where am I: chapter (when known) + progress
                Row(
                  children: [
                    Expanded(
                      child: Text(_navChapterTitle ?? widget.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                              color: _onChrome,
                              fontWeight: FontWeight.w700,
                              fontSize: 12.5)),
                    ),
                    const SizedBox(width: 8),
                    ValueListenableBuilder<double>(
                      valueListenable: _progress,
                      builder: (_, v, __) => Text(
                          '${((_dragValue ?? v) * 100).round()}%',
                          style: TextStyle(
                              color: _onChrome.withValues(alpha: 0.65),
                              fontWeight: FontWeight.w600,
                              fontSize: 12)),
                    ),
                  ],
                ),
                // move: scrubber (Contents lives in the top bar)
                Row(
                  children: [
                    Expanded(
                      child: ValueListenableBuilder<double>(
                        valueListenable: _progress,
                        builder: (_, v, __) {
                          final value =
                              (_dragValue ?? v).clamp(0.0, 1.0).toDouble();
                          return SliderTheme(
                            data: SliderTheme.of(context).copyWith(
                              activeTrackColor: _kBrand,
                              thumbColor: _kBrand,
                              inactiveTrackColor:
                                  _onChrome.withValues(alpha: 0.2),
                              trackHeight: 3,
                            ),
                            child: Slider(
                              value: value,
                              onChangeStart: (_) => _scrubFrom = _curCfi,
                              onChanged: (x) => setState(() => _dragValue = x),
                              onChangeEnd: (x) {
                                _controller.toProgressPercentage(x);
                                _offerReturn(_scrubFrom);
                                setState(() => _dragValue = null);
                              },
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      );
}

// ===========================================================================
// Whole-book search — find a term/theorem and jump to it (with return pill).
// ===========================================================================
class _SearchHit {
  final String cfi;
  final String excerpt;
  const _SearchHit(this.cfi, this.excerpt);
}

class _SearchScreen extends StatefulWidget {
  final EpubController controller;
  final Color bg;
  final Color chromeBg;
  final Color onChrome;
  const _SearchScreen({
    required this.controller,
    required this.bg,
    required this.chromeBg,
    required this.onChrome,
  });

  @override
  State<_SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<_SearchScreen> {
  final TextEditingController _q = TextEditingController();
  List<_SearchHit> _hits = [];
  bool _searching = false;
  bool _searched = false;

  @override
  void dispose() {
    _q.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    final query = _q.text.trim();
    if (query.length < 2) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _searching = true;
      _searched = true;
    });
    var hits = <_SearchHit>[];
    try {
      // ENGINE CALL — flutter_epub_viewer EpubController.search.
      // Verified shape: search({required String query}) → List<EpubSearchResult>
      // with .cfi (String) + .excerpt (String).
      final results = await widget.controller.search(query: query);
      hits = results
          .map((r) => _SearchHit(r.cfi, r.excerpt))
          .where((h) => h.cfi.isNotEmpty)
          .toList();
    } catch (_) {/* tolerate any engine quirk — show "no results" */}
    if (!mounted) return;
    setState(() {
      _hits = hits;
      _searching = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final muted = widget.onChrome.withValues(alpha: 0.6);
    return Scaffold(
      backgroundColor: widget.bg,
      appBar: AppBar(
        backgroundColor: widget.chromeBg,
        foregroundColor: widget.onChrome,
        titleSpacing: 0,
        title: TextField(
          controller: _q,
          autofocus: true,
          textInputAction: TextInputAction.search,
          onSubmitted: (_) => _run(),
          style: TextStyle(color: widget.onChrome, fontSize: 16),
          cursorColor: _kBrand,
          decoration: InputDecoration(
            hintText: 'Search this book',
            border: InputBorder.none,
            hintStyle: TextStyle(color: muted),
          ),
        ),
        actions: [
          IconButton(
              onPressed: _run,
              icon: Icon(Icons.search, color: widget.onChrome)),
        ],
      ),
      body: _searching
          ? const Center(child: CircularProgressIndicator(color: _kBrand))
          : !_searched
              ? Center(
                  child: Text('Find a word, theorem, or phrase.',
                      style: TextStyle(color: muted)))
              : _hits.isEmpty
                  ? Center(
                      child: Text('No results for “${_q.text.trim()}”.',
                          style: TextStyle(color: muted)))
                  : ListView.separated(
                      itemCount: _hits.length,
                      separatorBuilder: (_, __) =>
                          Divider(height: 1, color: muted.withValues(alpha: 0.2)),
                      itemBuilder: (_, i) {
                        final h = _hits[i];
                        return ListTile(
                          leading: Icon(Icons.search, size: 18, color: muted),
                          title: Text(h.excerpt.trim(),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                              style: TextStyle(
                                  color: widget.onChrome,
                                  fontSize: 14,
                                  height: 1.4)),
                          onTap: () => Navigator.pop(context, h.cfi),
                        );
                      },
                    ),
    );
  }
}
