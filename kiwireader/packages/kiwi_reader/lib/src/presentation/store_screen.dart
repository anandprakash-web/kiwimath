import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../state/library_providers.dart';
import '../state/store_providers.dart';
import 'book_cover.dart';

const Color _kGreen = Color(0xFFFF6F00); // Kiwimath brand orange (matches app theme)
const Color _kCoin = Color(0xFFB45309); // amber-700, for coin pricing
const Color _kInk = Color(0xFF13211A);

/// The **Store tab**: the backend catalog with prices. A student can **buy**
/// with money or **unlock with coins** (the kiwiapp's virtual currency). Owned
/// books show "In Library" and open in the reader; acquiring a book moves it to
/// the Library.
class StoreScreen extends ConsumerStatefulWidget {
  final void Function(BuildContext context, CatalogBook book) onOpenBook;
  final String title;

  const StoreScreen({
    super.key,
    required this.onOpenBook,
    this.title = 'Store',
  });

  @override
  ConsumerState<StoreScreen> createState() => _StoreScreenState();
}

class _StoreScreenState extends ConsumerState<StoreScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final catalog = ref.watch(libraryCatalogProvider);
    final entitlements = ref.watch(entitlementsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: _kGreen,
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          if (ref.watch(storeControllerProvider).supportsPurchase)
            IconButton(
              tooltip: 'Restore purchases',
              icon: const Icon(Icons.restore),
              onPressed: _restore,
            ),
          if (ref.watch(storeControllerProvider).supportsCoins)
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Center(child: CoinBalanceChip()),
            ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 8),
            child: TextField(
              onChanged: (q) => setState(() => _query = q),
              decoration: InputDecoration(
                hintText: 'Search the store',
                prefixIcon: const Icon(Icons.search),
                isDense: true,
                filled: true,
                fillColor: const Color(0xFFF1F5F3),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          Expanded(
            child: catalog.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator(color: _kGreen)),
              error: (e, _) => _Centered('Couldn\'t load the store.\n$e'),
              data: (books) {
                final list = _filter(books);
                if (list.isEmpty) return const _Centered('No books found.');
                return GridView.builder(
                  padding: const EdgeInsets.fromLTRB(14, 8, 14, 28),
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    mainAxisSpacing: 18,
                    crossAxisSpacing: 16,
                    childAspectRatio: 0.52,
                  ),
                  itemCount: list.length,
                  itemBuilder: (context, i) {
                    final b = list[i];
                    return _StoreCard(
                      book: b,
                      owned: entitlements.containsKey(b.id),
                      onTap: () => _onTap(b, entitlements.containsKey(b.id)),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  List<CatalogBook> _filter(List<CatalogBook> books) {
    final q = _query.trim().toLowerCase();
    if (q.isEmpty) return books;
    return books
        .where((b) =>
            b.title.toLowerCase().contains(q) ||
            (b.author?.toLowerCase().contains(q) ?? false))
        .toList();
  }

  void _onTap(CatalogBook book, bool owned) {
    if (owned) {
      widget.onOpenBook(context, book);
    } else {
      showAcquireSheet(context, book, widget.onOpenBook);
    }
  }

  Future<void> _restore() async {
    final messenger = ScaffoldMessenger.of(context);
    messenger.showSnackBar(
      const SnackBar(content: Text('Restoring your purchases…')),
    );
    await ref.read(storeControllerProvider).restore();
    if (!mounted) return;
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        const SnackBar(content: Text('Your purchases are up to date.')),
      );
  }
}

/// Coin balance pill, e.g. `🪙 380`.
class CoinBalanceChip extends ConsumerWidget {
  const CoinBalanceChip({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balance = ref.watch(coinBalanceProvider);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.18),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('🪙', style: TextStyle(fontSize: 13)),
          const SizedBox(width: 5),
          Text('$balance',
              style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 13)),
        ],
      ),
    );
  }
}

class _StoreCard extends StatelessWidget {
  final CatalogBook book;
  final bool owned;
  final VoidCallback onTap;
  const _StoreCard(
      {required this.book, required this.owned, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: BookCover(book: book)),
          const SizedBox(height: 8),
          Text(book.title,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                  fontWeight: FontWeight.w600, fontSize: 13, height: 1.2)),
          if (book.author != null)
            Text(book.author!,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 11, color: Colors.black54)),
          const SizedBox(height: 6),
          _pricePill(),
        ],
      ),
    );
  }

  Widget _pricePill() {
    if (owned) return _pill('✓ In Library', _kGreen, Colors.white);
    final p = book.pricing;
    if (p == null || p.isFree) return _pill('Get', _kGreen, Colors.white);
    if (p.payableWithCoins) {
      return _pill('🪙 ${p.coins}', const Color(0xFFFEF3C7), _kCoin);
    }
    if (p.payableWithMoney) {
      return _pill(p.moneyLabel ?? 'Buy', _kInk, Colors.white);
    }
    return _pill('—', const Color(0xFFE6ECE8), Colors.black54);
  }

  Widget _pill(String label, Color bg, Color fg) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
        decoration:
            BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
        child: Text(label,
            style: TextStyle(
                color: fg, fontWeight: FontWeight.w700, fontSize: 12)),
      );
}

class _Centered extends StatelessWidget {
  final String message;
  const _Centered(this.message);
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Text(message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.black54)),
        ),
      );
}

/// Opens the acquire sheet for [book]. Lets the student buy with money and/or
/// unlock with coins, shows live state, and offers "Read now" once owned.
Future<void> showAcquireSheet(
  BuildContext context,
  CatalogBook book,
  void Function(BuildContext, CatalogBook) onOpenBook,
) {
  return showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    isScrollControlled: true,
    builder: (ctx) => _AcquireSheet(book: book, onOpenBook: onOpenBook),
  );
}

class _AcquireSheet extends ConsumerWidget {
  final CatalogBook book;
  final void Function(BuildContext, CatalogBook) onOpenBook;
  const _AcquireSheet({required this.book, required this.onOpenBook});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final controller = ref.watch(storeControllerProvider);
    final owned = ref.watch(isOwnedProvider(book.id));
    final status = ref.watch(acquisitionStatusProvider(book.id));
    final balance = ref.watch(coinBalanceProvider);
    final p = book.pricing;

    final coins = p?.coins ?? 0;
    final canCoins = (p?.payableWithCoins ?? false) && controller.supportsCoins;
    final enoughCoins = balance >= coins;
    final canMoney =
        (p?.payableWithMoney ?? false) && controller.supportsPurchase;
    final isFree = p?.isFree ?? false;
    final busy = status.isBusy;

    return Padding(
      padding: EdgeInsets.fromLTRB(
          18, 4, 18, 18 + MediaQuery.of(context).viewInsets.bottom),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                  width: 56,
                  height: 75,
                  child: BookCover(book: book, radius: 6)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(book.title,
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 15)),
                    if (book.author != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(book.author!,
                            style: const TextStyle(
                                fontSize: 12, color: Colors.black54)),
                      ),
                    if (canCoins)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Text('Your balance: 🪙 $balance',
                            style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: enoughCoins ? _kCoin : Colors.redAccent)),
                      ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),

          if (owned) ...[
            const _OwnedBanner(),
            const SizedBox(height: 12),
            FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: _kGreen),
              onPressed: () {
                Navigator.pop(context);
                onOpenBook(context, book);
              },
              icon: const Icon(Icons.chrome_reader_mode_outlined),
              label: const Text('Read now'),
            ),
          ] else ...[
            if (isFree)
              _ActionButton(
                label: 'Get for free',
                filled: true,
                busy: busy,
                onPressed: () => controller.claimFree(book),
              ),
            if (canMoney)
              _ActionButton(
                label: 'Buy ${p!.moneyLabel}',
                filled: true,
                busy: busy,
                onPressed: () => controller.purchase(book),
              ),
            if (canMoney && canCoins)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8),
                child: Center(
                    child: Text('or',
                        style: TextStyle(color: Colors.black45, fontSize: 12))),
              ),
            if (canCoins)
              _ActionButton(
                label: enoughCoins
                    ? 'Unlock for 🪙 $coins'
                    : 'Need 🪙 ${coins - balance} more',
                filled: !canMoney,
                tonal: canMoney,
                busy: busy,
                onPressed: enoughCoins
                    ? () => controller.unlockWithCoins(book)
                    : null,
              ),
            if (!isFree && !canMoney && !canCoins)
              const Text('This book is not available right now.',
                  style: TextStyle(color: Colors.black54)),
            if (status.state == AcquisitionState.failed &&
                status.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(status.error!,
                    style: const TextStyle(
                        color: Colors.redAccent,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w500)),
              ),
            const SizedBox(height: 4),
            const _SafetyNote(),
          ],
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final bool filled;
  final bool tonal;
  final bool busy;
  final VoidCallback? onPressed;
  const _ActionButton({
    required this.label,
    required this.busy,
    this.filled = false,
    this.tonal = false,
    this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    final child = busy
        ? const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2.5))
        : Text(label);
    final onTap = busy ? null : onPressed;
    final button = filled
        ? FilledButton(
            style: FilledButton.styleFrom(backgroundColor: _kGreen),
            onPressed: onTap,
            child: child,
          )
        : tonal
            ? FilledButton.tonal(onPressed: onTap, child: child)
            : OutlinedButton(onPressed: onTap, child: child);
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: SizedBox(height: 46, child: button),
    );
  }
}

class _OwnedBanner extends StatelessWidget {
  const _OwnedBanner();
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xFFDCFCE7),
          borderRadius: BorderRadius.circular(10),
        ),
        child: const Row(
          children: [
            Icon(Icons.check_circle, color: _kGreen, size: 18),
            SizedBox(width: 8),
            Expanded(
                child: Text('In your library — find it under Library to download.',
                    style: TextStyle(
                        color: Color(0xFF166534),
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600))),
          ],
        ),
      );
}

class _SafetyNote extends StatelessWidget {
  const _SafetyNote();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.only(top: 10),
        child: Text(
          'Purchases are processed by your app store. Coins are earned and spent in kiwiapp.',
          style: TextStyle(fontSize: 10.5, color: Colors.black38),
        ),
      );
}
