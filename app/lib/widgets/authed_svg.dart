import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../services/authed_http.dart' as http;

/// Renders an SVG fetched from the Kiwimath backend WITH the Firebase
/// auth header attached. `SvgPicture.network` cannot send auth headers,
/// so backend visual endpoints (now token-protected) would return 401.
///
/// Drop-in replacement:
///   SvgPicture.network(url, ...) -> AuthedSvg(url: url, ...)
class AuthedSvg extends StatefulWidget {
  const AuthedSvg({
    super.key,
    required this.url,
    this.fit = BoxFit.contain,
    this.semanticsLabel,
    this.placeholderBuilder,
    this.errorBuilder,
  });

  final String url;
  final BoxFit fit;
  final String? semanticsLabel;
  final WidgetBuilder? placeholderBuilder;
  final Widget Function(BuildContext, Object, StackTrace?)? errorBuilder;

  // Tiny in-memory cache so revisiting a question doesn't refetch.
  static final Map<String, String> _cache = <String, String>{};
  static const int _cacheCap = 60;

  @override
  State<AuthedSvg> createState() => _AuthedSvgState();
}

class _AuthedSvgState extends State<AuthedSvg> {
  String? _svg;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(AuthedSvg oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.url != widget.url) {
      _svg = null;
      _error = null;
      _load();
    }
  }

  Future<void> _load() async {
    final cached = AuthedSvg._cache[widget.url];
    if (cached != null) {
      setState(() => _svg = cached);
      return;
    }
    try {
      final resp = await http.get(Uri.parse(widget.url));
      if (!mounted) return;
      if (resp.statusCode == 200 && resp.body.contains('<svg')) {
        if (AuthedSvg._cache.length >= AuthedSvg._cacheCap) {
          AuthedSvg._cache.remove(AuthedSvg._cache.keys.first);
        }
        AuthedSvg._cache[widget.url] = resp.body;
        setState(() => _svg = resp.body);
      } else {
        setState(() => _error = 'HTTP ${resp.statusCode}');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return widget.errorBuilder?.call(context, _error!, null) ??
          const SizedBox.shrink();
    }
    if (_svg == null) {
      return widget.placeholderBuilder?.call(context) ??
          const SizedBox(
            height: 60,
            child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
          );
    }
    return SvgPicture.string(
      _svg!,
      fit: widget.fit,
      semanticsLabel: widget.semanticsLabel,
    );
  }
}
