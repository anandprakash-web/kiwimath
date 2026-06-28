// Kiwimath HTML book reader — a fully OWNED reader for books that ship a
// self-contained HTML edition (e.g. Euclid's Garden's Mobile.html). We render
// the book's own HTML in a plain WebView we control, so scrolling is
// native-smooth. Dark mode rides the book's `body.night` hook; font scales the
// root <html> size (the book is rem/em-based and has no <main> for --fscale).
//
// Modes: continuous scroll OR paged "flip" (CSS columns slid by a transform,
// Kindle-style side-tap zones). Immersive chrome · theme · font · resume.

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api_client.dart' show ApiClient;
import '../services/authed_http.dart' as http;

const Color _kBrand = Color(0xFFFF6F00);

enum _Theme { light, sepia, dark }

class HtmlBookReader extends StatefulWidget {
  final String bookId;
  final String title;
  /// When set (a downloaded copy), the book loads from this local file with no
  /// network fetch — fully offline. Otherwise the bytes are streamed once.
  final String? localPath;
  const HtmlBookReader(
      {super.key, required this.bookId, required this.title, this.localPath});

  @override
  State<HtmlBookReader> createState() => _HtmlBookReaderState();
}

class _HtmlBookReaderState extends State<HtmlBookReader> {
  InAppWebViewController? _web;
  String? _filePath; // file loaded by the WebView (downloaded copy or staged temp)
  bool _ownsTemp = false; // true only when we created a temp file to clean up
  bool _loading = true;
  String? _error;
  bool _chrome = false;
  bool _ready = false;

  final ValueNotifier<double> _progress = ValueNotifier<double>(0);
  int _fontPct = 100; // scales the root <html> font-size (book is rem/em-based)
  _Theme _theme = _Theme.light;
  bool _paged = false; // false = continuous scroll, true = flip like a book
  double _resumeFrac = 0;
  int _lastSaveMs = 0;

  String get _posKey => 'kiwi_html.pos.${widget.bookId}';
  static const _fontKey = 'kiwi_html.font';
  static const _themeKey = 'kiwi_html.theme';
  static const _pagedKey = 'kiwi_html.paged';

  @override
  void initState() {
    super.initState();
    _applyImmersion(reading: true);
    _init();
  }

  Future<void> _init() async {
    try {
      final p = await SharedPreferences.getInstance();
      _fontPct = (p.getInt(_fontKey) ?? 100).clamp(70, 220);
      switch (p.getString(_themeKey)) {
        case 'dark':
          _theme = _Theme.dark;
          break;
        case 'sepia':
          _theme = _Theme.sepia;
          break;
        default:
          _theme = _Theme.light;
      }
      _paged = p.getBool(_pagedKey) ?? false;
      _resumeFrac = p.getDouble(_posKey) ?? 0;

      // Downloaded copy → load it directly, fully offline (no fetch).
      if (widget.localPath != null && File(widget.localPath!).existsSync()) {
        _filePath = widget.localPath;
        _ownsTemp = false;
        if (!mounted) return;
        setState(() => _loading = false);
        return;
      }
      final res = await http
          .get(Uri.parse(
              '${ApiClient.baseUrl}/v3/store/content/${widget.bookId}/bytes'))
          .timeout(const Duration(seconds: 90));
      if (res.statusCode != 200) throw StateError('bytes ${res.statusCode}');
      // Stage to a temp file and load via file:// — robust for large books
      // (a multi-MB self-contained HTML shouldn't ride the platform channel as
      // one initialData string). The book is self-contained (inline images), so
      // only basic allowFileAccess is needed — no cross-origin file flags.
      final dir = Directory.systemTemp.createTempSync('kiwi_html_');
      final f = File('${dir.path}/book.html')..writeAsBytesSync(res.bodyBytes);
      _filePath = f.path;
      _ownsTemp = true;
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
    _applyImmersion(reading: false);
    _savePosition();
    _progress.dispose();
    try {
      // only clean up the temp copy we created — never a downloaded book.
      if (_ownsTemp && _filePath != null) {
        File(_filePath!).parent.deleteSync(recursive: true);
      }
    } catch (_) {/* best-effort temp cleanup */}
    super.dispose();
  }

  void _applyImmersion({required bool reading}) {
    if (reading) {
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    } else {
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.manual,
          overlays: SystemUiOverlay.values);
    }
  }

  void _setChrome(bool v) {
    setState(() => _chrome = v);
    _applyImmersion(reading: !v);
  }

  // ---- persistence --------------------------------------------------------
  Future<void> _savePosition() async {
    try {
      final p = await SharedPreferences.getInstance();
      await p.setDouble(_posKey, _progress.value);
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
      await p.setInt(_fontKey, _fontPct);
      await p.setString(_themeKey, _theme.name);
      await p.setBool(_pagedKey, _paged);
    } catch (_) {}
  }

  // ---- the in-page controller (injected once) -----------------------------
  // This book has NO <main> element, so its own `main{font-size:..var(--fscale)}`
  // rule styles nothing — that's why --fscale did nothing. Body text inherits
  // 16px straight from <html>, so we scale the root font-size instead (the book
  // is entirely rem/em-based, so everything scales). Paged ("flip") mode lays
  // the body out as full-width CSS columns and slides it with a transform.
  static const String _bootScript = r"""
    (function(){
      if (window.__kiwi) return;
      var st=document.createElement('style'); st.id='kiwi-paged-css';
      st.textContent =
        'html.kpaged{height:100vh;overflow:hidden;}'+
        'html.kpaged body{height:100vh;margin:0;padding:0 22px;box-sizing:border-box;'+
          'column-width:calc(100vw - 44px);-webkit-column-width:calc(100vw - 44px);'+
          'column-gap:44px;-webkit-column-gap:44px;column-fill:auto;-webkit-column-fill:auto;'+
          'transition:transform .26s ease;will-change:transform;}'+
        'html.kpaged .bar{display:none;}'+
        'html.kpaged section{padding-left:0;padding-right:0;}'+
        'html.kpaged .lib{padding-left:0;padding-right:0;max-width:none;}'+
        'html.kpaged figure,html.kpaged svg,html.kpaged img,html.kpaged pre,html.kpaged table{break-inside:avoid;}';
      document.head.appendChild(st);

      var K = window.__kiwi = {
        paged:false, cur:0, _t:null,
        count:function(){return Math.max(1, Math.ceil((document.body.scrollWidth-1)/window.innerWidth));},
        report:function(){
          var f;
          if(this.paged){var n=this.count(); f=n>1?this.cur/(n-1):0;}
          else{var h=document.body.scrollHeight-window.innerHeight; f=h>0?window.scrollY/h:0;}
          f=Math.max(0,Math.min(1,f));
          window.flutter_inappwebview.callHandler('kprogress', f);
        },
        _place:function(animate){
          var body=document.body;
          body.style.transition = animate ? 'transform .26s ease' : 'none';
          body.style.transform = 'translateX('+(-this.cur*window.innerWidth)+'px)';
          if(!animate){ void body.offsetWidth; body.style.transition='transform .26s ease'; }
        },
        go:function(dir){
          if(!this.paged) return;
          var n=this.count();
          this.cur=Math.max(0,Math.min(n-1,this.cur+dir));
          this._place(true); this.report();
        },
        setFont:function(pct){
          document.documentElement.style.fontSize = pct+'%';
          if(this.paged){ var s=this; setTimeout(function(){ var n=s.count(); s.cur=Math.min(s.cur,n-1); s._place(false); s.report(); },30); }
        },
        setTheme:function(night,sepia){
          document.body.classList.toggle('night', !!night);
          var r=document.documentElement.style;
          if(sepia){ r.setProperty('--bg','#FBF0D9'); r.setProperty('--fg','#5B4636'); r.setProperty('--card','#FBF0D9'); }
          else { r.removeProperty('--bg'); r.removeProperty('--fg'); r.removeProperty('--card'); }
        },
        setPaged:function(on,frac){
          this.paged=!!on; var s=this;
          if(on){
            document.documentElement.classList.add('kpaged');
            setTimeout(function(){ var n=s.count(); s.cur=Math.round((frac||0)*(n-1)); s._place(false); s.report(); },60);
          } else {
            document.documentElement.classList.remove('kpaged');
            document.body.style.transform=''; document.body.style.transition='';
            setTimeout(function(){ var h=document.body.scrollHeight-window.innerHeight; window.scrollTo(0,(frac||0)*Math.max(1,h)); s.report(); },60);
          }
        }
      };

      var bar=document.querySelector('.bar'); if(bar) bar.style.display='none';

      window.addEventListener('scroll', function(){ if(K._t) return; K._t=setTimeout(function(){ K._t=null; if(!K.paged) K.report(); },120); }, {passive:true});

      document.addEventListener('click', function(e){
        // let interactive controls (links, reveal toggles, form fields) act
        // without turning a page or toggling chrome.
        if(e.target && e.target.closest &&
           e.target.closest('a,button,summary,details,label,input,select,textarea,[data-tap]')) return;
        if(K.paged){
          var xf=e.clientX/window.innerWidth;
          if(xf<0.30){ K.go(-1); return; }
          if(xf>0.72){ K.go(1); return; }
        }
        window.flutter_inappwebview.callHandler('ktap', 0);
      }, true);
    })();
  """;

  void _setPaged(bool on) {
    setState(() => _paged = on);
    _web?.evaluateJavascript(
        source: "window.__kiwi && window.__kiwi.setPaged($on, ${_progress.value});");
    _saveSettings();
  }

  Color get _pageBg => switch (_theme) {
        _Theme.light => const Color(0xFFFCFBF7),
        _Theme.sepia => const Color(0xFFFBF0D9),
        _Theme.dark => const Color(0xFF15171C),
      };
  Color get _chromeBg => switch (_theme) {
        _Theme.dark => const Color(0xFF1F232B),
        _ => Colors.white,
      };
  Color get _onChrome => switch (_theme) {
        _Theme.dark => const Color(0xFFE6E9EF),
        _ => const Color(0xFF1B1B1F),
      };

  void _setFont(int pct) {
    setState(() => _fontPct = pct.clamp(70, 220));
    _web?.evaluateJavascript(
        source: "window.__kiwi && window.__kiwi.setFont($_fontPct);");
    _saveSettings();
  }

  void _setTheme(_Theme t) {
    setState(() => _theme = t);
    _web?.evaluateJavascript(source:
        "window.__kiwi && window.__kiwi.setTheme(${t == _Theme.dark}, ${t == _Theme.sepia});");
    _saveSettings();
  }

  // ---- webview wiring ------------------------------------------------------
  void _onCreated(InAppWebViewController c) {
    _web = c;
    // reading position (0..1, from whichever mode is active) → progress + save
    c.addJavaScriptHandler(
      handlerName: 'kprogress',
      callback: (args) {
        if (args.isNotEmpty) {
          final f = (args.first as num).toDouble().clamp(0.0, 1.0);
          _progress.value = f;
          _savePositionThrottled();
        }
        return null;
      },
    );
    // a centre tap (or any tap in scroll mode) toggles the reader chrome
    c.addJavaScriptHandler(
      handlerName: 'ktap',
      callback: (args) {
        _setChrome(!_chrome);
        return null;
      },
    );
  }

  Future<void> _onLoadStop() async {
    final w = _web;
    if (w == null) return;
    await w.evaluateJavascript(source: _bootScript);
    // apply state in order: theme (no reflow) → font (reflows) → mode+position.
    await w.evaluateJavascript(source:
        "window.__kiwi.setTheme(${_theme == _Theme.dark}, ${_theme == _Theme.sepia});"
        "window.__kiwi.setFont($_fontPct);"
        "window.__kiwi.setPaged($_paged, $_resumeFrac);");
    if (mounted) setState(() => _ready = true);
  }

  // ---- settings sheet -----------------------------------------------------
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
                    IconButton(
                        onPressed: _fontPct > 70
                            ? () {
                                _setFont(_fontPct - 10);
                                setSheet(() {});
                              }
                            : null,
                        icon: Icon(Icons.text_decrease, color: _onChrome)),
                    SizedBox(
                        width: 56,
                        child: Text('$_fontPct%',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                                fontWeight: FontWeight.w700, color: _onChrome))),
                    IconButton(
                        onPressed: _fontPct < 220
                            ? () {
                                _setFont(_fontPct + 10);
                                setSheet(() {});
                              }
                            : null,
                        icon: Icon(Icons.text_increase, color: _onChrome)),
                  ],
                ),
                const SizedBox(height: 18),
                Text('Theme',
                    style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _swatch('Light', const Color(0xFFFCFBF7), const Color(0xFF1B1B1F),
                        _Theme.light, setSheet),
                    const SizedBox(width: 10),
                    _swatch('Sepia', const Color(0xFFFBF0D9), const Color(0xFF5B4636),
                        _Theme.sepia, setSheet),
                    const SizedBox(width: 10),
                    _swatch('Dark', const Color(0xFF15171C), const Color(0xFFE6E9EF),
                        _Theme.dark, setSheet),
                  ],
                ),
                const SizedBox(height: 18),
                Text('Reading',
                    style: TextStyle(fontWeight: FontWeight.w600, color: _onChrome)),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _modePill('Scroll', Icons.swap_vert, false, setSheet),
                    const SizedBox(width: 10),
                    _modePill('Pages', Icons.menu_book_outlined, true, setSheet),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _swatch(String label, Color bg, Color fg, _Theme t,
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
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: bg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                  color: _theme == t ? _kBrand : Colors.black.withValues(alpha: 0.12),
                  width: _theme == t ? 2.5 : 1),
            ),
            child: Text('Aa',
                style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 17)),
          ),
        ),
      );

  Widget _modePill(String label, IconData icon, bool paged,
          void Function(void Function()) setSheet) =>
      Expanded(
        child: InkWell(
          onTap: () {
            if (_paged != paged) _setPaged(paged);
            setSheet(() {});
          },
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 13),
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: _paged == paged ? _kBrand.withValues(alpha: 0.12) : null,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                  color: _paged == paged ? _kBrand : _onChrome.withValues(alpha: 0.18),
                  width: _paged == paged ? 2 : 1),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon,
                    size: 18,
                    color: _paged == paged ? _kBrand : _onChrome),
                const SizedBox(width: 7),
                Text(label,
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: _paged == paged ? _kBrand : _onChrome)),
              ],
            ),
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        backgroundColor: _pageBg,
        body: const Center(child: CircularProgressIndicator(color: _kBrand)),
      );
    }
    if (_error != null) {
      return Scaffold(appBar: AppBar(), body: Center(child: Text(_error!)));
    }
    return Scaffold(
      backgroundColor: _pageBg,
      body: Stack(
        children: [
          Positioned.fill(
            child: InAppWebView(
              initialUrlRequest:
                  URLRequest(url: WebUri('file://${_filePath!}')),
              initialSettings: InAppWebViewSettings(
                transparentBackground: true,
                supportZoom: true, // pinch-zoom figures
                builtInZoomControls: true,
                displayZoomControls: false,
                useWideViewPort: true, // honour the book's width=device-width
                loadWithOverviewMode: true, // fit page to screen on load
                verticalScrollBarEnabled: false,
                javaScriptEnabled: true,
                allowFileAccess: true, // read the staged temp .html
                domStorageEnabled: true,
                mediaPlaybackRequiresUserGesture: true,
              ),
              onWebViewCreated: _onCreated,
              onLoadStop: (c, url) => _onLoadStop(),
              // in-page anchors (#topic) load here; external links (video
              // solutions) open in the system browser / YouTube app instead.
              shouldOverrideUrlLoading: (c, action) async {
                final uri = action.request.url;
                if (uri == null) return NavigationActionPolicy.ALLOW;
                final s = uri.toString();
                final isInPage = s.startsWith('file://') ||
                    uri.fragment.isNotEmpty && uri.path.endsWith('book.html');
                if (isInPage) return NavigationActionPolicy.ALLOW;
                if (uri.scheme == 'http' || uri.scheme == 'https') {
                  try {
                    await launchUrl(Uri.parse(s),
                        mode: LaunchMode.externalApplication);
                  } catch (_) {}
                  return NavigationActionPolicy.CANCEL;
                }
                return NavigationActionPolicy.ALLOW;
              },
            ),
          ),
          if (!_ready)
            Positioned.fill(
              child: ColoredBox(
                color: _pageBg,
                child: const Center(
                    child: CircularProgressIndicator(color: _kBrand)),
              ),
            ),
          AnimatedPositioned(
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
            left: 0,
            right: 0,
            top: _chrome ? 0 : -120,
            child: _topBar(),
          ),
          AnimatedPositioned(
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOut,
            left: 0,
            right: 0,
            bottom: _chrome ? 0 : -120,
            child: _bottomBar(),
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
          child: SizedBox(
            height: 40,
            child: Center(
              child: ValueListenableBuilder<double>(
                valueListenable: _progress,
                builder: (_, v, __) => Text('${(v * 100).round()}%',
                    style: TextStyle(
                        color: _onChrome,
                        fontWeight: FontWeight.w700,
                        fontSize: 12.5)),
              ),
            ),
          ),
        ),
      );
}
