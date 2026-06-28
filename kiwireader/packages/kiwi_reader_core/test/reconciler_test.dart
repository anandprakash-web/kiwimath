import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

import 'helpers.dart';

void main() {
  test('reconcile tallies anchor states across a re-publish', () {
    const resolver = AnchorResolver();
    const reconciler = Reconciler(resolver);

    final annotations = [
      ann(
          id: 'ok',
          anchor: const Anchor(
              sectionId: 'ch1', quote: TextQuoteSelector(exact: 'alpha'))),
      ann(
          id: 'gone',
          anchor: const Anchor(
              sectionId: 'ch1',
              quote: TextQuoteSelector(exact: 'zzz-missing'))),
      // "beta gama" is one deletion away from "beta gamma" -> fuzzy/approx.
      ann(
          id: 'fuzz',
          anchor: const Anchor(
              sectionId: 'ch1', quote: TextQuoteSelector(exact: 'beta gama'))),
      ann(id: 'del', deleted: t(1)),
    ];

    SectionContent lookup(String s) =>
        SectionContent(sectionId: s, text: 'alpha beta gamma delta epsilon');

    final (out, report) = reconciler.reconcile(annotations, lookup);

    expect(
        report.repaired + report.resolved, greaterThanOrEqualTo(1)); // 'alpha'
    expect(report.orphaned, 1); // 'gone'
    expect(report.approx, 1); // 'beta gama'
    expect(report.needsReview, report.approx + report.orphaned);
    expect(out.length, 4); // deleted one is passed through untouched
    expect(out.firstWhere((a) => a.id == 'gone').anchor.state,
        AnchorState.orphaned);
  });
}
