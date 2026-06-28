// Kiwimath ↔ KiwiReader integration — Phase 0 spike (no backend).
//
// Drops the KiwiReader Store + Library + Reader into Kiwimath. The screens
// inherit Kiwimath's existing Material 3 theme (orange seed 0xFFFF6D00 in
// main_v3.dart), so the colour scheme is shared automatically.
//
// This file wires DEV adapters (in-memory catalog/content/coins) + a sample
// book so the whole flow runs on-device with no backend. Phase 1 swaps these
// for real adapters: CoinWallet → /v1/economy/spend, CatalogProvider →
// /v3/store/catalog, ContentProvider → /v3/store/content/*, etc.
// See KIWIMATH_STORE_INTEGRATION_PLAN.md.

import 'dart:async';
import 'dart:convert';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader/kiwi_reader.dart';

import '../services/api_client.dart' show ApiClient;
import '../services/authed_http.dart' as http;

// --------------------------------------------------------------- sample data
final _sampleBook = HtmlBook(
  id: 'algebra-ch1',
  title: 'Algebra · Chapter 1',
  sections: const [
    HtmlSection(
      id: 'ch1',
      title: 'Linear Equations',
      blocks: [
        HtmlBlock(HtmlBlockType.heading, 'Solving linear equations'),
        HtmlBlock(
          HtmlBlockType.paragraph,
          'A linear equation in one variable is an equation that can be written '
          'in the form ax + b = 0, where a and b are constants and a is not zero. '
          'Its single solution is the value of x that makes both sides equal.',
        ),
        HtmlBlock(
          HtmlBlockType.paragraph,
          'To solve it, isolate the variable: move the constant to the other '
          'side, then divide by the coefficient.',
        ),
        HtmlBlock(HtmlBlockType.math, 'ax + b = 0  =>  x = -b / a'),
      ],
    ),
  ],
);

final _catalog = <CatalogBook>[
  // School-issued sample: no pricing → owned via the seeded entitlement.
  const CatalogBook(
    id: 'algebra-ch1',
    title: 'Algebra · Chapter 1',
    author: 'Kiwimath',
    format: BookFormat.html,
    contentVersion: 'v1',
    byteSize: 48000,
  ),
  const CatalogBook(
    id: 'number-theory',
    title: 'Number Theory Primer',
    author: 'Kiwimath',
    format: BookFormat.pdf,
    contentVersion: 'v1',
    byteSize: 120000,
    pricing: BookPricing(coins: 300, amountMinor: 14900, currency: 'INR'),
  ),
  const CatalogBook(
    id: 'olympiad-combi',
    title: 'Olympiad Combinatorics',
    author: 'Kiwimath',
    format: BookFormat.pdf,
    contentVersion: 'v1',
    byteSize: 90000,
    pricing: BookPricing(coins: 200),
  ),
  const CatalogBook(
    id: 'geometry-gems',
    title: 'Geometry Gems',
    author: 'Kiwimath',
    format: BookFormat.epub,
    contentVersion: 'v1',
    byteSize: 60000,
    pricing: BookPricing(amountMinor: 9900, currency: 'INR'),
  ),
  const CatalogBook(
    id: 'study-skills',
    title: 'Study Skills Starter',
    author: 'Kiwimath',
    format: BookFormat.html,
    contentVersion: 'v1',
    byteSize: 30000,
    pricing: BookPricing.free,
  ),
];

// --------------------------------------------------------------- dev adapters
class _DevCatalog implements CatalogProvider {
  @override
  Future<List<CatalogBook>> books() async {
    await Future<void>.delayed(const Duration(milliseconds: 250));
    return _catalog;
  }
}

class _DevContent implements ContentProvider {
  @override
  Future<BookManifest> manifest(String bookId) async => BookManifest(
        id: bookId,
        format: BookFormat.html,
        contentVersion: 'v1',
        sections: const [],
      );

  @override
  Future<Uri?> coverImage(String bookId) async => null;

  @override
  Future<ByteStream> bytes(String bookId, {ByteRange? range}) async {
    final book = _catalog.firstWhere((b) => b.id == bookId);
    final total = book.byteSize ?? 40000;
    const chunks = 24;
    final chunk = (total / chunks).ceil();
    return Stream.periodic(
      const Duration(milliseconds: 90),
      (_) => List<int>.filled(chunk, 0),
    ).take(chunks);
  }
}

/// Dev coin wallet (500 coins). Phase 1: implement against the real economy
/// wallet — `GET /v1/economy/wallet` + `POST /v1/economy/spend` (idempotent).
class _DevWallet implements CoinWallet {
  int _balance;
  final _changes = StreamController<int>.broadcast();
  _DevWallet(this._balance);

  @override
  Future<int> balance() async => _balance;

  @override
  Future<CoinSpendResult> spend({
    required int amount,
    required String reason,
    String? bookId,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    if (_balance < amount) return CoinSpendResult.failure(_balance, 'insufficient');
    _balance -= amount;
    _changes.add(_balance);
    return CoinSpendResult.success(_balance);
  }

  @override
  Stream<int> get balanceChanges => _changes.stream;
}

/// Dev money gateway. Phase 2: wrap App Store / Play via `in_app_purchase`.
class _DevGateway implements PurchaseGateway {
  @override
  Future<PurchaseResult> purchase(CatalogBook book) async {
    await Future<void>.delayed(const Duration(milliseconds: 700));
    return const PurchaseResult.success();
  }

  @override
  Future<List<String>> restore() async => const [];
}

/// The ProviderScope overrides that wire KiwiReader to the (dev) adapters.
/// Wrap the app root with `ProviderScope(overrides: booksOverrides(), …)`.
List<Override> booksOverrides() => [
      deviceIdProvider.overrideWithValue('kiwimath-dev'),
      localStoreProvider.overrideWithValue(InMemoryLocalStore()),
      annotationApiProvider.overrideWithValue(InMemoryAnnotationApi()),
      catalogProviderRef.overrideWithValue(_DevCatalog()),
      contentProviderRef.overrideWithValue(_DevContent()),
      contentRendererProvider.overrideWithValue(HtmlRenderer.fromBook(_sampleBook)),
      coinWalletProvider.overrideWithValue(_DevWallet(500)),
      purchaseGatewayProvider.overrideWithValue(_DevGateway()),
      entitlementStoreProvider.overrideWithValue(
        InMemoryEntitlementStore({
          'algebra-ch1': Entitlement(
            bookId: 'algebra-ch1',
            via: AcquisitionMethod.granted,
            acquiredAt: DateTime.now(),
          ),
        }),
      ),
    ];

// --------------------------------------------------- PRODUCTION adapters (Phase 1)
// Real catalog / wallet / entitlements against the Kiwimath backend. They read
// the signed-in Firebase user at call time, so they work under the root
// ProviderScope (created before sign-in). Content + sync stay synthetic until
// ingestion (Phase 1.5) and the sync backend (Phase 2); money is Phase 2.

String? get _uid => FirebaseAuth.instance.currentUser?.uid;

class _BackendCatalog implements CatalogProvider {
  @override
  Future<List<CatalogBook>> books() async {
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/catalog'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) return const [];
    final list = (jsonDecode(res.body)['books'] as List?) ?? const [];
    return list
        .map((e) => CatalogBook.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
  }
}

class _BackendWallet implements CoinWallet {
  @override
  Future<int> balance() async {
    final uid = _uid;
    if (uid == null) return 0;
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/economy/wallet?user_id=$uid'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) return 0;
    return (jsonDecode(res.body)['coins'] as num?)?.toInt() ?? 0;
  }

  @override
  Future<CoinSpendResult> spend({
    required int amount,
    required String reason,
    String? bookId,
  }) async {
    final uid = _uid;
    if (uid == null) return const CoinSpendResult.failure(0, 'no_user');
    final res = await http
        .post(
          Uri.parse('${ApiClient.baseUrl}/v3/economy/spend'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'user_id': uid,
            'currency': 'coins',
            'amount': amount,
            'sku': bookId,
            'reason': reason,
            // stable key → a retry re-confirms instead of double-charging.
            'idempotency_key': '$uid:$bookId:$reason',
          }),
        )
        .timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) {
      return CoinSpendResult.failure(await _safeBalance(), 'error');
    }
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    final bal = (j['newBalance'] as num?)?.toInt() ?? 0;
    return j['ok'] == true
        ? CoinSpendResult.success(bal)
        : CoinSpendResult.failure(bal, (j['error'] ?? 'failed').toString());
  }

  Future<int> _safeBalance() async {
    try {
      return await balance();
    } catch (_) {
      return 0;
    }
  }

  @override
  Stream<int> get balanceChanges => const Stream<int>.empty();
}

class _BackendEntitlements implements EntitlementStore {
  @override
  Future<Map<String, Entitlement>> load() async {
    final uid = _uid;
    if (uid == null) return {};
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/entitlements?user_id=$uid'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) return {};
    final ids = ((jsonDecode(res.body)['owned'] as List?) ?? const [])
        .map((e) => '$e');
    final now = DateTime.now();
    return {
      for (final id in ids)
        id: Entitlement(bookId: id, via: AcquisitionMethod.granted, acquiredAt: now),
    };
  }

  @override
  Future<void> save(Entitlement e) async {
    // Coin / purchase ownership is already recorded server-side at debit; only a
    // FREE claim needs to be pushed up so it persists.
    if (e.via != AcquisitionMethod.free) return;
    final uid = _uid;
    if (uid == null) return;
    await http
        .post(
          Uri.parse('${ApiClient.baseUrl}/v3/store/claim'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'user_id': uid, 'book_id': e.bookId}),
        )
        .timeout(const Duration(seconds: 12));
  }

  @override
  Future<void> delete(String bookId) async {}
}

/// Real book content from the backend (Phase 1.5). `manifest` + `bytes` are
/// entitlement-gated server-side — only an owner can read a book — so a
/// purchased/owned book shows the *actual* file via the EPUB/PDF renderer.
class _BackendContent implements ContentProvider {
  BookFormat _fmt(String? s) => BookFormat.values
      .firstWhere((f) => f.name == s, orElse: () => BookFormat.html);

  @override
  Future<BookManifest> manifest(String bookId) async {
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/content/$bookId/manifest'))
        .timeout(const Duration(seconds: 12));
    if (res.statusCode != 200) {
      throw StateError('manifest ${res.statusCode}');
    }
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    return BookManifest(
      id: j['id'] as String? ?? bookId,
      format: _fmt(j['format'] as String?),
      contentVersion: j['contentVersion'] as String? ?? 'v1',
      sections: const [],
      title: j['title'] as String?,
    );
  }

  @override
  Future<Uri?> coverImage(String bookId) async => null; // placeholder card for now

  @override
  Future<ByteStream> bytes(String bookId, {ByteRange? range}) async {
    // KiwiReader's EPUB/PDF renderers buffer the whole stream, so fetch the
    // full file (Range is a later optimisation) and hand back a single chunk.
    final res = await http
        .get(Uri.parse('${ApiClient.baseUrl}/v3/store/content/$bookId/bytes'))
        .timeout(const Duration(seconds: 45));
    if (res.statusCode != 200) {
      throw StateError('bytes ${res.statusCode}');
    }
    return Stream<List<int>>.value(res.bodyBytes);
  }
}

/// Production overrides: real catalog/wallet/entitlements/content. The content
/// renderer is built *per book* in `_openBook` (the global override here is just
/// a harmless default — KiwiReader reads the per-book one). main_v3 uses this.
List<Override> backendBooksOverrides() => [
      deviceIdProvider.overrideWithValue('kiwimath'),
      localStoreProvider.overrideWithValue(InMemoryLocalStore()),
      annotationApiProvider.overrideWithValue(InMemoryAnnotationApi()),
      catalogProviderRef.overrideWithValue(_BackendCatalog()),
      contentProviderRef.overrideWithValue(_BackendContent()),
      contentRendererProvider.overrideWithValue(HtmlRenderer.fromBook(_sampleBook)),
      coinWalletProvider.overrideWithValue(_BackendWallet()),
      purchaseGatewayProvider.overrideWithValue(_DevGateway()),
      entitlementStoreProvider.overrideWithValue(_BackendEntitlements()),
    ];

// --------------------------------------------------------------- screens
// KiwiReader reads `contentRendererProvider` for the open book, so we resolve
// the right renderer for *this* book's format (EPUB/PDF/HTML) from the active
// ContentProvider, then push the reader in a scope that overrides it.
Future<ContentRenderer> _rendererFor(BookManifest m, ContentProvider content) {
  switch (m.format) {
    case BookFormat.epub:
      return EpubRenderer.open(m, content);
    case BookFormat.pdf:
      return PdfRenderer.open(m, content);
    case BookFormat.html:
      // Structured-HTML ingestion is a later pass; the sample stands in.
      return Future.value(HtmlRenderer.fromBook(_sampleBook));
    case BookFormat.image:
      return Future.error(UnsupportedError('Image books are not supported yet.'));
  }
}

/// Open a book in the reader by id. The single hardened boundary to the EPUB/PDF
/// render engine: fetches the manifest, builds the right renderer, and pushes
/// KiwiReader in a scope that binds that renderer. Any failure shows a snackbar
/// instead of crashing. Public so our own Library UI can call it.
Future<void> openBookReader(BuildContext context, String bookId) async {
  final content =
      ProviderScope.containerOf(context, listen: false).read(contentProviderRef);
  showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (_) => const Center(child: CircularProgressIndicator()),
  );
  ContentRenderer renderer;
  try {
    final manifest = await content.manifest(bookId);
    renderer = await _rendererFor(manifest, content);
  } catch (_) {
    if (context.mounted) Navigator.of(context).pop(); // dismiss loader
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not open this book. Please try again.')),
      );
    }
    return;
  }
  if (!context.mounted) return;
  Navigator.of(context).pop(); // dismiss loader
  Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (_) => ProviderScope(
        overrides: [contentRendererProvider.overrideWithValue(renderer)],
        child: KiwiReader(
          bookId: bookId,
          config: const ReaderConfig(theme: ReaderTheme.light),
        ),
      ),
    ),
  );
}

// Adapter for KiwiReader's own Store/Library screens (still used by the
// BooksHubScreen/Body fallbacks); our Library UI calls openBookReader directly.
void _openBook(BuildContext context, CatalogBook book) =>
    openBookReader(context, book.id);

/// Store + Library in one screen (two tabs). Inherits Kiwimath's orange theme.
class BooksHubScreen extends StatelessWidget {
  const BooksHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Library', style: TextStyle(fontWeight: FontWeight.w800)),
          bottom: const TabBar(
            tabs: [Tab(text: 'Store'), Tab(text: 'My books')],
          ),
        ),
        body: TabBarView(
          children: [
            StoreScreen(onOpenBook: _openBook),
            LibraryScreen(onOpenBook: _openBook, ownedOnly: true),
          ],
        ),
      ),
    );
  }
}

/// Library as an embedded **tab body** — no Scaffold/AppBar, because the app
/// shell already supplies the top bar (with the wallet chips). Two sub-tabs:
/// Store and My books. Used as a first-class bottom-nav tab.
class BooksHubBody extends StatelessWidget {
  const BooksHubBody({super.key});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          Material(
            color: Theme.of(context).scaffoldBackgroundColor,
            child: TabBar(
              labelColor: cs.primary,
              indicatorColor: cs.primary,
              tabs: const [Tab(text: 'Store'), Tab(text: 'My books')],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: [
                StoreScreen(onOpenBook: _openBook),
                LibraryScreen(onOpenBook: _openBook, ownedOnly: true),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
