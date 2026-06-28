import 'dart:convert';
import 'dart:io';

import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// On-device [EntitlementStore]: owned-book records persisted to a JSON file, so
/// purchases/unlocks survive restarts and are available offline. Parity with
/// `FileOfflineBookStore`; the unit-tested `InMemoryEntitlementStore` is the
/// reference. The backend stays the source of truth — call
/// `StoreController.restore()` on launch / sign-in to reconcile.
///
/// ```dart
/// final path = '${(await getApplicationSupportDirectory()).path}/kiwi_entitlements.json';
/// final store = await FileEntitlementStore.open(path);
/// // entitlementStoreProvider.overrideWithValue(store)
/// ```
class FileEntitlementStore implements EntitlementStore {
  final File _file;
  final Map<String, Entitlement> _items;

  FileEntitlementStore._(this._file, this._items);

  static Future<FileEntitlementStore> open(String path) async {
    final file = File(path);
    final items = <String, Entitlement>{};
    if (await file.exists()) {
      final raw = jsonDecode(await file.readAsString());
      if (raw is Map) {
        raw.forEach((k, v) {
          items[k as String] =
              Entitlement.fromJson(Map<String, dynamic>.from(v as Map));
        });
      }
    } else {
      await file.parent.create(recursive: true);
    }
    return FileEntitlementStore._(file, items);
  }

  Future<void> _flush() async {
    final map = {for (final e in _items.entries) e.key: e.value.toJson()};
    await _file.writeAsString(jsonEncode(map));
  }

  @override
  Future<Map<String, Entitlement>> load() async =>
      Map<String, Entitlement>.from(_items);

  @override
  Future<void> save(Entitlement entitlement) async {
    _items[entitlement.bookId] = entitlement;
    await _flush();
  }

  @override
  Future<void> delete(String bookId) async {
    _items.remove(bookId);
    await _flush();
  }
}
