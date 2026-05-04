import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart';
import 'models/clan.dart';
import 'models/question_v2.dart';
import 'models/student_levels.dart';
import 'models/user_profile.dart';
import 'screens/clan_create_screen.dart';
import 'screens/clan_hub_screen.dart';
import 'screens/clan_join_screen.dart';
import 'screens/clan_leaderboard_screen.dart';
import 'screens/home_screen.dart';
import 'screens/learning_path_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/parent_dashboard_screen.dart';
import 'screens/picture_challenge_screen.dart';
import 'screens/question_screen_v2.dart';
import 'screens/sign_in_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/clan_service.dart';
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

/// Auth state listener — sign-in or main app shell.
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

/// v5 app shell — pure adaptive engine, ground-up rebuild.
///
/// Key architecture changes from v4:
///   - Adaptive practice is THE primary experience
///   - No curriculum gating on home screen
///   - Bottom nav: "Home" / "School" / "Parent"
///   - Chapters load only for syllabus tab (not home)
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

  // Bottom nav: 0=Home, 1=School, 2=Clan, 3=Parent
  int _selectedTab = 0;

  // Parental gate
  bool _parentGatePassed = false;

  // Grade
  int _selectedGrade = 1;

  // Student name
  String _studentName = '';

  // v2 adaptive topics (ALWAYS loaded — the primary content)
  List<TopicV2>? _topicsV2;
  bool _topicsV2Loading = false;

  // Student levels
  StudentLevels? _studentLevels;

  // Mastery overview
  Map<String, dynamic>? _masteryOverview;

  // Companion
  final CompanionService _companionService = CompanionService();

  // Clan
  final ClanService _clanService = ClanService.instance;
  Clan? _clan;
  ChallengeInfo? _activeChallenge;
  ChallengeProgress? _challengeProgress;
  List<GuessEntry> _guesses = [];
  List<LeaderboardEntry> _leaderboardEntries = [];
  bool _clanLoading = false;

  // Onboarding guard
  bool _onboardingHandled = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
    _loadTopicsV2();
    _loadStudentLevels();
    _loadMasteryOverview();
    _companionService.initialize();
    _loadClan();
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
        if (_studentName.isEmpty &&
            profile.displayName.isNotEmpty &&
            profile.displayName != 'Kiwi Learner' &&
            profile.displayName.length >= 3) {
          _studentName = profile.displayName;
        }
      });
      _maybeShowOnboarding();
    } catch (e) {
      debugPrint('Failed to load profile: $e');
      setState(() {
        _profile = UserProfile(userId: widget.userId);
        _loading = false;
        _error = 'Offline mode — data will sync when connected';
      });
    }
  }

  void _maybeShowOnboarding() {
    if (_onboardingHandled) return;
    if (_profile.hasOnboarded) {
      _onboardingHandled = true;
      if (_profile.grade != null && _profile.grade != _selectedGrade) {
        setState(() => _selectedGrade = _profile.grade!);
        _loadTopicsV2();
      }
      return;
    }
    if (_error != null) {
      _onboardingHandled = true;
      return;
    }
    _onboardingHandled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
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

  // ---------------------------------------------------------------------------
  // Clan loading
  // ---------------------------------------------------------------------------

  Future<void> _loadClan() async {
    setState(() => _clanLoading = true);
    try {
      // Check if user belongs to a clan
      final myClan = await _clanService.getMyClan(userUid: widget.userId);
      setState(() => _clan = myClan);

      if (myClan != null) {
        // Load active challenge
        final challenge = await _clanService.getActiveChallenge(grade: _selectedGrade);
        setState(() => _activeChallenge = challenge);

        // Load challenge progress if there's an active challenge
        if (challenge != null) {
          _loadChallengeProgress();
        }
      } else {
        setState(() {
          _activeChallenge = null;
          _challengeProgress = null;
        });
      }
    } catch (e) {
      debugPrint('Failed to load clan data: $e');
    } finally {
      setState(() => _clanLoading = false);
    }
  }

  Future<void> _loadChallengeProgress() async {
    if (_clan == null || _activeChallenge == null) return;
    try {
      final progress = await _clanService.getChallengeProgress(
        challengeId: _activeChallenge!.challengeId,
        clanId: _clan!.clanId,
      );
      final guesses = await _clanService.getGuessBoard(
        challengeId: _activeChallenge!.challengeId,
        clanId: _clan!.clanId,
      );
      setState(() {
        _challengeProgress = progress;
        _guesses = guesses;
      });
    } catch (e) {
      debugPrint('Failed to load challenge progress: $e');
    }
  }

  Future<void> _loadLeaderboard() async {
    try {
      final entries = await _clanService.getLeaderboard(grade: _selectedGrade);
      setState(() => _leaderboardEntries = entries);
    } catch (e) {
      debugPrint('Failed to load leaderboard: $e');
    }
  }

  Future<void> _handleCreateClan(String name, String crestShape, String crestColor) async {
    try {
      final clan = await _clanService.createClan(
        name: name,
        grade: _selectedGrade,
        leaderUid: widget.userId,
        parentUid: widget.userId,
        crestShape: crestShape,
        crestColor: crestColor,
      );
      setState(() => _clan = clan);
      if (mounted) Navigator.of(context).pop();
      _loadClan();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not create clan: $e')),
        );
      }
    }
  }

  Future<void> _handleJoinClan(String inviteCode) async {
    try {
      final clan = await _clanService.joinClan(
        inviteCode: inviteCode,
        userUid: widget.userId,
        parentUid: widget.userId,
        userGrade: _selectedGrade,
      );
      setState(() => _clan = clan);
      if (mounted) Navigator.of(context).pop();
      _loadClan();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not join clan: $e')),
        );
      }
    }
  }

  void _navigateToCreateClan() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ClanCreateScreen(
          grade: _selectedGrade,
          leaderUid: widget.userId,
          onCreate: _handleCreateClan,
          onBack: () => Navigator.of(context).pop(),
        ),
      ),
    );
  }

  void _navigateToJoinClan() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ClanJoinScreen(
          userGrade: _selectedGrade,
          userUid: widget.userId,
          onJoin: _handleJoinClan,
          onBack: () => Navigator.of(context).pop(),
          onCreateInstead: () {
            Navigator.of(context).pop();
            _navigateToCreateClan();
          },
        ),
      ),
    );
  }

  void _navigateToChallenge() {
    if (_activeChallenge == null || _challengeProgress == null) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => PictureChallengeScreen(
          challenge: _activeChallenge!,
          progress: _challengeProgress!,
          guesses: _guesses,
          isLeader: _clan?.leaderUid == widget.userId,
          userUid: widget.userId,
          onSubmitAnswer: (answer) async {
            try {
              await _clanService.submitAnswer(
                challengeId: _activeChallenge!.challengeId,
                clanId: _clan!.clanId,
                leaderUid: widget.userId,
                answerText: answer,
              );
              _loadChallengeProgress();
            } catch (e) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Could not submit answer: $e')),
                );
              }
            }
          },
          onSubmitGuess: (guess) async {
            try {
              await _clanService.submitGuess(
                challengeId: _activeChallenge!.challengeId,
                clanId: _clan!.clanId,
                userUid: widget.userId,
                guessText: guess,
              );
              _loadChallengeProgress();
            } catch (e) {
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Could not submit guess: $e')),
                );
              }
            }
          },
          onBack: () {
            Navigator.of(context).pop();
            _loadChallengeProgress();
          },
        ),
      ),
    );
  }

  void _navigateToLeaderboard() {
    _loadLeaderboard();
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ClanLeaderboardScreen(
          entries: _leaderboardEntries,
          currentClanId: _clan?.clanId,
          selectedGrade: _selectedGrade,
          onGradeChanged: (grade) {},
          onBack: () => Navigator.of(context).pop(),
        ),
      ),
    );
  }

  Future<void> _handleLeaveClan() async {
    if (_clan == null) return;
    try {
      await _clanService.removeMember(
        clanId: _clan!.clanId,
        userUid: widget.userId,
      );
      setState(() {
        _clan = null;
        _challengeProgress = null;
        _guesses = [];
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not leave clan: $e')),
        );
      }
    }
  }

  void _copyInviteCode() {
    if (_clan?.inviteCode != null) {
      // Use Clipboard.setData in the hub screen's callback
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Invite code copied: ${_clan!.inviteCode}')),
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Clan landing widget (no-clan state)
  // ---------------------------------------------------------------------------

  Widget _buildClanLanding(KiwiTier tier) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('⚔️', style: TextStyle(fontSize: 64)),
                const SizedBox(height: 16),
                Text(
                  'Join a Clan!',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.w800,
                    color: tier.colors.textPrimary,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Team up with friends, solve puzzles together, and compete on the leaderboard!',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 15,
                    color: tier.colors.textSecondary,
                  ),
                ),
                const SizedBox(height: 32),
                // Create clan button
                SizedBox(
                  width: double.infinity,
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [tier.colors.primary, tier.colors.primaryDark],
                      ),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: ElevatedButton(
                      onPressed: _navigateToCreateClan,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: const Text(
                        'Create a Clan',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                // Join clan button
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton(
                    onPressed: _navigateToJoinClan,
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: BorderSide(color: tier.colors.primary, width: 2),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    child: Text(
                      'Join with Invite Code',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: tier.colors.primary,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
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
    _loadStudentLevels();
    _loadMasteryOverview();
  }

  Future<void> _signOut() async {
    await AuthService().signOut();
  }

  void _onTabTapped(int index) async {
    if (index == 3 && !_parentGatePassed) {
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
              Container(
                width: 36, height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(height: 16),
              // Avatar — Kiwimath orange gradient
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
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildStatChip('\u{1F525}', '${_profile.streakCurrent}', tier),
                  const SizedBox(width: 8),
                  _buildStatChip('\u{26A1}', '${_profile.xpTotal} XP', tier),
                  const SizedBox(width: 8),
                  _buildStatChip('\u{1FA99}', '${_profile.kiwiCoins}', tier),
                ],
              ),
              const SizedBox(height: 20),
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

    final shell = Scaffold(
      body: Stack(
        children: [
          IndexedStack(
            index: _selectedTab,
            children: [
              // Tab 0 — Home (adaptive-first, no curriculum gating)
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
                onOpenParentDashboard: () => _onTabTapped(3),
                onRestartOnboarding: _restartOnboarding,
                masteryOverview: _masteryOverview,
                onSmartSession: _navigateToSmartSession,
                onAvatarTap: _showProfileSheet,
              ),
              // Tab 1 — School (curriculum chapters)
              LearningPathScreen(
                userId: widget.userId,
                grade: _selectedGrade,
                companionService: _companionService,
                studentLevels: _studentLevels,
                embedded: true,
                curriculum: _profile.curriculum,
              ),
              // Tab 2 — Clan
              _clan != null
                  ? ClanHubScreen(
                      clan: _clan!,
                      activeChallenge: _activeChallenge,
                      challengeProgress: _challengeProgress,
                      onOpenChallenge: _navigateToChallenge,
                      onOpenLeaderboard: _navigateToLeaderboard,
                      onLeaveClan: _handleLeaveClan,
                      onCopyInviteCode: _copyInviteCode,
                    )
                  : _buildClanLanding(tier),
              // Tab 3 — Parent Dashboard
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
          // Offline banner
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
      // Bottom nav: Home / School / Parent
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
                _buildNavItem(1, Icons.school_rounded, 'School', tier),
                _buildNavItem(2, Icons.groups_rounded, 'Clan', tier),
                _buildNavItem(3, Icons.family_restroom_rounded, 'Parent', tier),
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
