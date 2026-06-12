/// Drop-in replacement for `package:http/http.dart` top-level helpers that
/// attaches the Firebase `Authorization: Bearer <token>` header to every
/// request (see [authHeaders] in auth_token.dart).
///
/// Usage: change `import 'package:http/http.dart' as http;` to
/// `import 'authed_http.dart' as http;` — all existing `http.get(...)` /
/// `http.post(...)` / `http.delete(...)` call sites then automatically send
/// the auth header. When no user is signed in, no header is added.
library;

import 'dart:convert' show Encoding;

import 'package:http/http.dart' as base;

import 'auth_token.dart';

export 'package:http/http.dart' show ClientException, Response;

Future<Map<String, String>> _merged(Map<String, String>? headers) async {
  final auth = await authHeaders();
  if (headers == null || headers.isEmpty) return auth;
  return <String, String>{...auth, ...headers};
}

Future<base.Response> get(Uri url, {Map<String, String>? headers}) async =>
    base.get(url, headers: await _merged(headers));

Future<base.Response> post(
  Uri url, {
  Map<String, String>? headers,
  Object? body,
  Encoding? encoding,
}) async =>
    base.post(url,
        headers: await _merged(headers), body: body, encoding: encoding);

Future<base.Response> put(
  Uri url, {
  Map<String, String>? headers,
  Object? body,
  Encoding? encoding,
}) async =>
    base.put(url,
        headers: await _merged(headers), body: body, encoding: encoding);

Future<base.Response> delete(
  Uri url, {
  Map<String, String>? headers,
  Object? body,
  Encoding? encoding,
}) async =>
    base.delete(url,
        headers: await _merged(headers), body: body, encoding: encoding);
