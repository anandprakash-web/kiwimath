/// How a book entered the user's library.
enum AcquisitionMethod {
  /// Free title, claimed at no cost.
  free,

  /// Granted by the backend (school issue, promo, admin grant).
  granted,

  /// Unlocked with the kiwiapp's virtual coins.
  coins,

  /// Bought with real money (App Store / Play / web checkout).
  purchase,
}

/// A record that the user **owns** a book. Its presence in the entitlement map
/// is what makes a book appear in the Library and become readable. Persisted so
/// ownership survives restarts and offline use; the backend remains the source
/// of truth and is reconciled on `restore()`.
class Entitlement {
  final String bookId;
  final AcquisitionMethod via;
  final DateTime acquiredAt;

  const Entitlement({
    required this.bookId,
    required this.via,
    required this.acquiredAt,
  });

  Map<String, dynamic> toJson() => {
        'bookId': bookId,
        'via': via.name,
        'acquiredAt': acquiredAt.toUtc().toIso8601String(),
      };

  factory Entitlement.fromJson(Map<String, dynamic> j) => Entitlement(
        bookId: j['bookId'] as String,
        via: AcquisitionMethod.values.byName(j['via'] as String),
        acquiredAt: DateTime.parse(j['acquiredAt'] as String),
      );

  @override
  bool operator ==(Object other) =>
      other is Entitlement &&
      other.bookId == bookId &&
      other.via == via &&
      other.acquiredAt.toUtc() == acquiredAt.toUtc();

  @override
  int get hashCode => Object.hash(bookId, via, acquiredAt.toUtc());
}

/// Transient state of an in-progress acquisition (drives the Store button /
/// sheet). Distinct from [Entitlement], which is the durable ownership record.
enum AcquisitionState {
  /// Nothing happening (also where a cancelled purchase returns to).
  idle,

  /// Talking to the wallet / billing.
  processing,

  /// Acquired — the book is now owned.
  owned,

  /// Failed; [AcquisitionStatus.error] explains why (e.g. not enough coins).
  failed,
}

class AcquisitionStatus {
  final String bookId;
  final AcquisitionState state;
  final String? error;

  const AcquisitionStatus({
    required this.bookId,
    this.state = AcquisitionState.idle,
    this.error,
  });

  factory AcquisitionStatus.initial(String bookId) =>
      AcquisitionStatus(bookId: bookId);

  bool get isBusy => state == AcquisitionState.processing;

  @override
  bool operator ==(Object other) =>
      other is AcquisitionStatus &&
      other.bookId == bookId &&
      other.state == state &&
      other.error == error;

  @override
  int get hashCode => Object.hash(bookId, state, error);
}
