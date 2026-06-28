/// KiwiReader core — dart:io extras (NOT exported from the default barrel so
/// the core stays web-safe). Import this explicitly on desktop / server / tests:
///
/// ```dart
/// import 'package:kiwi_reader_core/io.dart';
/// ```
library kiwi_reader_core.io;

export 'src/io/json_file_store.dart';
export 'src/io/http_annotation_api.dart';
export 'src/io/sync_server.dart';
