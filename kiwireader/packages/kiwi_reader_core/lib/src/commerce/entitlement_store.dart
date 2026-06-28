import 'entitlement.dart';

/// Persistence seam for [Entitlement]s (which books the user owns). Mirrors the
/// other store seams: an on-device implementation persists to disk; the
/// unit-tested [InMemoryEntitlementStore] is the reference. The backend stays
/// the source of truth and is reconciled via `StoreController.restore()`.
abstract class EntitlementStore {
  Future<Map<String, Entitlement>> load();
  Future<void> save(Entitlement entitlement);
  Future<void> delete(String bookId);
}

class InMemoryEntitlementStore implements EntitlementStore {
  final Map<String, Entitlement> _items;

  InMemoryEntitlementStore([Map<String, Entitlement>? seed])
      : _items = {...?seed};

  @override
  Future<Map<String, Entitlement>> load() async =>
      Map<String, Entitlement>.from(_items);

  @override
  Future<void> save(Entitlement entitlement) async =>
      _items[entitlement.bookId] = entitlement;

  @override
  Future<void> delete(String bookId) async => _items.remove(bookId);
}
