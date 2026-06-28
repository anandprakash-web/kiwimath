import '../util/equality.dart';
import 'anchor.dart';
import 'enums.dart';

/// One row to rule all five verbs (discriminated by [type]).
///
/// Sync metadata ([revision], [updatedAt], [deletedAt], [deviceId]) lives on
/// the entity itself so the merge logic and the delta protocol stay simple.
class Annotation {
  final String id;
  final String bookId;
  final AnnotationType type;

  /// Highlight/underline color token (e.g. "green"); null for notes/ink.
  final String? color;
  final Anchor anchor;

  /// Free text for [AnnotationType.note]; null otherwise.
  final String? noteText;

  /// Opaque payload for [AnnotationType.ink] strokes; null otherwise.
  final Map<String, dynamic>? ink;

  final int revision;
  final String deviceId;
  final DateTime createdAt;
  final DateTime updatedAt;

  /// Soft-delete tombstone. Non-null means deleted.
  final DateTime? deletedAt;

  const Annotation({
    required this.id,
    required this.bookId,
    required this.type,
    required this.anchor,
    required this.deviceId,
    required this.createdAt,
    required this.updatedAt,
    this.color,
    this.noteText,
    this.ink,
    this.revision = 1,
    this.deletedAt,
  });

  bool get isDeleted => deletedAt != null;

  Annotation copyWith({
    AnnotationType? type,
    String? color,
    Anchor? anchor,
    String? noteText,
    Map<String, dynamic>? ink,
    int? revision,
    String? deviceId,
    DateTime? updatedAt,
    DateTime? deletedAt,
  }) =>
      Annotation(
        id: id,
        bookId: bookId,
        type: type ?? this.type,
        color: color ?? this.color,
        anchor: anchor ?? this.anchor,
        noteText: noteText ?? this.noteText,
        ink: ink ?? this.ink,
        revision: revision ?? this.revision,
        deviceId: deviceId ?? this.deviceId,
        createdAt: createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
        deletedAt: deletedAt ?? this.deletedAt,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'bookId': bookId,
        'type': type.name,
        if (color != null) 'color': color,
        'anchor': anchor.toJson(),
        if (noteText != null) 'noteText': noteText,
        if (ink != null) 'ink': ink,
        'revision': revision,
        'deviceId': deviceId,
        'createdAt': createdAt.toUtc().toIso8601String(),
        'updatedAt': updatedAt.toUtc().toIso8601String(),
        if (deletedAt != null)
          'deletedAt': deletedAt!.toUtc().toIso8601String(),
      };

  factory Annotation.fromJson(Map<String, dynamic> j) => Annotation(
        id: j['id'] as String,
        bookId: j['bookId'] as String,
        type: AnnotationType.values.byName(j['type'] as String),
        color: j['color'] as String?,
        anchor: Anchor.fromJson(Map<String, dynamic>.from(j['anchor'] as Map)),
        noteText: j['noteText'] as String?,
        ink: j['ink'] == null
            ? null
            : Map<String, dynamic>.from(j['ink'] as Map),
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
      other is Annotation && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(id, revision, updatedAt, deletedAt);

  @override
  String toString() => 'Annotation($id, $type, rev=$revision, '
      'deleted=${isDeleted}, anchor=${anchor.state.name})';
}
