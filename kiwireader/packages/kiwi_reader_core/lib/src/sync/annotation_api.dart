import 'sync_models.dart';

/// The remote contract the [SyncEngine] depends on. The real implementation is
/// a thin Dio client over `POST /v1/sync`; tests use [InMemoryAnnotationApi].
abstract class AnnotationApi {
  Future<SyncResponse> sync(SyncRequest request);
}
