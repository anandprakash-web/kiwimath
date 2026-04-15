import 'package:flutter/material.dart';

import 'screens/question_screen.dart';
import 'theme/kiwi_theme.dart';

void main() {
  runApp(const KiwimathApp());
}

class KiwimathApp extends StatelessWidget {
  const KiwimathApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kiwimath',
      debugShowCheckedModeBanner: false,
      theme: kiwiTheme(),
      home: const QuestionScreen(locale: 'IN'),
    );
  }
}
