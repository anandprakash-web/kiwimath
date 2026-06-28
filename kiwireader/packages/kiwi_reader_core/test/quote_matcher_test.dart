import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

void main() {
  group('QuoteMatcher', () {
    const text = 'the cat sat. the cat ran. a dog slept.';

    test('findAll returns every exact occurrence', () {
      final hits =
          QuoteMatcher(text).findAll(const TextQuoteSelector(exact: 'the cat'));
      expect(hits.length, 2);
    });

    test('prefix/suffix context narrows to one occurrence', () {
      final hits = QuoteMatcher(text)
          .findAll(const TextQuoteSelector(exact: 'the cat', suffix: ' ran'));
      expect(hits.length, 1);
      expect(hits.first.start, text.indexOf('the cat ran'));
    });

    test('fuzzy finds a near match above threshold', () {
      final span = QuoteMatcher(text).findFuzzy('the cot sat', threshold: 0.7);
      expect(span, isNotNull);
      expect(text.substring(span!.start, span.end), contains('cat'));
    });

    test('fuzzy returns null when nothing is close enough', () {
      final span =
          QuoteMatcher(text).findFuzzy('xylophone quartz', threshold: 0.82);
      expect(span, isNull);
    });
  });
}
