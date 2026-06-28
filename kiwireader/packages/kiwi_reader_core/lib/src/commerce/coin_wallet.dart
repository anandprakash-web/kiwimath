/// Result of spending coins.
class CoinSpendResult {
  final bool ok;

  /// The balance after the attempt (unchanged on failure).
  final int balance;

  /// Why it failed (e.g. `insufficient`, `network`), null on success.
  final String? error;

  const CoinSpendResult({required this.ok, required this.balance, this.error});

  const CoinSpendResult.success(this.balance)
      : ok = true,
        error = null;

  const CoinSpendResult.failure(this.balance, this.error) : ok = false;
}

/// HOST SEAM — the kiwiapp's **coin system**.
///
/// The coins were built elsewhere in kiwiapp; KiwiReader never owns the balance
/// or the ledger. It only asks this seam to read the balance and to spend coins
/// to unlock a book. The host implements it against its existing wallet
/// (local + backend), where the real debit, idempotency and fraud checks live.
///
/// [spend] must be **atomic and authoritative**: deduct on the server, and
/// return `ok: false` (without deducting) when the balance is insufficient or
/// the call fails. KiwiReader treats a non-`ok` result as "not unlocked".
///
/// [spend] should also be **idempotent on `(bookId, reason)`**: if the app
/// crashes after a successful debit but before the entitlement is recorded, a
/// retry must re-confirm the same unlock rather than charge again. Pair this
/// with a backend that marks the book owned on debit, so the next launch
/// reconciles ownership even if the local write was lost.
abstract class CoinWallet {
  Future<int> balance();

  Future<CoinSpendResult> spend({
    required int amount,
    required String reason,
    String? bookId,
  });

  /// Optional live balance (e.g. coins earned elsewhere in the app). Defaults to
  /// empty; the `StoreController` also refreshes the balance around a spend.
  Stream<int> get balanceChanges => Stream<int>.empty();
}
