import '../library/catalog_book.dart';

enum PurchaseOutcome {
  /// Payment captured and verified.
  success,

  /// User dismissed the payment sheet — not an error.
  cancelled,

  /// Declined, network error, verification failed, etc.
  failed,
}

class PurchaseResult {
  final PurchaseOutcome outcome;
  final String? error;

  const PurchaseResult(this.outcome, {this.error});

  const PurchaseResult.success() : this(PurchaseOutcome.success);
  const PurchaseResult.cancelled() : this(PurchaseOutcome.cancelled);
  const PurchaseResult.failed(String error)
      : this(PurchaseOutcome.failed, error: error);

  bool get isSuccess => outcome == PurchaseOutcome.success;
}

/// HOST SEAM — **real-money** purchases.
///
/// The host wraps its billing provider here. On mobile, purchases of digital
/// books must go through **App Store / Play in-app purchase** (e.g. the
/// `in_app_purchase` plugin); on web the host may use Stripe/PG. KiwiReader only
/// records the resulting entitlement — it never sees card data or receipts.
///
/// [restore] re-checks the billing provider / backend for already-bought books
/// (new device, reinstall) and returns their ids.
abstract class PurchaseGateway {
  Future<PurchaseResult> purchase(CatalogBook book);
  Future<List<String>> restore();
}
