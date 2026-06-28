import 'package:kiwi_reader_core/kiwi_reader_core.dart';

/// One stream the host can log / react to. Mirrors the design's event surface.
sealed class ReaderEvent {
  const ReaderEvent();
}

class BookOpened extends ReaderEvent {
  final String bookId;
  final BookFormat format;
  final bool fromCache;
  const BookOpened(this.bookId, this.format, {this.fromCache = false});
}

class ProgressChanged extends ReaderEvent {
  final double percent;
  final Locator locator;
  const ProgressChanged(this.percent, this.locator);
}

class AnnotationCreated extends ReaderEvent {
  final String id;
  final AnnotationType type;
  final String? color;
  const AnnotationCreated(this.id, this.type, {this.color});
}

class AnnotationUpdated extends ReaderEvent {
  final String id;
  const AnnotationUpdated(this.id);
}

class AnnotationDeleted extends ReaderEvent {
  final String id;
  const AnnotationDeleted(this.id);
}

class BookmarkToggled extends ReaderEvent {
  final String id;
  final bool on;
  const BookmarkToggled(this.id, this.on);
}

/// "Ask about this" — host decides what to do (e.g. open the assistant).
class SelectionRequestedAI extends ReaderEvent {
  final String text;
  const SelectionRequestedAI(this.text);
}

/// Phase 3 cross-link: jump from a highlight to a quiz on the same concept.
class JumpToQuizRequested extends ReaderEvent {
  final String conceptTag;
  const JumpToQuizRequested(this.conceptTag);
}

enum SyncState { idle, syncing, offline, error }

class SyncStateChanged extends ReaderEvent {
  final SyncState state;
  const SyncStateChanged(this.state);
}

class AnchorOrphaned extends ReaderEvent {
  final int count;
  const AnchorOrphaned(this.count);
}

class ReaderError extends ReaderEvent {
  final String code;
  final bool recoverable;
  const ReaderError(this.code, {this.recoverable = true});
}
