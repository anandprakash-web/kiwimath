import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader/kiwi_reader.dart';

/// Sample book in the Phase-0 custom HTML/JSON format (the open book renders
/// this regardless of which catalog book was tapped — demo simplification).
final _sampleBook = HtmlBook(
  id: 'calc-ch3',
  title: 'Calculus · Chapter 3',
  sections: const [
    HtmlSection(
      id: 'ch3',
      title: 'Derivatives',
      blocks: [
        HtmlBlock(HtmlBlockType.heading, 'What is a derivative?'),
        HtmlBlock(
          HtmlBlockType.paragraph,
          'In calculus, the derivative measures the instantaneous rate of change '
          'of a quantity with respect to another. It is one of the two central '
          'ideas of calculus, the other being the integral.',
        ),
        HtmlBlock(
          HtmlBlockType.paragraph,
          'Geometrically, the derivative at a point is the slope of the tangent '
          'line to the curve at that point, found by taking a limit as the '
          'interval shrinks to zero.',
        ),
        HtmlBlock(
          HtmlBlockType.math,
          "f'(x) = lim (h->0) [ f(x+h) - f(x) ] / h",
        ),
      ],
    ),
  ],
);

/// The demo store catalog — uploaded on the "backend". Mix of pricing:
/// free / school-issued (no pricing) / coins / money / both.
final _catalog = <CatalogBook>[
  // School-issued sample: no pricing -> owned via the seeded entitlement.
  const CatalogBook(
    id: 'calc-ch3',
    title: 'Calculus · Chapter 3',
    author: 'kiwimaths',
    format: BookFormat.html,
    contentVersion: 'v1',
    byteSize: 48000,
  ),
  const CatalogBook(
    id: 'organic-chem',
    title: 'Essential Organic Chemistry',
    author: 'P. Y. Bruice',
    format: BookFormat.pdf,
    contentVersion: 'v1',
    byteSize: 120000,
    pricing: BookPricing(coins: 300, amountMinor: 14900, currency: 'INR'),
  ),
  const CatalogBook(
    id: 'physics-200',
    title: '200 Physics Problems',
    author: 'Gnädig',
    format: BookFormat.pdf,
    contentVersion: 'v1',
    byteSize: 90000,
    pricing: BookPricing(coins: 200), // coins only
  ),
  const CatalogBook(
    id: 'trig',
    title: 'Trigonometry Essentials',
    author: 'kiwimaths',
    format: BookFormat.epub,
    contentVersion: 'v1',
    byteSize: 60000,
    pricing: BookPricing(amountMinor: 9900, currency: 'INR'), // money only
  ),
  const CatalogBook(
    id: 'study-skills',
    title: 'Study Skills Starter',
    author: 'kiwimaths',
    format: BookFormat.html,
    contentVersion: 'v1',
    byteSize: 30000,
    pricing: BookPricing.free,
  ),
];

class _DemoCatalog implements CatalogProvider {
  @override
  Future<List<CatalogBook>> books() async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    return _catalog;
  }
}

/// Synthesises bytes so downloads visibly progress.
class _DemoContent implements ContentProvider {
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
      const Duration(milliseconds: 100),
      (_) => List<int>.filled(chunk, 0),
    ).take(chunks);
  }
}

/// Demo coin wallet (the kiwiapp's coin system would implement this).
class _DemoWallet implements CoinWallet {
  int _balance;
  final _changes = StreamController<int>.broadcast();
  _DemoWallet(this._balance);

  @override
  Future<int> balance() async => _balance;

  @override
  Future<CoinSpendResult> spend({
    required int amount,
    required String reason,
    String? bookId,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 500));
    if (_balance < amount) {
      return CoinSpendResult.failure(_balance, 'insufficient');
    }
    _balance -= amount;
    _changes.add(_balance);
    return CoinSpendResult.success(_balance);
  }

  @override
  Stream<int> get balanceChanges => _changes.stream;
}

/// Demo money gateway — a real host wraps App Store / Play / Stripe here.
class _DemoGateway implements PurchaseGateway {
  @override
  Future<PurchaseResult> purchase(CatalogBook book) async {
    await Future<void>.delayed(const Duration(milliseconds: 800));
    return const PurchaseResult.success();
  }

  @override
  Future<List<String>> restore() async => const [];
}

void main() {
  runApp(
    ProviderScope(
      overrides: [
        deviceIdProvider.overrideWithValue('demo-device'),
        localStoreProvider.overrideWithValue(InMemoryLocalStore()),
        annotationApiProvider.overrideWithValue(InMemoryAnnotationApi()),
        // Library + content.
        catalogProviderRef.overrideWithValue(_DemoCatalog()),
        contentProviderRef.overrideWithValue(_DemoContent()),
        contentRendererProvider.overrideWithValue(
          HtmlRenderer.fromBook(_sampleBook),
        ),
        // Store: a coin wallet (500 coins), a money gateway, and a seeded
        // entitlement for the school-issued sample so it starts in the Library.
        coinWalletProvider.overrideWithValue(_DemoWallet(500)),
        purchaseGatewayProvider.overrideWithValue(_DemoGateway()),
        entitlementStoreProvider.overrideWithValue(
          InMemoryEntitlementStore({
            'calc-ch3': Entitlement(
              bookId: 'calc-ch3',
              via: AcquisitionMethod.granted,
              acquiredAt: DateTime.now(),
            ),
          }),
        ),
      ],
      child: const _DemoApp(),
    ),
  );
}

class _DemoApp extends StatelessWidget {
  const _DemoApp();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KiwiReader Demo',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF16A34A),
        useMaterial3: true,
      ),
      home: const _Shell(),
    );
  }
}

void _openBook(BuildContext context, CatalogBook book) {
  Navigator.of(context).push(
    MaterialPageRoute<void>(
      builder: (_) => KiwiReader(
        bookId: book.id,
        config: const ReaderConfig(theme: ReaderTheme.sepia),
      ),
    ),
  );
}

/// Bottom-nav shell: Store (buy / unlock with coins) + Library (owned books).
class _Shell extends StatefulWidget {
  const _Shell();
  @override
  State<_Shell> createState() => _ShellState();
}

class _ShellState extends State<_Shell> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _tab,
        children: [
          StoreScreen(onOpenBook: _openBook),
          LibraryScreen(onOpenBook: _openBook, ownedOnly: true),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.storefront_outlined),
              selectedIcon: Icon(Icons.storefront),
              label: 'Store'),
          NavigationDestination(
              icon: Icon(Icons.menu_book_outlined),
              selectedIcon: Icon(Icons.menu_book),
              label: 'Library'),
        ],
      ),
    );
  }
}
