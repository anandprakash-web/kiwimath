//
// Generated file. Do not edit.
// This file is generated from template in file `flutter_tools/lib/src/flutter_plugins.dart`.
//

// @dart = 3.3

import 'dart:io'; // flutter_ignore: dart_io_import.
import 'package:google_sign_in_android/google_sign_in_android.dart' as google_sign_in_android;
import 'package:google_sign_in_ios/google_sign_in_ios.dart' as google_sign_in_ios;
import 'package:google_sign_in_ios/google_sign_in_ios.dart' as google_sign_in_ios;

@pragma('vm:entry-point')
class _PluginRegistrant {

  @pragma('vm:entry-point')
  static void register() {
    if (Platform.isAndroid) {
      try {
        google_sign_in_android.GoogleSignInAndroid.registerWith();
      } catch (err) {
        print(
          '`google_sign_in_android` threw an error: $err. '
          'The app may not function as expected until you remove this plugin from pubspec.yaml'
        );
      }

    } else if (Platform.isIOS) {
      try {
        google_sign_in_ios.GoogleSignInIOS.registerWith();
      } catch (err) {
        print(
          '`google_sign_in_ios` threw an error: $err. '
          'The app may not function as expected until you remove this plugin from pubspec.yaml'
        );
      }

    } else if (Platform.isLinux) {
    } else if (Platform.isMacOS) {
      try {
        google_sign_in_ios.GoogleSignInIOS.registerWith();
      } catch (err) {
        print(
          '`google_sign_in_ios` threw an error: $err. '
          'The app may not function as expected until you remove this plugin from pubspec.yaml'
        );
      }

    } else if (Platform.isWindows) {
    }
  }
}
