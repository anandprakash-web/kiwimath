import 'dart:async';

import '../library/catalog_book.dart';
import 'coin_wallet.dart';
import 'entitlement.dart';
import 'entitlement_store.dart';
import 'purchase_gateway.dart';

/// Orchestrates **acquisition**: turning a Store book into an owned library
/// book, either by spending coins or paying money — plus restore and balance
/// tracking.
///
/// Pure Dart and fully unit-tested. The money path ([PurchaseGateway]) and the
/// coin path ([CoinWallet]) are host seams, so the whole decision logic —
/// ownership checks, insufficient-coins handling, declined payments, no
/// double-charging — is verified with fakes, no billing SDK or Flutter
/// required. Either seam may be null when the app supports only one path.
class StoreController {
  StoreController({
    required EntitlementStore store,
    CoinWallet? wallet,
    PurchaseGateway? gateway,
  })  : _store = store,
        _wallet = wallet,
        _gateway = gateway;

  final EntitlementStore _store;
  final CoinWallet? _wallet;
  final PurchaseGateway? _gateway;

  final Map<String, Entitlement> _entitlements = {};
  final Map<String, AcquisitionStatus> _acq = {};
  int _balance = 0;
  StreamSubscription<int>? _balanceSub;

  final StreamController<void> _changes = StreamController<void>.broadcast();

  /// Ticks on any change (ownership, acquisition status, or balance). UI
  /// providers watch this and re-read the getters below.
  Stream<void> get changes => _changes.stream;

  bool get supportsCoins => _wallet != null;
  bool get supportsPurchase => _gateway != null;

  Map<String, Entitlement> get entitlements =>
      Map<String, Entitlement>.unmodifiable(_entitlements);

  bool isOwned(String bookId) => _entitlements.containsKey(bookId);

  int get coinBalance => _balance;

  AcquisitionStatus statusOf(String bookId) =>
      _acq[bookId] ?? AcquisitionStatus.initial(bookId);

  /// Load owned books and the current coin balance; subscribe to live balance.
  Future<void> init() async {
    _entitlements
      ..clear()
      ..addAll(await _store.load());
    final wallet = _wallet;
    if (wallet != null) {
      _balance = await wallet.balance();
      _balanceSub = wallet.balanceChanges.listen((b) {
        _balance = b;
        _tick();
      });
    }
    _tick();
  }

  /// Claim a free book (no payment).
  Future<void> claimFree(CatalogBook book) async {
    if (isOwned(book.id)) return _setStatus(book.id, AcquisitionState.owned);
    // Guard against a double-tap / two widgets: don't start a second spend or
    // charge while one is already in flight.
    if (statusOf(book.id).state == AcquisitionState.processing) return;
    if (!(book.pricing?.isFree ?? false)) {
      return _setStatus(book.id, AcquisitionState.failed, 'This book is not free.');
    }
    await _grant(book.id, AcquisitionMethod.free);
  }

  /// Unlock a book with coins. Checks ownership and balance first, then asks the
  /// wallet to spend; only records ownership if the spend actually succeeds.
  Future<void> unlockWithCoins(CatalogBook book) async {
    if (isOwned(book.id)) return _setStatus(book.id, AcquisitionState.owned);
    // Guard against a double-tap / two widgets: don't start a second spend or
    // charge while one is already in flight.
    if (statusOf(book.id).state == AcquisitionState.processing) return;

    final price = book.pricing?.coins ?? 0;
    if (!(book.pricing?.payableWithCoins ?? false) || price <= 0) {
      return _setStatus(
          book.id, AcquisitionState.failed, "This book can't be unlocked with coins.");
    }
    final wallet = _wallet;
    if (wallet == null) {
      return _setStatus(
          book.id, AcquisitionState.failed, 'Coins are not available.');
    }

    _setStatus(book.id, AcquisitionState.processing);

    // Refresh the balance so we fail fast (and keep the UI honest) before
    // attempting an authoritative spend.
    _balance = await wallet.balance();
    _tick();
    if (_balance < price) {
      return _setStatus(book.id, AcquisitionState.failed,
          'Not enough coins — you have $_balance, this book costs $price.');
    }

    final result = await wallet.spend(
      amount: price,
      reason: 'unlock_book',
      bookId: book.id,
    );
    _balance = result.balance;
    _tick();
    if (!result.ok) {
      return _setStatus(book.id, AcquisitionState.failed,
          result.error ?? 'Could not spend coins. Please try again.');
    }
    await _grant(book.id, AcquisitionMethod.coins);
  }

  /// Buy a book with real money via the host [PurchaseGateway].
  Future<void> purchase(CatalogBook book) async {
    if (isOwned(book.id)) return _setStatus(book.id, AcquisitionState.owned);
    // Guard against a double-tap / two widgets: don't start a second spend or
    // charge while one is already in flight.
    if (statusOf(book.id).state == AcquisitionState.processing) return;

    if (!(book.pricing?.payableWithMoney ?? false)) {
      return _setStatus(book.id, AcquisitionState.failed,
          'This book is not available for purchase.');
    }
    final gateway = _gateway;
    if (gateway == null) {
      return _setStatus(
          book.id, AcquisitionState.failed, 'Purchasing is not available.');
    }

    _setStatus(book.id, AcquisitionState.processing);
    final result = await gateway.purchase(book);
    switch (result.outcome) {
      case PurchaseOutcome.success:
        await _grant(book.id, AcquisitionMethod.purchase);
      case PurchaseOutcome.cancelled:
        _setStatus(book.id, AcquisitionState.idle); // user backed out
      case PurchaseOutcome.failed:
        _setStatus(book.id, AcquisitionState.failed,
            result.error ?? 'Purchase failed. You were not charged.');
    }
  }

  /// Reconcile previously-bought books from the billing provider / backend
  /// (new device, reinstall). Idempotent.
  Future<void> restore() async {
    final gateway = _gateway;
    if (gateway == null) return;
    final ids = await gateway.restore();
    for (final id in ids) {
      if (!isOwned(id)) await _grant(id, AcquisitionMethod.purchase);
    }
  }

  Future<void> _grant(String bookId, AcquisitionMethod via) async {
    // Idempotent: never overwrite an existing entitlement, so a restore() or a
    // retried grant can't change acquiredAt/via or double-record.
    if (_entitlements.containsKey(bookId)) {
      _setStatus(bookId, AcquisitionState.owned);
      return;
    }
    final e = Entitlement(bookId: bookId, via: via, acquiredAt: DateTime.now());
    // Own in-memory FIRST so a paid-for book is never lost if the local cache
    // write fails — the backend is the source of truth and is reconciled via
    // restore() / catalog ownership on the next launch.
    _entitlements[bookId] = e;
    _setStatus(bookId, AcquisitionState.owned);
    try {
      await _store.save(e);
    } catch (_) {
      // Cache write failed (disk full, etc.); ownership stands for this session.
    }
  }

  void _setStatus(String bookId, AcquisitionState state, [String? error]) {
    _acq[bookId] = AcquisitionStatus(bookId: bookId, state: state, error: error);
    _tick();
  }

  void _tick() {
    if (!_changes.isClosed) _changes.add(null);
  }

  Future<void> dispose() async {
    await _balanceSub?.cancel();
    await _changes.close();
  }
}
