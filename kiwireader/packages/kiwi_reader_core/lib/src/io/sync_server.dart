import 'dart:convert';
import 'dart:io';

import '../sync/in_memory_api.dart';
import '../sync/sync_models.dart';

/// A runnable reference implementation of the Annotation & Sync API over HTTP,
/// wrapping [InMemoryAnnotationApi]. Implements `POST /v1/sync` per
/// `openapi/openapi.yaml` plus a `GET /health`. Use it as a local dev backend
/// (`bin/mock_server.dart`) and as the server side of the HTTP sync tests.
class SyncServer {
  final InMemoryAnnotationApi api;
  HttpServer? _server;

  /// The Authorization header seen on the most recent `/v1/sync` request
  /// (lets tests assert the client sent its bearer token).
  String? lastAuthHeader;

  SyncServer({InMemoryAnnotationApi? api})
      : api = api ?? InMemoryAnnotationApi();

  int? get port => _server?.port;

  Future<int> start({int port = 0, String host = '127.0.0.1'}) async {
    final server = await HttpServer.bind(host, port);
    _server = server;
    server.listen(_handle);
    return server.port;
  }

  Future<void> stop() async {
    await _server?.close(force: true);
    _server = null;
  }

  Future<void> _handle(HttpRequest req) async {
    try {
      if (req.method == 'POST' && req.uri.path == '/v1/sync') {
        lastAuthHeader = req.headers.value(HttpHeaders.authorizationHeader);
        final body = await utf8.decoder.bind(req).join();
        final request =
            SyncRequest.fromJson(jsonDecode(body) as Map<String, dynamic>);
        final response = await api.sync(request);
        req.response
          ..statusCode = HttpStatus.ok
          ..headers.contentType = ContentType.json
          ..write(jsonEncode(response.toJson()));
      } else if (req.method == 'GET' && req.uri.path == '/health') {
        req.response
          ..statusCode = HttpStatus.ok
          ..write('ok');
      } else {
        req.response.statusCode = HttpStatus.notFound;
      }
    } catch (e) {
      req.response
        ..statusCode = HttpStatus.badRequest
        ..write('error: $e');
    } finally {
      await req.response.close();
    }
  }
}
