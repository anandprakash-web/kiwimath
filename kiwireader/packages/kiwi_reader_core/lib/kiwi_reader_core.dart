/// KiwiReader core — pure-Dart domain layer.
///
/// Models, the layered (W3C-style) anchor resolver, the re-publish reconciler,
/// and the offline-first sync engine. No Flutter dependency.
library kiwi_reader_core;

// Models
export 'src/models/enums.dart';
export 'src/models/selectors.dart';
export 'src/models/anchor.dart';
export 'src/models/annotation.dart';
export 'src/models/locator.dart';
export 'src/models/bookmark.dart';
export 'src/models/reading_progress.dart';
export 'src/models/book_manifest.dart';

// Anchoring
export 'src/anchoring/text_normalizer.dart';
export 'src/anchoring/section_content.dart';
export 'src/anchoring/quote_matcher.dart';
export 'src/anchoring/anchor_resolver.dart';
export 'src/anchoring/anchor_factory.dart';
export 'src/anchoring/offset_map.dart';
export 'src/anchoring/pdf_anchor.dart';
export 'src/anchoring/reconciler.dart';

// Sync
export 'src/sync/sync_models.dart';
export 'src/sync/merge.dart';
export 'src/sync/annotation_api.dart';
export 'src/sync/in_memory_api.dart';
export 'src/sync/sync_engine.dart';
export 'src/sync/connectivity.dart';
export 'src/sync/sync_scheduler.dart';

// Store
export 'src/store/local_store.dart';

// Library (catalog + offline downloads)
export 'src/library/catalog_book.dart';
export 'src/library/download_status.dart';
export 'src/library/offline_book_store.dart';
export 'src/library/download_manager.dart';

// Commerce (store: pricing, entitlements, coins + purchases)
export 'src/commerce/pricing.dart';
export 'src/commerce/entitlement.dart';
export 'src/commerce/coin_wallet.dart';
export 'src/commerce/purchase_gateway.dart';
export 'src/commerce/entitlement_store.dart';
export 'src/commerce/store_controller.dart';

// Export
export 'src/export/annotation_exporter.dart';

// Util
export 'src/util/equality.dart';
