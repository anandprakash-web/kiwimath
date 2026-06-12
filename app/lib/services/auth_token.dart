import 'dart:math';

import 'package:firebase_auth/firebase_auth.dart';

/// Shared Firebase auth-token helper for all Kiwimath HTTP clients.
///
/// `getIdToken()` already caches and auto-refreshes internally; we add a
/// light ~5 minute memo on top so we don't await the plugin channel on
/// every single request. When no user is signed in, no header is sent.
class AuthToken {
  AuthToken._();

  static String? _cached;
  static String? _cachedUid;
  static DateTime? _fetchedAt;
  static const _maxAge = Duration(minutes: 5);

  /// Current user's ID token, or null when signed out / unavailable.
  static Future<String?> idToken() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) {
      clear();
      return null;
    }
    final now = DateTime.now();
    if (_cached != null &&
        _cachedUid == user.uid &&
        _fetchedAt != null &&
        now.difference(_fetchedAt!) < _maxAge) {
      return _cached;
    }
    try {
      _cached = await user.getIdToken();
      _cachedUid = user.uid;
      _fetchedAt = now;
    } catch (_) {
      // Token fetch failed (e.g. offline) — fall back to the last token if
      // it belongs to the same user, otherwise send no header.
      if (_cachedUid != user.uid) clear();
    }
    return _cached;
  }

  /// Drop the memoized token (called automatically when signed out).
  static void clear() {
    _cached = null;
    _cachedUid = null;
    _fetchedAt = null;
  }
}

/// Build request headers with `Authorization: Bearer <token>` attached when
/// a Firebase user is signed in. Returns an empty map when signed out.
Future<Map<String, String>> authHeaders() async {
  final token = await AuthToken.idToken();
  if (token == null || token.isEmpty) return <String, String>{};
  return <String, String>{'Authorization': 'Bearer $token'};
}

final Random _idemRandom = Random();

/// Generate a unique idempotency key (time + random hex — no uuid package).
/// Sent as `X-Idempotency-Key` on mutation POSTs so the backend can dedupe.
String newIdempotencyKey() {
  final ts = DateTime.now().microsecondsSinceEpoch.toRadixString(16);
  final rand = List.generate(
    20,
    (_) => _idemRandom.nextInt(16).toRadixString(16),
  ).join();
  return '$ts-$rand';
}
