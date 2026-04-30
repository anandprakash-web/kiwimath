import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart';
import 'models/question_v2.dart';
import 'models/student_levels.dart';
import 'models/user_profile.dart';
import 'screens/home_screen.dart';
import 'screens/learning_path_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/parent_dashboard_screen.dart';
import 'screens/question_screen_v2.dart';
import 'screens/sign_in_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/companion_service.dart';
import 'theme/kiwi_theme.dart';
import 'widgets/parental_gate.dart';

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

  // Kid's display name (from onboarding or profile).
  String _studentName = '';

  // v2 topics.
  List<TopicV2>? _topicsV2;
  bool _topicsV2Loading = false;

  // Student level progression.
  StudentLevels? _studentLevels;

  // Mastery overview for home screen badges.
  Map<String, dynamic>? _masteryOverview;

  // Companion system.
  final CompanionService _companionService = CompanionService();

  // First-launch onboarding routing — guard so we only push the screen once
  // per signed-in session even if the profile reloads.
  bool _onboardingHandled = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _loadTopicsV2();
    _loadStudentLevels();
    _loadMasteryOverview();
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
        // Use saved display name if we don't already have one from onboarding.
        if (_studentName.isEmpty &&
            profile.displayName.isNotEmpty &&
            profile.displayName != 'Kiwi Learner') {
          _studentName = profile.displayName;
        }
      });
      _maybeShowOnboarding();
    } catch (e) {
      debugPrint('Failed to load profile: $e');
      setState(() {
        _profile = UserProfile(userId: widget.userId);
        _loading = false;
        _error = 'Offline mode \u2014 data will sync when connected';
      });
    }
  }

  /// Detects a first-launch and pushes the onboarding flow.
  ///
  /// Heuristic: if the loaded profile has zero XP, zero streak, and zero
  /// daily progress, treat it as a brand-new user. After onboarding completes
  /// (which submits 10 answers and seeds the adaptive engine), the next
  /// profile load will have non-zero XP and we'll skip this branch.
  void _maybeShowOnboarding() {
    if (_onboardingHandled) return;
    final isFresh = _profile.xpTotal == 0 &&
        _profile.streakCurrent == 0 &&
        _profile.dailyProgress == 0 &&
        _profile.kiwiCoins == 0;
    if (!isFresh) {
      _onboardingHandled = true;
      return;
    }
    _onboardingHandled = true;
    // Defer to next frame so we have a valid Navigator context.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          fullscreenDialog: true,
          builder: (_) => OnboardingScreen(
            userId: widget.userId,
            onComplete: (result) {
              // Capture kid's name from onboarding.
              if (result.kidName.isNotEmpty) {
                setState(() => _studentName = result.kidName);
              }
              // Switch the home view to the recommended grade and refresh.
              final newGrade = result.grade.clamp(1, 5);
              if (newGrade != _selectedGrade) {
                setState(() => _selectedGrade = newGrade);
                _loadTopicsV2();
              }
              Navigator.of(context).pop();
              _loadProfile();
            },
          ),
        ),
      );
    });
  }

  Future<void> _openParentDashboard() async {
    // Parental gate — multiplication problem a kid can't solve.
    final verified = await ParentalGate.show(context);
    if (!verified || !mounted) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ParentDashboardScreen(
          userId: widget.userId,
          childName: _profile.displayName == 'Kiwi Learner'
              ? null
              : _profile.displayName,
        ),
      ),
    );
  }

  void _openLearningPath() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => LearningPathScreen(
          userId: widget.userId,
          grade: _selectedGrade,
          companionService: _companionService,
        ),
      ),
    );
  }

  void _restartOnboarding() {
    Navigator.of(context).push(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => OnboardingScreen(
          userId: widget.userId,
          onComplete: (result) {
            if (result.kidName.isNotEmpty) {
              setState(() => _studentName = result.kidName);
            }
            final newGrade = result.grade.clamp(1, 5);
            if (newGrade != _selectedGrade) {
              setState(() => _selectedGrade = newGrade);
              _loadTopicsV2();
            }
            Navigator.of(context).pop();
            _loadProfile();
          },
        ),
      ),
    );
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

  Future<void> _loadStudentLevels() async {
    try {
      final levels = await _api.getStudentLevels(
        userId: widget.userId,
        grade: _selectedGrade,
      );
      setState(() => _studentLevels = levels);
    } catch (e) {
      debugPrint('Failed to load student levels: $e');
    }
  }

  Future<void> _loadMasteryOverview() async {
    try {
      final overview = await _api.getMasteryOverview(widget.userId, _selectedGrade);
      setState(() => _masteryOverview = overview);
    } catch (e) {
      debugPrint('Failed to load mastery overview: $e');
    }
  }

  Future<void> _navigateToSmartSession() async {
    try {
      final plan = await _api.getSessionPlan(widget.userId, _selectedGrade);
      if (!mounted) return;
      final questions = plan['questions'] as List<dynamic>?;
      if (questions == null || questions.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No questions available for smart session')),
        );
        return;
      }
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => QuestionScreenV2(
            topicId: 'smart-session',
            topicName: 'Smart Practice',
            userId: widget.userId,
            grade: _selectedGrade,
            companionService: _companionService,
            sessionPlan: questions.cast<Map<String, dynamic>>(),
            onBackToHome: () {
              Navigator.of(context).pop();
              _loadProfile();
              _loadStudentLevels();
              _loadMasteryOverview();
            },
          ),
        ),
      );
    } catch (e) {
      debugPrint('Failed to load session plan: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not load smart session. Try again.')),
        );
      }
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
            _loadStudentLevels();
            _loadMasteryOverview();
          },
        ),
      ),
    );
  }

  void _onGradeChanged(int grade) {
    if (grade == _selectedGrade) return;
    setState(() => _selectedGrade = grade);
    _loadTopicsV2();
    _loadStudentLevels();
    _loadMasteryOverview();
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
      studentName: _studentName.isNotEmpty ? _studentName : _profile.displayName,
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
      studentLevels: _studentLevels,
      onOpenLearningPath: _openLearningPath,
      onOpenParentDashboard: _openParentDashboard,
      onRestartOnboarding: _restartOnboarding,
      masteryOverview: _masteryOverview,
      onSmartSession: _navigateToSmartSession,
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
