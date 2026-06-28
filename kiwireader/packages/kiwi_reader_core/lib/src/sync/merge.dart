import '../models/annotation.dart';

/// Field-level conflict resolution for two versions of the same annotation id.
///
/// Rules (design §Sync):
///   * A tombstone (`deletedAt`) ALWAYS beats a concurrent edit — even a newer
///     one. (A recoverable trash window handles the UX of accidental deletes.)
///   * Otherwise last-write-wins by `updatedAt`, with `deviceId` as a
///     deterministic tiebreaker when timestamps are identical.
///   * Notes are special: if both sides hold different non-empty note text,
///     KEEP BOTH so a student's writing is never silently lost.
class Merge {
  static Annotation resolve(Annotation a, Annotation b) {
    // 1) Tombstone wins outright.
    if (a.isDeleted && !b.isDeleted) return a;
    if (b.isDeleted && !a.isDeleted) return b;
    if (a.isDeleted && b.isDeleted) {
      return a.deletedAt!.isAfter(b.deletedAt!) ? a : b;
    }

    // 2) Both alive -> newer wins.
    final winner = _newer(a, b);
    final loser = identical(winner, a) ? b : a;
    final maxRev = a.revision > b.revision ? a.revision : b.revision;

    // 3) Note keep-both.
    final wn = winner.noteText, ln = loser.noteText;
    final bothNotes = (wn?.isNotEmpty ?? false) && (ln?.isNotEmpty ?? false);
    if (bothNotes && wn != ln) {
      return winner.copyWith(
        noteText: '$wn\n\n— also —\n$ln',
        revision: maxRev + 1,
      );
    }
    return winner.copyWith(revision: maxRev);
  }

  static Annotation _newer(Annotation a, Annotation b) {
    final cmp = a.updatedAt.compareTo(b.updatedAt);
    if (cmp != 0) return cmp > 0 ? a : b;
    // Deterministic tiebreak on identical timestamps.
    return a.deviceId.compareTo(b.deviceId) >= 0 ? a : b;
  }
}
