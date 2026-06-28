import '../util/equality.dart';
import 'locator.dart';

/// Per-user, per-book reading position. Resolves cross-device with simple
/// last-write-wins by [updatedAt]; [deviceId] lets the UI say "continue on
/// this device?" when positions diverge.
class ReadingProgress {
  final String bookId;
  final Locator locator;
  final double percent; // 0..1
  final String deviceId;
  final DateTime updatedAt;

  const ReadingProgress({
    required this.bookId,
    required this.locator,
    required this.percent,
    required this.deviceId,
    required this.updatedAt,
  });

  Map<String, dynamic> toJson() => {
        'bookId': bookId,
        'locator': locator.toJson(),
        'percent': percent,
        'deviceId': deviceId,
        'updatedAt': updatedAt.toUtc().toIso8601String(),
      };

  factory ReadingProgress.fromJson(Map<String, dynamic> j) => ReadingProgress(
        bookId: j['bookId'] as String,
        locator:
            Locator.fromJson(Map<String, dynamic>.from(j['locator'] as Map)),
        percent: (j['percent'] as num).toDouble(),
        deviceId: j['deviceId'] as String,
        updatedAt: DateTime.parse(j['updatedAt'] as String),
      );

  @override
  bool operator ==(Object other) =>
      other is ReadingProgress && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode => Object.hash(bookId, percent, updatedAt);
}
