import '../util/equality.dart';

/// A logical reading position, format-agnostic. [raw] holds the format-native
/// detail (CFI string, PDF page, DOM path); [progress] is a 0..1 fraction used
/// for the progress bar and cross-device "continue reading".
class Locator {
  final String sectionId;
  final double? progress;
  final Map<String, dynamic> raw;

  const Locator({required this.sectionId, this.progress, this.raw = const {}});

  Locator copyWith(
          {String? sectionId, double? progress, Map<String, dynamic>? raw}) =>
      Locator(
        sectionId: sectionId ?? this.sectionId,
        progress: progress ?? this.progress,
        raw: raw ?? this.raw,
      );

  Map<String, dynamic> toJson() => {
        'sectionId': sectionId,
        if (progress != null) 'progress': progress,
        if (raw.isNotEmpty) 'raw': raw,
      };

  factory Locator.fromJson(Map<String, dynamic> j) => Locator(
        sectionId: j['sectionId'] as String,
        progress: (j['progress'] as num?)?.toDouble(),
        raw: j['raw'] == null
            ? const {}
            : Map<String, dynamic>.from(j['raw'] as Map),
      );

  @override
  bool operator ==(Object other) =>
      other is Locator && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(sectionId, progress);
}
