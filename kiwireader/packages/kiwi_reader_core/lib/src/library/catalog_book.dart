import '../commerce/pricing.dart';
import '../models/enums.dart';
import '../util/equality.dart';

/// One row in the library catalog the backend serves.
///
/// The host's `CatalogProvider` returns these. Books are uploaded / ingested
/// on the **backend** — never from the app — so there is no upload surface in
/// the reader; the Library tab only lists and downloads.
///
/// A [CatalogBook] carries just enough to render a library card and start a
/// download. The full [BookManifest] (sections, license, …) is fetched from
/// the `ContentProvider` when the book is actually opened, so the catalog stays
/// cheap to list.
class CatalogBook {
  final String id;
  final String title;
  final BookFormat format;

  /// Mirrors `BookManifest.contentVersion`. When the backend re-publishes a
  /// book this changes, which lets a stale offline copy be detected and
  /// re-downloaded.
  final String contentVersion;

  final String? author;
  final String? subtitle;

  /// Where the cover art lives (host URL/URI). Optional — the card shows a
  /// generated placeholder when absent.
  final String? coverUrl;

  /// Total content size in bytes when the backend knows it. Drives the
  /// download progress bar; downloads still work when null (indeterminate).
  final int? byteSize;

  /// How the book is acquired in the Store (free / coins / money / both).
  /// `null` means the book needs no acquisition (e.g. school-issued) — it never
  /// appears in the Store and is treated as owned.
  final BookPricing? pricing;

  const CatalogBook({
    required this.id,
    required this.title,
    required this.format,
    required this.contentVersion,
    this.author,
    this.subtitle,
    this.coverUrl,
    this.byteSize,
    this.pricing,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'format': format.name,
        'contentVersion': contentVersion,
        if (author != null) 'author': author,
        if (subtitle != null) 'subtitle': subtitle,
        if (coverUrl != null) 'coverUrl': coverUrl,
        if (byteSize != null) 'byteSize': byteSize,
        if (pricing != null) 'pricing': pricing!.toJson(),
      };

  factory CatalogBook.fromJson(Map<String, dynamic> j) => CatalogBook(
        id: j['id'] as String,
        title: j['title'] as String,
        format: BookFormat.values.byName(j['format'] as String),
        contentVersion: j['contentVersion'] as String,
        author: j['author'] as String?,
        subtitle: j['subtitle'] as String?,
        coverUrl: j['coverUrl'] as String?,
        byteSize: (j['byteSize'] as num?)?.toInt(),
        pricing: j['pricing'] == null
            ? null
            : BookPricing.fromJson(Map<String, dynamic>.from(j['pricing'] as Map)),
      );

  @override
  bool operator ==(Object other) =>
      other is CatalogBook && deepEquals(toJson(), other.toJson());

  @override
  int get hashCode => Object.hash(id, format, contentVersion);
}
