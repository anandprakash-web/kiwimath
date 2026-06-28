/// KiwiReader — Flutter reader + annotation module for kiwimaths.
///
/// Public API: embed [KiwiReader], implement [ContentProvider] + [AuthProvider]
/// in the host, and override the dependency providers in a `ProviderScope`.
library kiwi_reader;

// Re-export the pure-Dart core so hosts get models/anchoring/sync in one import.
export 'package:kiwi_reader_core/kiwi_reader_core.dart';

export 'src/config/reader_config.dart';
export 'src/content/html_content.dart';
export 'src/data/sqlite_local_store.dart';
export 'src/data/file_offline_book_store.dart';
export 'src/data/file_entitlement_store.dart';
export 'src/data/offline_first_content_provider.dart';
export 'src/events/reader_event.dart';
export 'src/host/providers.dart';
export 'src/rendering/content_renderer.dart';
export 'src/rendering/html_renderer.dart';
export 'src/rendering/pdf_renderer.dart';
export 'src/rendering/epub_renderer.dart';
export 'src/state/reader_controllers.dart';
export 'src/state/reader_providers.dart';
export 'src/state/library_providers.dart';
export 'src/state/store_providers.dart';
export 'src/state/connectivity_plus_source.dart';
export 'src/presentation/book_cover.dart';
export 'src/presentation/html_reader_surface.dart';
export 'src/presentation/pdf_reader_surface.dart';
export 'src/presentation/epub_reader_surface.dart';
export 'src/presentation/selection_toolbar.dart';
export 'src/presentation/note_editor.dart';
export 'src/presentation/annotations_list.dart';
export 'src/presentation/library_screen.dart';
export 'src/presentation/store_screen.dart';
export 'src/presentation/kiwi_reader_widget.dart';
