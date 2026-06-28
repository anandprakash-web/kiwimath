import '../util/equality.dart';
import 'enums.dart';

/// Describes one readable unit (chapter / page-range / section).
class SectionRef {
  final String id;
  final String? title;
  final String? href;

  const SectionRef({required this.id, this.title, this.href});

  Map<String, dynamic> toJson() => {
        'id': id,
        if (title != null) 'title': title,
        if (href != null) 'href': href,
      };

  factory SectionRef.fromJson(Map<String, dynamic> j) => SectionRef(
        id: j['id'] as String,
        title: j['title'] as String?,
        href: j['href'] as String?,
      );
}

/// What the host's `ContentProvider` returns. [contentVersion] is the trigger
/// for re-anchoring: when it changes, every annotation is re-resolved against
/// the new content and a reconciliation report is produced.
class BookManifest {
  final String id;
  final BookFormat format;
  final String contentVersion;
  final List<SectionRef> sections;
  final String? title;

  /// Opaque license/entitlement blob the host understands (DRM hook).
  final Map<String, dynamic>? license;

  const BookManifest({
    required this.id,
    required this.format,
    required this.contentVersion,
    required this.sections,
    this.title,
    this.license,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'format': format.name,
        'contentVersion': contentVersion,
        'sections': sections.map((s) => s.toJson()).toList(),
        if (title != null) 'title': title,
        if (license != null) 'license': license,
      };

  factory BookManifest.fromJson(Map<String, dynamic> j) => BookManifest(
        id: j['id'] as String,
        format: BookFormat.values.byName(j['format'] as String),
        contentVersion: j['contentVersion'] as String,
        sections: (j['sections'] as List)
            .map(
                (e) => SectionRef.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        title: j['title'] as String?,
        license: j['license'] == null
            ? null
            : Map<String, dynamic>.from(j['license'] as Map),
      );

  @override
  bool operator ==(Object other) =>
      other is BookManifest && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(id, format, contentVersion);
}
