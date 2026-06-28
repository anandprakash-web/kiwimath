import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// === Store / commerce wiring =============================================
/// The Store sells the same backend catalog the Library lists. Three host
/// seams feed the pure-Dart `StoreController`:
///   • `coinWalletProvider`     — the kiwiapp's coin system (null => no coins),
///   • `purchaseGatewayProvider`— real-money billing (null => no purchases),
///   • `entitlementStoreProvider` — where ownership is cached.
/// All UI binds to change-driven providers below.

/// Override with the kiwiapp's coin wallet. `null` disables the coin path.
final coinWalletProvider = Provider<CoinWallet?>((ref) => null);

/// Override with the host's IAP / Stripe gateway. `null` disables purchases.
final purchaseGatewayProvider = Provider<PurchaseGateway?>((ref) => null);

/// Ownership cache. In-memory for dev; on device override with a persistent
/// implementation (and reconcile with the backend via `restore()`).
final entitlementStoreProvider =
    Provider<EntitlementStore>((ref) => InMemoryEntitlementStore());

/// The single app-wide store controller. Restores entitlements + balance.
final storeControllerProvider = Provider<StoreController>((ref) {
  final controller = StoreController(
    store: ref.watch(entitlementStoreProvider),
    wallet: ref.watch(coinWalletProvider),
    gateway: ref.watch(purchaseGatewayProvider),
  );
  unawaited(controller.init());
  ref.onDispose(controller.dispose);
  return controller;
});

/// Ticks on any ownership / balance / acquisition-status change.
final storeChangesProvider = StreamProvider<void>((ref) {
  final controller = ref.watch(storeControllerProvider);
  final out = StreamController<void>();
  out.add(null);
  final sub = controller.changes.listen((_) => out.add(null));
  ref.onDispose(() {
    sub.cancel();
    out.close();
  });
  return out.stream;
});

/// Owned books (bookId -> entitlement). The Library binds to this in owned mode.
final entitlementsProvider = Provider<Map<String, Entitlement>>((ref) {
  ref.watch(storeChangesProvider);
  return ref.watch(storeControllerProvider).entitlements;
});

/// Current coin balance (for the balance chip / acquire sheet).
final coinBalanceProvider = Provider<int>((ref) {
  ref.watch(storeChangesProvider);
  return ref.watch(storeControllerProvider).coinBalance;
});

final isOwnedProvider = Provider.family<bool, String>((ref, bookId) {
  ref.watch(storeChangesProvider);
  return ref.watch(storeControllerProvider).isOwned(bookId);
});

final acquisitionStatusProvider =
    Provider.family<AcquisitionStatus, String>((ref, bookId) {
  ref.watch(storeChangesProvider);
  return ref.watch(storeControllerProvider).statusOf(bookId);
});
