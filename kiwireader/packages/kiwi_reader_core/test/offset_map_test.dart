import 'package:kiwi_reader_core/kiwi_reader_core.dart';
import 'package:test/test.dart';

void main() {
  group('OffsetMap', () {
    test('canonical equals the shared normalizer (consistency)', () {
      const messy =
          '  In   calculus,\n\tthe derivative   measures\n the rate.  ';
      final m = OffsetMap.build(messy);
      expect(m.canonical, TextNormalizer.normalize(messy));
      expect(m.isConsistent, isTrue);
      expect(m.canonical, 'In calculus, the derivative measures the rate.');
    });

    test('display->canonical->display round-trips on a word', () {
      const display = 'Line one.\n\nLine two has the WORD here.\n';
      final m = OffsetMap.build(display);
      final cStart = m.canonical.indexOf('WORD');
      final cEnd = cStart + 'WORD'.length;
      final (dStart, dEnd) = m.toDisplayRange(cStart, cEnd);
      expect(display.substring(dStart, dEnd), 'WORD');
      // and back again
      final (c2s, c2e) = m.toCanonicalRange(dStart, dEnd);
      expect(m.canonical.substring(c2s, c2e), 'WORD');
    });

    test('a selection made in DISPLAY space maps to the right canonical text',
        () {
      const display = 'alpha\n   beta   gamma\ndelta';
      final m = OffsetMap.build(display);
      // user drags across "beta   gamma" in the displayed (multi-space) text
      final dStart = display.indexOf('beta');
      final dEnd = display.indexOf('gamma') + 'gamma'.length;
      final (cStart, cEnd) = m.toCanonicalRange(dStart, dEnd);
      // canonical collapses the run, so the canonical slice is single-spaced
      expect(m.canonical.substring(cStart, cEnd), 'beta gamma');
    });

    test('leading/trailing whitespace is trimmed in canonical', () {
      final m = OffsetMap.build('\n\n   hello world   \n');
      expect(m.canonical, 'hello world');
      // canonical 0 maps to the first visible glyph in display
      expect(m.display[m.toDisplay(0)], 'h');
      // end maps to display length
      expect(m.toDisplay(m.length), m.display.length);
    });

    test('empty / whitespace-only display yields empty canonical', () {
      final m = OffsetMap.build('   \n\t  ');
      expect(m.canonical, isEmpty);
      expect(m.toDisplay(0), 0);
      expect(m.toCanonical(3), 0);
    });
  });
}
