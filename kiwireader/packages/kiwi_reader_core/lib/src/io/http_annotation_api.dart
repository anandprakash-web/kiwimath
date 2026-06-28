import 'dart:convert';
import 'dart:io';

import '../sync/annotation_api.dart';
import '../sync/sync_models.dart';

/// Talks to the real Annotation & Sync backend over HTTP (`POST /v1/sync`),
/// matching `openapi/openapi.yaml`. Pure dart:io so it is testable against an
/// in-process [SyncServer]; the Flutter app can use this directly or a Dio
/// variant (same [AnnotationApi] interface).
class HttpAnnotationApi implements AnnotationApi {
  final Uri baseUri;
  final Future<String> Function()? tokenProvider;
  final HttpClient _client;

  HttpAnnotationApi(this.baseUri, {this.tokenProvider, HttpClient? client})
      : _client = client ?? HttpClient();

  @override
  Future<SyncResponse> sync(SyncRequest request) async {
    final uri = Uri(
      scheme: baseUri.scheme,
      host: baseUri.host,
      port: baseUri.port,
      path: '/v1/sync',
    );
    final httpReq = await _client.postUrl(uri);
    httpReq.headers.contentType = ContentType.json;
    if (tokenProvider != null) {
      httpReq.headers.add(
          HttpHeaders.authorizationHeader, 'Bearer ${await tokenProvider!()}');
    }
    httpReq.add(utf8.encode(jsonEncode(request.toJson())));
    final resp = await httpReq.close();
    final body = await resp.transform(utf8.decoder).join();
    if (resp.statusCode != 200) {
      throw HttpException('sync failed (${resp.statusCode}): $body', uri: uri);
    }
    return SyncResponse.fromJson(jsonDecode(body) as Map<String, dynamic>);
  }

  void close() => _client.close(force: true);
}
