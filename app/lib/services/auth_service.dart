import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

/// Thin wrapper over firebase_auth. Gives the rest of the app a stable, typed
/// interface so we can swap providers (Google, Apple, phone OTP) without
/// rewriting screens.
class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final GoogleSignIn _googleSignIn = GoogleSignIn();

  /// Emits the current user (null = signed out) whenever auth state changes.
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  User? get currentUser => _auth.currentUser;

  Future<User> signInWithEmail({
    required String email,
    required String password,
  }) async {
    final cred = await _auth.signInWithEmailAndPassword(
      email: email,
      password: password,
    );
    final user = cred.user;
    if (user == null) {
      throw AuthFailure('Sign-in returned no user');
    }
    return user;
  }

  Future<User> signUpWithEmail({
    required String email,
    required String password,
  }) async {
    final cred = await _auth.createUserWithEmailAndPassword(
      email: email,
      password: password,
    );
    final user = cred.user;
    if (user == null) {
      throw AuthFailure('Sign-up returned no user');
    }
    return user;
  }

  /// Trigger Google sign-in. On Android this shows the native account picker.
  /// Returns the FirebaseAuth User on success, or null if the user cancelled.
  Future<User?> signInWithGoogle() async {
    // Step 1: Google-side flow (account picker)
    final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
    if (googleUser == null) {
      // User cancelled — not an error.
      return null;
    }

    // Step 2: Get the auth credentials Google gave us
    final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
    final credential = GoogleAuthProvider.credential(
      accessToken: googleAuth.accessToken,
      idToken: googleAuth.idToken,
    );

    // Step 3: Hand them to Firebase Auth
    final userCredential = await _auth.signInWithCredential(credential);
    return userCredential.user;
  }

  Future<void> signOut() async {
    // Sign out of Google too so the next sign-in shows the picker again.
    await _googleSignIn.signOut();
    await _auth.signOut();
  }

  Future<void> sendPasswordResetEmail(String email) async {
    await _auth.sendPasswordResetEmail(email: email);
  }

  // ---------------------------------------------------------------------------
  // Phone OTP sign-in
  // ---------------------------------------------------------------------------

  /// Start phone number verification. Firebase sends an OTP SMS.
  ///
  /// [onCodeSent] fires once the SMS is dispatched — the caller should
  /// show an OTP input field and call [verifyOtp] with the code.
  ///
  /// [onAutoVerified] fires on Android when the SMS is auto-read.
  ///
  /// [onError] fires if verification fails (invalid number, quota, etc.).
  Future<void> sendOtp({
    required String phoneNumber,
    required void Function(String verificationId) onCodeSent,
    required void Function(User user) onAutoVerified,
    required void Function(String message) onError,
  }) async {
    await _auth.verifyPhoneNumber(
      phoneNumber: phoneNumber,
      timeout: const Duration(seconds: 60),

      // Android auto-verification — SMS is read automatically.
      verificationCompleted: (PhoneAuthCredential credential) async {
        final userCredential = await _auth.signInWithCredential(credential);
        if (userCredential.user != null) {
          onAutoVerified(userCredential.user!);
        }
      },

      verificationFailed: (FirebaseAuthException e) {
        onError(humanMessage(e));
      },

      codeSent: (String verificationId, int? resendToken) {
        onCodeSent(verificationId);
      },

      codeAutoRetrievalTimeout: (String verificationId) {
        // Android auto-retrieval timed out — user must enter code manually.
      },
    );
  }

  /// Verify an OTP code entered by the user.
  Future<User> verifyOtp({
    required String verificationId,
    required String smsCode,
  }) async {
    final credential = PhoneAuthProvider.credential(
      verificationId: verificationId,
      smsCode: smsCode,
    );
    final userCredential = await _auth.signInWithCredential(credential);
    final user = userCredential.user;
    if (user == null) {
      throw AuthFailure('OTP verification returned no user');
    }
    return user;
  }

  /// Convert a FirebaseAuthException into a friendlier message.
  static String humanMessage(Object error) {
    if (error is FirebaseAuthException) {
      switch (error.code) {
        case 'invalid-email':
          return 'That email address doesn\'t look right.';
        case 'user-disabled':
          return 'This account has been disabled.';
        case 'user-not-found':
        case 'wrong-password':
        case 'invalid-credential':
          return 'Email or password is incorrect.';
        case 'email-already-in-use':
          return 'An account with this email already exists. Try signing in.';
        case 'weak-password':
          return 'Password must be at least 6 characters.';
        case 'too-many-requests':
          return 'Too many attempts. Wait a moment and try again.';
        case 'invalid-verification-code':
          return 'Invalid OTP code. Please check and try again.';
        case 'invalid-phone-number':
          return 'Invalid phone number. Include country code (e.g. +91).';
        case 'session-expired':
          return 'OTP has expired. Please request a new code.';
        case 'network-request-failed':
          return 'Network error. Check your internet connection.';
        case 'account-exists-with-different-credential':
          return 'You already signed up with a different method. Try that.';
      }
      return error.message ?? 'Authentication failed. (${error.code})';
    }
    if (error is AuthFailure) return error.message;
    final msg = error.toString();
    if (msg.contains('ApiException: 10')) {
      return 'Google sign-in not configured. '
          'Ask your cofounder about the SHA-1 fingerprint.';
    }
    if (msg.contains('ApiException: 12501')) {
      return 'Sign-in cancelled.';
    }
    return 'Something went wrong. Please try again.';
  }
}

class AuthFailure implements Exception {
  final String message;
  AuthFailure(this.message);
  @override
  String toString() => 'AuthFailure: $message';
}
