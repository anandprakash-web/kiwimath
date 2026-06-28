import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// A stream of content bytes (so large PDFs can be streamed, not fully loaded).
typedef ByteStream = Stream<List<int>>;

/// An optional byte range for ranged/streamed reads.
class ByteRange {
  final int start;
  final int? end;
  const ByteRange(this.start, [this.end]);
}

/// HOST INTERFACE #1 — content.
///
/// kiwimaths implements this. The reader never assumes where content lives
/// (CDN, bundled asset, encrypted blob) or how it is licensed.
abstract class ContentProvider {
  Future<BookManifest> manifest(String bookId);
  Future<ByteStream> bytes(String bookId, {ByteRange? range});
  Future<Uri?> coverImage(String bookId);
}

/// HOST INTERFACE #2 — auth.
///
/// Supplies the token for the sync backend and a sign-out signal so the reader
/// can flush + clear local state. The host keeps its auth secrets.
abstract class AuthProvider {
  Future<String> accessToken();
  String get userId;
  Stream<void> get onSignOut;
}

/// HOST INTERFACE #3 — catalog.
///
/// Returns the books available to this user. Books are uploaded / ingested on
/// the **backend** — there is no upload surface in the reader — so from the
/// app's perspective the catalog is read-only. Typically the same backend that
/// serves [ContentProvider] bytes also serves this list.
///
/// The Library tab lists these and lets the user download any of them for
/// offline reading via the core `DownloadManager`. Opening a book then goes
/// through the existing [ContentProvider]/renderer path unchanged.
abstract class CatalogProvider {
  /// The current catalog for the signed-in user (drives the Library grid;
  /// re-invoked on pull-to-refresh).
  Future<List<CatalogBook>> books();
}
