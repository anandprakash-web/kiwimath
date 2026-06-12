// Kiwimath smoke tests.
//
// The full app (KiwimathApp) needs Firebase initialization, so these tests
// cover pure pieces instead: the KiwiTier grade-tier logic and the
// OptionCard answer widget — no network, no Firebase.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kiwimath_app/theme/kiwi_theme.dart';
import 'package:kiwimath_app/widgets/option_card.dart';

void main() {
  group('KiwiTier.forGrade', () {
    test('grades 1-2 resolve to the junior tier', () {
      expect(KiwiTier.forGrade(1).isJunior, isTrue);
      expect(KiwiTier.forGrade(2).isJunior, isTrue);
    });

    test('grades 3-6 resolve to the senior tier', () {
      expect(KiwiTier.forGrade(3).isSenior, isTrue);
      expect(KiwiTier.forGrade(4).isSenior, isTrue);
      expect(KiwiTier.forGrade(5).isSenior, isTrue);
      expect(KiwiTier.forGrade(6).isSenior, isTrue);
    });

    test('junior tier uses bigger, rounder typography than senior', () {
      final junior = KiwiTier.forGrade(1);
      final senior = KiwiTier.forGrade(5);
      expect(junior.typography.headlineSize,
          greaterThan(senior.typography.headlineSize));
      expect(junior.shape.cardRadius, greaterThan(senior.shape.cardRadius));
    });
  });

  group('OptionCard', () {
    testWidgets('renders its text and fires onTap when idle', (tester) async {
      var tapped = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OptionCard(
              text: '42',
              index: 0,
              state: OptionState.idle,
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      expect(find.text('42'), findsOneWidget);
      await tester.tap(find.byType(OptionCard));
      await tester.pumpAndSettle();
      expect(tapped, isTrue);
    });

    testWidgets('shows a check icon when marked correct and ignores taps',
        (tester) async {
      var tapped = false;
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OptionCard(
              text: '7',
              index: 1,
              state: OptionState.selectedCorrect,
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.check_circle), findsOneWidget);
      await tester.tap(find.byType(OptionCard), warnIfMissed: false);
      await tester.pumpAndSettle();
      expect(tapped, isFalse);
    });
  });
}
