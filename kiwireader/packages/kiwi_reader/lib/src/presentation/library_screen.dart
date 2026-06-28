import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

import '../state/library_providers.dart';
import '../state/store_providers.dart';
import 'book_cover.dart';

const Color _kGreen = Color(0xFFFF6F00); // Kiwimath brand orange (matches app theme)

/// The **Library tab**: a grid of the backend catalog's books, each showing its
/// offline download state. Lists and downloads only — books are uploaded /
/// ingested on the backend, so there is no upload surface here.
///
/// [onOpenBook] fires when the user opens a book; the host pushes the
/// `KiwiReader` widget for `book.id`. Downloaded books open offline; others
/// stream through the host `ContentProvider`.
class LibraryScreen extends ConsumerStatefulWidget {
  final void Function(BuildContext context, CatalogBook book) onOpenBook;
  final String title;

  /// When true, show only books the user owns (entitlements) — use this when
  /// the app also has a Store. Default false shows the whole catalog.
  final bool ownedOnly;

  const LibraryScreen({
    super.key,
    required this.onOpenBook,
    this.title = 'Library',
    this.ownedOnly = false,
  });

  @override
  ConsumerState<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends ConsumerState<LibraryScreen> {
  String _query = '';
  bool _downloadedOnly = false;

  DownloadManager get _manager => ref.read(downloadManagerProvider);

  @override
  Widget build(BuildContext context) {
    final catalog = ref.watch(libraryCatalogProvider);
    final statuses = ref.watch(downloadStatusesProvider).valueOrNull ??
        const <String, DownloadStatus>{};
    final ownedIds =
        widget.ownedOnly ? ref.watch(entitlementsProvider).keys.toSet() : null;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: _kGreen,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Column(
        children: [
          _SearchAndFilter(
            downloadedOnly: _downloadedOnly,
            onQuery: (q) => setState(() => _query = q),
            onFilter: (v) => setState(() => _downloadedOnly = v),
          ),
          Expanded(
            child: catalog.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator(color: _kGreen)),
              error: (e, _) => _ErrorView(
                message: '$e',
                onRetry: () => ref.invalidate(libraryCatalogProvider),
              ),
              data: (books) {
                final filtered = _applyFilters(books, statuses, ownedIds);
                if (filtered.isEmpty) {
                  return _EmptyView(
                    downloadedOnly: _downloadedOnly,
                    ownedMode: widget.ownedOnly,
                  );
                }
                return RefreshIndicator(
                  color: _kGreen,
                  onRefresh: () =>
                      ref.refresh(libraryCatalogProvider.future),
                  child: GridView.builder(
                    padding: const EdgeInsets.fromLTRB(14, 12, 14, 28),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      mainAxisSpacing: 18,
                      crossAxisSpacing: 16,
                      childAspectRatio: 0.56,
                    ),
                    itemCount: filtered.length,
                    itemBuilder: (context, i) {
                      final b = filtered[i];
                      final st = statuses[b.id] ?? DownloadStatus.initial(b.id);
                      return BookCard(
                        book: b,
                        status: st,
                        onOpen: () => widget.onOpenBook(context, b),
                        onBadgeTap: () => _primaryAction(b, st),
                        onLongPress: () => _showActions(b, st),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  List<CatalogBook> _applyFilters(
    List<CatalogBook> books,
    Map<String, DownloadStatus> statuses,
    Set<String>? ownedIds,
  ) {
    final q = _query.trim().toLowerCase();
    return books.where((b) {
      if (ownedIds != null && !ownedIds.contains(b.id)) return false;
      final matchesQuery = q.isEmpty ||
          b.title.toLowerCase().contains(q) ||
          (b.author?.toLowerCase().contains(q) ?? false);
      final st = statuses[b.id] ?? DownloadStatus.initial(b.id);
      final matchesFilter = !_downloadedOnly || st.isAvailableOffline;
      return matchesQuery && matchesFilter;
    }).toList();
  }

  /// The badge's tap behaviour, driven by current state.
  void _primaryAction(CatalogBook b, DownloadStatus st) {
    switch (st.state) {
      case DownloadState.notDownloaded:
      case DownloadState.paused:
      case DownloadState.failed:
        _manager.download(b);
      case DownloadState.queued:
      case DownloadState.downloading:
        _manager.pause(b.id);
      case DownloadState.downloaded:
        widget.onOpenBook(context, b);
    }
  }

  Future<void> _showActions(CatalogBook b, DownloadStatus st) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.menu_book_outlined),
              title: Text(b.title,
                  maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: b.author == null ? null : Text(b.author!),
            ),
            const Divider(height: 1),
            ListTile(
              leading: const Icon(Icons.chrome_reader_mode_outlined),
              title: const Text('Open'),
              onTap: () {
                Navigator.pop(ctx);
                widget.onOpenBook(context, b);
              },
            ),
            if (!st.isAvailableOffline && !st.isActive)
              ListTile(
                leading: const Icon(Icons.download_outlined),
                title: Text(st.state == DownloadState.failed
                    ? 'Retry download'
                    : 'Download for offline'),
                onTap: () {
                  Navigator.pop(ctx);
                  _manager.download(b);
                },
              ),
            if (st.isActive)
              ListTile(
                leading: const Icon(Icons.pause_circle_outline),
                title: const Text('Pause download'),
                onTap: () {
                  Navigator.pop(ctx);
                  _manager.pause(b.id);
                },
              ),
            if (st.isAvailableOffline)
              ListTile(
                leading: const Icon(Icons.delete_outline, color: Colors.red),
                title: const Text('Remove from device',
                    style: TextStyle(color: Colors.red)),
                onTap: () {
                  Navigator.pop(ctx);
                  _manager.remove(b.id);
                },
              ),
          ],
        ),
      ),
    );
  }
}

/// Search field + All / Downloaded segmented filter.
class _SearchAndFilter extends StatelessWidget {
  final bool downloadedOnly;
  final ValueChanged<String> onQuery;
  final ValueChanged<bool> onFilter;

  const _SearchAndFilter({
    required this.downloadedOnly,
    required this.onQuery,
    required this.onFilter,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 4),
      child: Column(
        children: [
          TextField(
            onChanged: onQuery,
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: 'Search your library',
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
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: SegmentedButton<bool>(
              showSelectedIcon: false,
              style: ButtonStyle(
                visualDensity: VisualDensity.compact,
                backgroundColor: WidgetStateProperty.resolveWith(
                  (s) => s.contains(WidgetState.selected) ? _kGreen : null,
                ),
                foregroundColor: WidgetStateProperty.resolveWith(
                  (s) =>
                      s.contains(WidgetState.selected) ? Colors.white : null,
                ),
              ),
              segments: const [
                ButtonSegment(value: false, label: Text('All')),
                ButtonSegment(value: true, label: Text('Downloaded')),
              ],
              selected: {downloadedOnly},
              onSelectionChanged: (s) => onFilter(s.first),
            ),
          ),
        ],
      ),
    );
  }
}

/// A single book in the grid: cover + offline-state badge + title/author.
class BookCard extends StatelessWidget {
  final CatalogBook book;
  final DownloadStatus status;
  final VoidCallback onOpen;
  final VoidCallback onBadgeTap;
  final VoidCallback onLongPress;

  const BookCard({
    super.key,
    required this.book,
    required this.status,
    required this.onOpen,
    required this.onBadgeTap,
    required this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onOpen,
      onLongPress: onLongPress,
      behavior: HitTestBehavior.opaque,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Stack(
              children: [
                Positioned.fill(child: BookCover(book: book)),
                Positioned(
                  right: 6,
                  bottom: 6,
                  child: DownloadBadge(status: status, onTap: onBadgeTap),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            book.title,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
                fontWeight: FontWeight.w600, fontSize: 13, height: 1.2),
          ),
          if (book.author != null)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                book.author!,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 11, color: Colors.black54),
              ),
            ),
        ],
      ),
    );
  }
}

/// The circular offline-state badge overlaid on a cover.
class DownloadBadge extends StatelessWidget {
  final DownloadStatus status;
  final VoidCallback onTap;
  const DownloadBadge({super.key, required this.status, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: _content(),
      ),
    );
  }

  Widget _content() {
    switch (status.state) {
      case DownloadState.downloaded:
        return _circle(_kGreen, const Icon(Icons.check, size: 16, color: Colors.white));
      case DownloadState.downloading:
        return _circle(
          Colors.white,
          SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(
              strokeWidth: 2.5,
              value: status.progress, // null => indeterminate
              color: _kGreen,
            ),
          ),
        );
      case DownloadState.queued:
        return _circle(Colors.white,
            const Icon(Icons.schedule, size: 15, color: Color(0xFF5B6B62)));
      case DownloadState.failed:
        return _circle(Colors.white,
            const Icon(Icons.refresh, size: 16, color: Colors.red));
      case DownloadState.paused:
        return _circle(Colors.white,
            const Icon(Icons.download_outlined, size: 16, color: Color(0xFF5B6B62)));
      case DownloadState.notDownloaded:
        return _circle(Colors.white,
            const Icon(Icons.download_outlined, size: 16, color: Color(0xFF5B6B62)));
    }
  }

  Widget _circle(Color bg, Widget child) => Container(
        width: 30,
        height: 30,
        decoration: BoxDecoration(
          color: bg,
          shape: BoxShape.circle,
          border: bg == Colors.white
              ? Border.all(color: const Color(0xFFCFD9D3))
              : null,
          boxShadow: const [
            BoxShadow(
                color: Color(0x40000000), blurRadius: 4, offset: Offset(0, 2)),
          ],
        ),
        alignment: Alignment.center,
        child: child,
      );
}

class _EmptyView extends StatelessWidget {
  final bool downloadedOnly;
  final bool ownedMode;
  const _EmptyView({required this.downloadedOnly, this.ownedMode = false});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              downloadedOnly
                  ? Icons.cloud_download_outlined
                  : Icons.menu_book_outlined,
              size: 48,
              color: Colors.black26,
            ),
            const SizedBox(height: 12),
            Text(
              downloadedOnly
                  ? 'No downloaded books yet.\nDownload a book to read it offline.'
                  : ownedMode
                      ? 'No books in your library yet.\nVisit the Store to get books.'
                      : 'No books in your library yet.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 44, color: Colors.redAccent),
            const SizedBox(height: 12),
            Text("Couldn't load your library.\n$message",
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Try again')),
          ],
        ),
      ),
    );
  }
}
