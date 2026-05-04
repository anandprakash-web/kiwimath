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
import 'models/companion.dart';
import 'services/companion_service.dart';
import 'theme/kiwi_theme.dart';
import 'widgets/companion_view.dart';
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

  // Bottom nav tab index: 0=Home, 1=Learning Path, 2=Parent
  int _selectedTab = 0;

  // Whether the parental gate has been passed this session (for Parent tab).
  bool _parentGatePassed = false;

  // Multi-grade support.
  int _selectedGrade = 1;

  // Kid's display name (from onboarding or profile).
  String _studentName = '';

  // v2 topics.
  List<TopicV2>? _topicsV2;
  bool _topicsV2Loading = false;

  // Curriculum chapters (for home screen + path screen).
  List<Map<String, dynamic>>? _chapters;
  bool _chaptersLoading = false;

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
        // Reject names that look like truncated email prefixes or junk
        // (too short, all lowercase, matches email-like patterns).
        if (_studentName.isEmpty &&
            profile.displayName.isNotEmpty &&
            profile.displayName != 'Kiwi Learner' &&
            profile.displayName.length >= 3) {
          _studentName = profile.displayName;
        }
      });
      _maybeShowOnboarding();
      // Always reload chapters after profile is ready (fixes race condition
      // where _loadChapters() was called before profile had curriculum set).
      if (_profile.hasCurriculum) {
        _loadChapters();
      }
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
  /// Uses the persistent `onboarded_at` flag from Firestore — not a fragile
  /// heuristic based on stats being zero. If the profile fetch failed (network
  /// error), we do NOT trigger onboarding — show offline mode instead.
  void _maybeShowOnboarding() {
    if (_onboardingHandled) return;
    // If we have a valid onboarded_at timestamp, user is not new.
    if (_profile.hasOnboarded) {
      _onboardingHandled = true;
      // Also restore saved grade from profile if available.
      if (_profile.grade != null && _profile.grade != _selectedGrade) {
        setState(() => _selectedGrade = _profile.grade!);
        _loadTopicsV2();
      }
      // Load chapters for curriculum-based users.
      _loadChapters();
      return;
    }
    // If profile has errors (userId empty = fetch failed), don't trigger onboarding.
    if (_error != null) {
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
              final newGrade = result.grade.clamp(1, 6);
              if (newGrade != _selectedGrade) {
                setState(() => _selectedGrade = newGrade);
                _loadTopicsV2();
              }
              Navigator.of(context).pop();
              _loadProfile();
              _loadChapters();
            },
          ),
        ),
      );
    });
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
            final newGrade = result.grade.clamp(1, 6);
            if (newGrade != _selectedGrade) {
              setState(() => _selectedGrade = newGrade);
              _loadTopicsV2();
            }
            Navigator.of(context).pop();
            _loadProfile();
            _loadChapters();
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

  Future<void> _loadChapters() async {
    // Only load chapters if user has a curriculum-based selection (not olympiad).
    final cur = _profile.curriculum;
    if (cur == null || cur.isEmpty || cur == 'olympiad') return;
    setState(() => _chaptersLoading = true);
    try {
      final chapters = await _api.getChapters(
        curriculum: cur,
        grade: _selectedGrade,
      );
      setState(() {
        _chapters = chapters;
        _chaptersLoading = false;
      });
    } catch (e) {
      debugPrint('Failed to load chapters: $e');
      setState(() {
        _chapters = null;
        _chaptersLoading = false;
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
      final plan = await _api.getUnifiedSession(widget.userId, _selectedGrade);
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
            topicName: plan['session_message'] as String? ?? 'Smart Practice',
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
      debugPrint('Failed to load unified session: $e');
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
    _loadChapters();
    _loadStudentLevels();
    _loadMasteryOverview();
  }

  Future<void> _signOut() async {
    await AuthService().signOut();
  }

  void _onTabTapped(int index) async {
    // Tab 2 = Parent Dashboard — requires parental gate
    if (index == 2 && !_parentGatePassed) {
      final verified = await ParentalGate.show(context);
      if (!verified || !mounted) return;
      setState(() => _parentGatePassed = true);
    }
    setState(() => _selectedTab = index);
  }

  void _showProfileSheet() {
    final tier = KiwiTier.forGrade(_selectedGrade);
    final name = _studentName.isNotEmpty ? _studentName : _profile.displayName;
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Handle
              Container(
                width: 36, height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              // Avatar + name
              Container(
                width: 56, height: 56,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [tier.colors.primary, tier.colors.primaryDark],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    name.isNotEmpty ? name[0].toUpperCase() : 'K',
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: Colors.white),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              Text(name, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: tier.colors.textPrimary)),
              Text('Grade $_selectedGrade', style: TextStyle(fontSize: 13, color: tier.colors.textMuted)),
              const SizedBox(height: 6),
              // Stats
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildStatChip('\u{1F525}', '${_profile.streakCurrent}', tier),
                  const SizedBox(width: 8),
                  _buildStatChip('\u{2B50}', '${_profile.xpTotal} XP', tier),
                  const SizedBox(width: 8),
                  _buildStatChip('\u{1FA99}', '${_profile.kiwiCoins}', tier),
                ],
              ),
              const SizedBox(height: 20),
              // Actions
              ListTile(
                leading: Icon(Icons.refresh_rounded, color: tier.colors.primary),
                title: const Text('Retake Diagnostic Test'),
                onTap: () { Navigator.pop(ctx); _restartOnboarding(); },
              ),
              ListTile(
                leading: Icon(Icons.logout_rounded, color: Colors.red.shade400),
                title: const Text('Sign Out'),
                onTap: () { Navigator.pop(ctx); _signOut(); },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatChip(String emoji, String label, KiwiTier tier) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: tier.colors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: tier.colors.primary.withOpacity(0.12)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(emoji, style: const TextStyle(fontSize: 13)),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: tier.colors.textPrimary)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final tier = KiwiTier.forGrade(_selectedGrade);

    // Use IndexedStack to preserve tab state — avoids re-creating
    // LearningPathScreen (and re-fetching from the backend) on every tab tap.
    final shell = Scaffold(
      body: Stack(
        children: [
          IndexedStack(
            index: _selectedTab,
            children: [
              // Tab 0 — Home
              HomeScreen(
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
                onOpenLearningPath: () => _onTabTapped(1),
                onOpenParentDashboard: () => _onTabTapped(2),
                onRestartOnboarding: _restartOnboarding,
                masteryOverview: _masteryOverview,
                onSmartSession: _navigateToSmartSession,
                onAvatarTap: _showProfileSheet,
                curriculum: _profile.curriculum,
                chapters: _chapters,
                chaptersLoading: _chaptersLoading,
              ),
              // Tab 1 — Learning Path
              LearningPathScreen(
                userId: widget.userId,
                grade: _selectedGrade,
                companionService: _companionService,
                studentLevels: _studentLevels,
                embedded: true,
                curriculum: _profile.curriculum,
              ),
              // Tab 2 — Parent Dashboard
              _parentGatePassed
                  ? ParentDashboardScreen(
                      userId: widget.userId,
                      childName: _studentName.isNotEmpty
                          ? _studentName
                          : (_profile.displayName != 'Kiwi Learner' ? _profile.displayName : null),
                      embedded: true,
                      curriculum: _profile.curriculum,
                    )
                  : const Scaffold(body: Center(child: CircularProgressIndicator())),
            ],
          ),
          // Show offline banner if initial profile load failed
          if (_error != null)
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
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: tier.colors.cardBg,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.06),
              blurRadius: 12,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildNavItem(0, Icons.home_rounded, 'Home', tier),
                _buildNavItem(1, Icons.alt_route_rounded, 'Path', tier),
                _buildNavItem(2, Icons.family_restroom_rounded, 'Parent', tier),
              ],
            ),
          ),
        ),
      ),
    );

    return shell;
  }

  Widget _buildNavItem(int index, IconData icon, String label, KiwiTier tier) {
    final isSelected = _selectedTab == index;
    return GestureDetector(
      onTap: () => _onTabTapped(index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: isSelected
            ? BoxDecoration(
                color: tier.colors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(14),
              )
            : null,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 24,
              color: isSelected ? tier.colors.primary : tier.colors.textMuted,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                color: isSelected ? tier.colors.primary : tier.colors.textMuted,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
