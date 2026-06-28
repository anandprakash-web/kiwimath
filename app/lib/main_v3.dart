// Entry point for the new Level/Grade experience (v3).
//
// Build/run this instead of main.dart to get the remapped 4-tab app on /v3:
//   flutter run -t lib/main_v3.dart
//   flutter build apk --release -t lib/main_v3.dart
//
// It reuses your existing Firebase init + sign-in; everything after sign-in
// is the new self-contained app in lib/v3/kiwi_v3.dart (talks to /v3 only).

import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

import 'firebase_options.dart';
import 'screens/sign_in_screen.dart';
import 'v3/books_integration.dart';
import 'v3/kiwi_v3.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  // KiwiReader state lives in a ProviderScope; the existing setState screens are
  // unaffected. backendBooksOverrides() wires the real catalog/wallet/entitlements
  // (swap to booksOverrides() for the no-backend dev demo).
  runApp(ProviderScope(overrides: backendBooksOverrides(), child: const KiwiMathV3App()));
}

class KiwiMathV3App extends StatelessWidget {
  const KiwiMathV3App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kiwimath',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFFFF6D00),
        scaffoldBackgroundColor: const Color(0xFFFAFAF7),
        // Branded fonts via google_fonts (fetched once, then cached) — no
        // bundled TTFs needed. Bundle them later to remove the first-load fetch.
        textTheme: GoogleFonts.nunitoTextTheme(),
      ),
      home: const _Gate(),
    );
  }
}

/// Firebase auth gate — sign-in screen or the new v3 shell.
class _Gate extends StatelessWidget {
  const _Gate();

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(body: Center(child: CircularProgressIndicator()));
        }
        final user = snap.data;
        if (user == null) {
          return const SignInScreen();
        }
        return KiwiV3Shell(userId: user.uid);
      },
    );
  }
}
