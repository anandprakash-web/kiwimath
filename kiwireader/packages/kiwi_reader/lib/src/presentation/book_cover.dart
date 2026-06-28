import 'package:flutter/material.dart';
import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// Shared cover art for a catalog book: the network cover when available, else a
/// branded gradient placeholder showing the title initials. Used by both the
/// Library grid and the Store grid.
class BookCover extends StatelessWidget {
  final CatalogBook book;
  final double radius;
  const BookCover({super.key, required this.book, this.radius = 8});

  @override
  Widget build(BuildContext context) {
    final url = book.coverUrl;
    if (url != null && url.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: Image.network(
          url,
          fit: BoxFit.cover,
          width: double.infinity,
          errorBuilder: (_, __, ___) => _placeholder(),
          loadingBuilder: (ctx, child, progress) =>
              progress == null ? child : _placeholder(),
        ),
      );
    }
    return _placeholder();
  }

  Widget _placeholder() {
    final words = book.title.trim().split(RegExp(r'\s+'));
    final initials = words.isEmpty || words.first.isEmpty
        ? '?'
        : words.take(2).map((w) => w[0]).join().toUpperCase();
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFA726), Color(0xFFE65100)], // Kiwimath orange
        ),
        boxShadow: const [
          BoxShadow(
              color: Color(0x33000000), blurRadius: 8, offset: Offset(0, 4)),
        ],
      ),
      alignment: Alignment.center,
      padding: const EdgeInsets.all(10),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(initials,
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w800)),
          const SizedBox(height: 6),
          Text(
            book.title,
            maxLines: 3,
            textAlign: TextAlign.center,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
                color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}
