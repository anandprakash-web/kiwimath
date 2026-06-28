import 'package:kiwi_reader_core/io.dart';

/// Runnable local sync backend. Usage:
///   dart run kiwi_reader_core:mock_server [port]
Future<void> main(List<String> args) async {
  final port = args.isNotEmpty ? int.parse(args.first) : 8080;
  final server = SyncServer();
  final bound = await server.start(port: port);
  // ignore: avoid_print
  print('KiwiReader mock sync server listening on '
      'http://127.0.0.1:$bound  (POST /v1/sync, GET /health)');
}
