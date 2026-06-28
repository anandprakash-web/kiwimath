import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

CatalogBook priced(
  String id, {
  int? coins,
  int? money,
  String currency = 'INR',
  bool free = false,
}) =>
    CatalogBook(
      id: id,
      title: id.toUpperCase(),
      format: BookFormat.pdf,
      contentVersion: 'v1',
      pricing: BookPricing(
        isFree: free,
        coins: coins,
        amountMinor: money,
        currency: money == null ? null : currency,
      ),
    );

class FakeWallet implements CoinWallet {
  int bal;
  bool spendOk;
  String? spendError;
  int spendCalls = 0;
  final List<int> spends = [];

  FakeWallet(this.bal, {this.spendOk = true, this.spendError});

  @override
  Future<int> balance() async => bal;

  @override
  Future<CoinSpendResult> spend({
    required int amount,
    required String reason,
    String? bookId,
  }) async {
    spendCalls++;
    if (!spendOk) return CoinSpendResult.failure(bal, spendError ?? 'declined');
    bal -= amount;
    spends.add(amount);
    return CoinSpendResult.success(bal);
  }

  @override
  Stream<int> get balanceChanges => Stream<int>.empty();
}

class FakeGateway implements PurchaseGateway {
  PurchaseResult result;
  List<String> restoreIds;
  int purchaseCalls = 0;

  FakeGateway(this.result, {this.restoreIds = const []});

  @override
  Future<PurchaseResult> purchase(CatalogBook book) async {
    purchaseCalls++;
    return result;
  }

  @override
  Future<List<String>> restore() async => restoreIds;
}

/// An entitlement store whose save() always fails (e.g. disk full).
class ThrowingEntitlementStore implements EntitlementStore {
  @override
  Future<Map<String, Entitlement>> load() async => {};
  @override
  Future<void> save(Entitlement entitlement) async =>
      throw Exception('disk full');
  @override
  Future<void> delete(String bookId) async {}
}

void main() {
  test('unlock with coins: debits the wallet and grants ownership', () async {
    final wallet = FakeWallet(500);
    final store = InMemoryEntitlementStore();
    final c = StoreController(store: store, wallet: wallet);
    await c.init();
    expect(c.coinBalance, 500);

    await c.unlockWithCoins(priced('a', coins: 120));

    expect(c.isOwned('a'), isTrue);
    expect(c.statusOf('a').state, AcquisitionState.owned);
    expect(c.coinBalance, 380);
    expect(wallet.spends, [120]);
    expect((await store.load()).containsKey('a'), isTrue);
    expect(c.entitlements['a']!.via, AcquisitionMethod.coins);
    await c.dispose();
  });

  test('insufficient coins: fails, no spend, not owned', () async {
    final wallet = FakeWallet(50);
    final c = StoreController(store: InMemoryEntitlementStore(), wallet: wallet);
    await c.init();

    await c.unlockWithCoins(priced('a', coins: 120));

    expect(c.isOwned('a'), isFalse);
    expect(c.statusOf('a').state, AcquisitionState.failed);
    expect(c.statusOf('a').error, contains('Not enough coins'));
    expect(wallet.spendCalls, 0); // never attempted the spend
    expect(c.coinBalance, 50);
    await c.dispose();
  });

  test('wallet declines the spend: fails and stays unowned', () async {
    final wallet = FakeWallet(500, spendOk: false, spendError: 'wallet locked');
    final c = StoreController(store: InMemoryEntitlementStore(), wallet: wallet);
    await c.init();

    await c.unlockWithCoins(priced('a', coins: 120));

    expect(c.isOwned('a'), isFalse);
    expect(c.statusOf('a').state, AcquisitionState.failed);
    expect(c.statusOf('a').error, contains('wallet locked'));
    expect(wallet.spendCalls, 1);
    await c.dispose();
  });

  test('coins path rejects a book with no coin price', () async {
    final c = StoreController(
        store: InMemoryEntitlementStore(), wallet: FakeWallet(999));
    await c.init();
    await c.unlockWithCoins(priced('a', money: 14900)); // money-only
    expect(c.isOwned('a'), isFalse);
    expect(c.statusOf('a').state, AcquisitionState.failed);
    await c.dispose();
  });

  test('purchase success grants ownership via money', () async {
    final gateway = FakeGateway(const PurchaseResult.success());
    final store = InMemoryEntitlementStore();
    final c = StoreController(store: store, gateway: gateway);
    await c.init();

    await c.purchase(priced('a', money: 14900));

    expect(c.isOwned('a'), isTrue);
    expect(c.entitlements['a']!.via, AcquisitionMethod.purchase);
    expect(gateway.purchaseCalls, 1);
    await c.dispose();
  });

  test('purchase cancelled: returns to idle, not owned, no error', () async {
    final c = StoreController(
      store: InMemoryEntitlementStore(),
      gateway: FakeGateway(const PurchaseResult.cancelled()),
    );
    await c.init();

    await c.purchase(priced('a', money: 14900));

    expect(c.isOwned('a'), isFalse);
    expect(c.statusOf('a').state, AcquisitionState.idle);
    expect(c.statusOf('a').error, isNull);
    await c.dispose();
  });

  test('purchase failed: surfaces the error, not owned', () async {
    final c = StoreController(
      store: InMemoryEntitlementStore(),
      gateway: FakeGateway(const PurchaseResult.failed('card declined')),
    );
    await c.init();

    await c.purchase(priced('a', money: 14900));

    expect(c.isOwned('a'), isFalse);
    expect(c.statusOf('a').state, AcquisitionState.failed);
    expect(c.statusOf('a').error, contains('card declined'));
    await c.dispose();
  });

  test('already owned: no double charge on either path', () async {
    final wallet = FakeWallet(500);
    final gateway = FakeGateway(const PurchaseResult.success());
    final c = StoreController(
        store: InMemoryEntitlementStore(), wallet: wallet, gateway: gateway);
    await c.init();
    final book = priced('a', coins: 120, money: 14900);

    await c.unlockWithCoins(book); // first acquisition
    expect(c.coinBalance, 380);

    await c.unlockWithCoins(book); // again with coins
    await c.purchase(book); // and with money

    expect(wallet.spendCalls, 1); // not spent twice
    expect(gateway.purchaseCalls, 0); // never charged
    expect(c.coinBalance, 380);
    await c.dispose();
  });

  test('free book is claimed at no cost', () async {
    final wallet = FakeWallet(0);
    final c = StoreController(store: InMemoryEntitlementStore(), wallet: wallet);
    await c.init();

    await c.claimFree(priced('a', free: true));

    expect(c.isOwned('a'), isTrue);
    expect(c.entitlements['a']!.via, AcquisitionMethod.free);
    expect(wallet.spendCalls, 0);
    await c.dispose();
  });

  test('restore reconciles previously-purchased books', () async {
    final c = StoreController(
      store: InMemoryEntitlementStore(),
      gateway: FakeGateway(const PurchaseResult.cancelled(),
          restoreIds: ['x', 'y']),
    );
    await c.init();

    await c.restore();

    expect(c.isOwned('x'), isTrue);
    expect(c.isOwned('y'), isTrue);
    await c.dispose();
  });

  test('init restores persisted ownership and the coin balance', () async {
    final store = InMemoryEntitlementStore({
      'owned-book': Entitlement(
        bookId: 'owned-book',
        via: AcquisitionMethod.purchase,
        acquiredAt: DateTime.utc(2026, 1, 1),
      ),
    });
    final c = StoreController(store: store, wallet: FakeWallet(275));
    await c.init();

    expect(c.isOwned('owned-book'), isTrue);
    expect(c.coinBalance, 275);
    await c.dispose();
  });

  test('models JSON round-trip (pricing, entitlement)', () {
    final book = priced('a', coins: 120, money: 14900);
    expect(CatalogBook.fromJson(book.toJson()), book);
    expect(BookPricing.fromJson(book.pricing!.toJson()), book.pricing);
    final e = Entitlement(
        bookId: 'a',
        via: AcquisitionMethod.coins,
        acquiredAt: DateTime.utc(2026, 6, 1));
    expect(Entitlement.fromJson(e.toJson()), e);
  });

  test('money label formats minor units', () {
    expect(const BookPricing(amountMinor: 14900, currency: 'INR').moneyLabel,
        '₹149');
    expect(const BookPricing(amountMinor: 499, currency: 'USD').moneyLabel,
        r'$4.99');
  });

  test('concurrent double-tap unlocks once (no double spend)', () async {
    final wallet = FakeWallet(500);
    final c = StoreController(store: InMemoryEntitlementStore(), wallet: wallet);
    await c.init();
    final book = priced('a', coins: 120);

    await Future.wait([c.unlockWithCoins(book), c.unlockWithCoins(book)]);

    expect(wallet.spendCalls, 1); // the in-flight guard blocked the second
    expect(c.isOwned('a'), isTrue);
    expect(c.coinBalance, 380);
    await c.dispose();
  });

  test('restore does not overwrite an existing entitlement (idempotent)',
      () async {
    final store = InMemoryEntitlementStore({
      'a': Entitlement(
        bookId: 'a',
        via: AcquisitionMethod.coins,
        acquiredAt: DateTime.utc(2025, 1, 1),
      ),
    });
    final c = StoreController(
      store: store,
      gateway: FakeGateway(const PurchaseResult.cancelled(), restoreIds: ['a']),
    );
    await c.init();

    await c.restore();

    expect(c.entitlements['a']!.via, AcquisitionMethod.coins); // unchanged
    await c.dispose();
  });

  test('a failed local cache write still grants the book this session',
      () async {
    final c = StoreController(
        store: ThrowingEntitlementStore(), wallet: FakeWallet(500));
    await c.init();

    await c.unlockWithCoins(priced('a', coins: 100));

    expect(c.isOwned('a'), isTrue); // money was spent -> ownership must stand
    await c.dispose();
  });
}
