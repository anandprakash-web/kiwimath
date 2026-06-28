import '../util/equality.dart';
import 'locator.dart';

/// A saved location. Lighter than an annotation — no anchor resolution needed,
/// it just stores a [Locator] and an optional [label]. Soft-deleted + synced
/// the same way as annotations.
class Bookmark {
  final String id;
  final String bookId;
  final Locator locator;
  final String? label;
  final int revision;
  final String deviceId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? deletedAt;

  const Bookmark({
    required this.id,
    required this.bookId,
    required this.locator,
    required this.deviceId,
    required this.createdAt,
    required this.updatedAt,
    this.label,
    this.revision = 1,
    this.deletedAt,
  });

  bool get isDeleted => deletedAt != null;

  Bookmark copyWith({
    Locator? locator,
    String? label,
    int? revision,
    DateTime? updatedAt,
    DateTime? deletedAt,
  }) =>
      Bookmark(
        id: id,
        bookId: bookId,
        locator: locator ?? this.locator,
        label: label ?? this.label,
        revision: revision ?? this.revision,
        deviceId: deviceId,
        createdAt: createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
        deletedAt: deletedAt ?? this.deletedAt,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'bookId': bookId,
        'locator': locator.toJson(),
        if (label != null) 'label': label,
        'revision': revision,
        'deviceId': deviceId,
        'createdAt': createdAt.toUtc().toIso8601String(),
        'updatedAt': updatedAt.toUtc().toIso8601String(),
        if (deletedAt != null)
          'deletedAt': deletedAt!.toUtc().toIso8601String(),
      };

  factory Bookmark.fromJson(Map<String, dynamic> j) => Bookmark(
        id: j['id'] as String,
        bookId: j['bookId'] as String,
        locator:
            Locator.fromJson(Map<String, dynamic>.from(j['locator'] as Map)),
        label: j['label'] as String?,
        revision: (j['revision'] as num?)?.toInt() ?? 1,
        deviceId: j['deviceId'] as String,
        createdAt: DateTime.parse(j['createdAt'] as String),
        updatedAt: DateTime.parse(j['updatedAt'] as String),
        deletedAt: j['deletedAt'] == null
            ? null
            : DateTime.parse(j['deletedAt'] as String),
      );

  @override
  bool operator ==(Object other) =>
      other is Bookmark && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(id, revision, updatedAt, deletedAt);
}
