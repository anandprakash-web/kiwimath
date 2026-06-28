import '../models/annotation.dart';
import '../models/enums.dart';
import 'anchor_resolver.dart';
import 'section_content.dart';

/// Tally produced when re-anchoring after a content version bump.
class ReconcileReport {
  final int resolved;
  final int repaired;
  final int approx;
  final int orphaned;

  const ReconcileReport({
    this.resolved = 0,
    this.repaired = 0,
    this.approx = 0,
    this.orphaned = 0,
  });

  int get total => resolved + repaired + approx + orphaned;

  /// What the "N notes need a quick look" prompt counts.
  int get needsReview => approx + orphaned;

  @override
  String toString() =>
      'ReconcileReport(resolved=$resolved, repaired=$repaired, '
      'approx=$approx, orphaned=$orphaned, needsReview=$needsReview)';
}

/// Re-resolves a set of annotations against new content — the "book was
/// re-published" branch. Returns the updated annotations (with refreshed
/// anchor states) and a [ReconcileReport].
class Reconciler {
  final AnchorResolver resolver;
  const Reconciler(this.resolver);

  (List<Annotation>, ReconcileReport) reconcile(
    List<Annotation> annotations,
    SectionContent Function(String sectionId) sectionLookup,
  ) {
    var resolved = 0, repaired = 0, approx = 0, orphaned = 0;
    final out = <Annotation>[];
    for (final a in annotations) {
      if (a.isDeleted) {
        out.add(a);
        continue;
      }
      final result =
          resolver.resolve(a.anchor, sectionLookup(a.anchor.sectionId));
      switch (result.state) {
        case AnchorState.resolved:
          resolved++;
        case AnchorState.repaired:
          repaired++;
        case AnchorState.approx:
          approx++;
        case AnchorState.orphaned:
          orphaned++;
      }
      out.add(a.copyWith(anchor: result.anchor));
    }
    return (
      out,
      ReconcileReport(
          resolved: resolved,
          repaired: repaired,
          approx: approx,
          orphaned: orphaned),
    );
  }
}
