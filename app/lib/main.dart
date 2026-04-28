import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart';
import 'models/question_v2.dart';
import 'models/user_profile.dart';
import 'screens/home_screen.dart';
import 'screens/question_screen_v2.dart';
import 'screens/sign_in_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/companion_service.dart';
import 'theme/kiwi_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
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
      home: const _AuthWrapper(),
    );
  }
}

/// Listens to auth state and shows either the sign-in screen (when signed out)
/// or the main app shell (when signed in).
class _AuthWrapper extends StatelessWidget {
  const _AuthWrapper();

  @override
  Widget build(BuildContext context) {
    final auth = AuthService();
    return StreamBuilder<User?>(
      stream: auth.authStateChanges,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        final user = snap.data;
        if (user == null) {
          return const SignInScreen();
        }
        return _AppShell(userId: user.uid);
      },
    );
  }
}

/// v2 app shell — unified on the v2 adaptive engine.
/// All topics (both curriculum and olympiad) route through QuestionScreenV2.
/// Profile (streak, gems, XP) refreshes on app start and after each session.
class _AppShell extends StatefulWidget {
  final String userId;
  const _AppShell({required this.userId});

  @override
  State<_AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<_AppShell> {
  final _api = ApiClient();
  UserProfile _profile = UserProfile.empty;
  bool _loading = true;
  String? _error;

  // Multi-grade support.
  int _selectedGrade = 1;

  // v2 topics.
  List<TopicV2>? _topicsV2;
  bool _topicsV2Loading = false;

  // Companion system.
  final CompanionService _companionService = CompanionService();

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _loadTopicsV2();
    _companionService.initialize();
  }

  @override
  void dispose() {
    _companionService.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final profile = await _api.getProfile(widget.userId);
      setState(() {
        _profile = profile;
        _loading = false;
      });
    } catch (e) {
      debugPrint('Failed to load profile: $e');
      setState(() {
        _profile = UserProfile(userId: widget.userId);
        _loading = false;
        _error = 'Offline mode \u2014 data will sync when connected';
      });
    }
  }

  Future<void> _loadTopicsV2() async {
    setState(() => _topicsV2Loading = true);
    try {
      final topics = await _api.getTopicsV2(grade: _selectedGrade);
      setState(() {
        _topicsV2 = topics;
        _topicsV2Loading = false;
      });
    } catch (e) {
      debugPrint('Failed to load v2 topics: $e');
      setState(() {
        _topicsV2 = null;
        _topicsV2Loading = false;
      });
    }
  }

  void _navigateToQuestions({
    required String topicId,
    required String topicName,
  }) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionScreenV2(
          topicId: topicId,
          topicName: topicName,
          userId: widget.userId,
          grade: _selectedGrade,
          companionService: _companionService,
          onBackToHome: () {
            Navigator.of(context).pop();
            _loadProfile();
          },
        ),
      ),
    );
  }

  void _onGradeChanged(int grade) {
    if (grade == _selectedGrade) return;
    setState(() => _selectedGrade = grade);
    _loadTopicsV2(); // Reload topics for the new grade
  }

  Future<void> _signOut() async {
    await AuthService().signOut();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final homeScreen = HomeScreen(
      streak: _profile.streakCurrent,
      kiwiCoins: _profile.kiwiCoins,
      masteryGems: _profile.masteryGems,
      xp: _profile.xpTotal,
      dailyProgress: _profile.dailyProgress,
      dailyGoal: _profile.dailyGoal,
      onTopicTap: (topicId, topicName) => _navigateToQuestions(
        topicId: topicId,
        topicName: topicName,
      ),
      onSignOut: _signOut,
      selectedGrade: _selectedGrade,
      onGradeChanged: _onGradeChanged,
      topicsV2: _topicsV2,
      topicsV2Loading: _topicsV2Loading,
      companionService: _companionService,
    );

    // Show offline banner if initial profile load failed.
    if (_error != null) {
      return Stack(
        children: [
          homeScreen,
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF3E0),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFFFFCC80)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.cloud_off, size: 16, color: Color(0xFFE65100)),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _error!,
                        style: const TextStyle(fontSize: 12, color: Color(0xFFE65100)),
                      ),
                    ),
                    GestureDetector(
                      onTap: _loadProfile,
                      child: const Padding(
                        padding: EdgeInsets.only(left: 8),
                        child: Icon(Icons.refresh, size: 18, color: Color(0xFFE65100)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      );
    }

    return homeScreen;
  }
}
