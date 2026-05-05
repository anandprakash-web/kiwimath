import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart';
import 'models/clan.dart';
import 'models/engagement.dart';
import 'models/user_profile.dart';
import 'screens/clan_create_screen.dart';
import 'screens/clan_hub_screen.dart';
import 'screens/clan_join_screen.dart';
import 'screens/clan_leaderboard_screen.dart';
import 'screens/curriculum_screen.dart';
import 'screens/daily_puzzle_screen.dart';
import 'screens/benchmark_test_screen.dart';
import 'screens/growth_tab_screen.dart';
import 'screens/olympiad_screen.dart';
import 'screens/olympiad_tab_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/parent_dashboard_screen.dart';
import 'screens/picture_challenge_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/question_screen_v2.dart';
import 'screens/rewards_screen.dart';
import 'screens/sign_in_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/clan_service.dart';
import 'services/companion_service.dart';
import 'services/engagement_service.dart';
import 'services/growth_service.dart';
import 'theme/kiwi_theme.dart';
import 'widgets/pin_gate.dart';

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

/// v8 app shell — 6-tab navigation.
///
/// Bottom nav: Olympiad / School / Growth / Clan / Parent / Profile
///   - Olympiad: Smart practice with progressive topic unlocking
///   - School: Multi-curriculum chapter browser (Cambridge, NCERT, Singapore, ICSE)
///   - Growth: Diagnostic test → improvement journey with mountain climb
///   - Clan: Team-based puzzle challenges + daily challenge
///   - Parent: PIN-protected dashboard
///   - Profile: Stats, invite, quote, sign out
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

  // Bottom nav: 0=Olympiad, 1=School, 2=Growth, 3=Clan, 4=Parent, 5=Profile
  int _selectedTab = 0;

  // Parent PIN gate
  bool _parentPinVerified = false;

  // Grade
  int _selectedGrade = 1;

  // Student name
  String _studentName = '';

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

  // Engagement
  final EngagementService _engagementService = EngagementService.instance;
  DailyPuzzle? _dailyPuzzle;
  StreakData? _streakData;
  LeagueStatus? _leagueStatus;
  ClanWar? _clanWar;
  RewardData? _rewardData;
  Pledge? _activePledge;

  // Onboarding guard
  bool _onboardingHandled = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
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
            }
            Navigator.of(context).pop();
            _loadProfile();
          },
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Avatar change — save to backend
  // ---------------------------------------------------------------------------

  void _onAvatarChanged(String emoji) {
    setState(() {
      _profile = _profile.copyWith();
    });
    // Save to backend (fire-and-forget)
    _api.updateStudentProfile(userId: widget.userId, avatar: emoji).then((_) {
      _loadProfile(); // Reload to get the updated avatar
    }).catchError((_) {
      // Silently ignore — the avatar will reload on next app start
    });
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

      // Always load engagement data (daily puzzle, streaks, etc.)
      // even without a clan — the Clan landing page shows daily challenge.
      _loadEngagementData();

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

  Future<void> _loadEngagementData() async {
    try {
      final futures = await Future.wait([
        _engagementService.getDailyPuzzle(grade: _selectedGrade),
        _engagementService.getStreak(uid: widget.userId),
        _engagementService.getLeagueStatus(uid: widget.userId),
        _engagementService.getRewards(uid: widget.userId),
        if (_clan != null) _engagementService.getCurrentWar(clanId: _clan!.clanId),
        if (_clan != null) _engagementService.getClanPledges(clanId: _clan!.clanId),
      ]);

      setState(() {
        _dailyPuzzle = futures[0] as DailyPuzzle?;
        _streakData = futures[1] as StreakData?;
        _leagueStatus = futures[2] as LeagueStatus?;
        _rewardData = futures[3] as RewardData?;
        if (futures.length > 4) _clanWar = futures[4] as ClanWar?;
        if (futures.length > 5) {
          final pledges = futures[5] as List<Pledge>?;
          _activePledge = pledges?.where((p) => p.uid == widget.userId && p.active).firstOrNull;
        }
      });
    } catch (e) {
      debugPrint('Failed to load engagement data: $e');
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
  // Engagement navigation callbacks
  // ---------------------------------------------------------------------------

  void _navigateToDailyPuzzle() {
    if (_dailyPuzzle == null) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DailyPuzzleScreen(
          puzzle: _dailyPuzzle!,
          currentStreak: _streakData?.currentStreak ?? 0,
          gemsBalance: _rewardData?.totalGems ?? 0,
          onSubmit: (selectedIndex) async {
            try {
              final options = _dailyPuzzle!.options;
              final answerText = selectedIndex < options.length
                  ? options[selectedIndex]
                  : '$selectedIndex';
              await _engagementService.submitPuzzleAnswer(
                uid: widget.userId,
                puzzleId: _dailyPuzzle!.puzzleId,
                answer: answerText,
                timeTakenSeconds: 0, // DailyPuzzleScreen tracks internally
              );
              _loadEngagementData();
            } catch (e) {
              debugPrint('Failed to submit puzzle answer: $e');
            }
          },
          onClose: () {
            Navigator.of(context).pop();
            _loadEngagementData();
          },
        ),
      ),
    );
  }

  void _navigateToRewards() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RewardsScreen(
          grade: _selectedGrade,
          stickers: _rewardData?.stickersCollected ?? [],
          stickerProgress: _rewardData?.stickerAlbumProgress ?? 0.0,
          badges: _rewardData?.badges ?? [],
          mysteryBoxesAvailable: _rewardData?.mysteryBoxesAvailable ?? 0,
          onOpenMysteryBox: () async {
            try {
              await _engagementService.openMysteryBox(uid: widget.userId);
              _loadEngagementData();
            } catch (e) {
              debugPrint('Failed to open mystery box: $e');
            }
          },
          onClose: () {
            Navigator.of(context).pop();
            _loadEngagementData();
          },
        ),
      ),
    );
  }

  Future<void> _handleClaimDailyReward() async {
    try {
      await _engagementService.claimDailyReward(uid: widget.userId);
      _loadEngagementData();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Daily reward claimed!')),
        );
      }
    } catch (e) {
      debugPrint('Failed to claim daily reward: $e');
    }
  }

  Future<void> _handleOpenMysteryBox() async {
    try {
      await _engagementService.openMysteryBox(uid: widget.userId);
      _loadEngagementData();
    } catch (e) {
      debugPrint('Failed to open mystery box: $e');
    }
  }

  Future<void> _handleMakePledge() async {
    if (_clan == null) return;
    try {
      await _engagementService.createPledge(
        uid: widget.userId,
        targetPuzzles: 5,
      );
      _loadEngagementData();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Pledge made! Your clan is counting on you.')),
        );
      }
    } catch (e) {
      debugPrint('Failed to make pledge: $e');
    }
  }

  // ---------------------------------------------------------------------------
  // Clan landing widget (no-clan state)
  // ---------------------------------------------------------------------------

  Widget _buildClanLanding(KiwiTier tier) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Header ──────────────────────────────────────────────
              Text(
                'Clan',
                style: TextStyle(
                  fontSize: tier.typography.headlineSize + 2,
                  fontWeight: FontWeight.w800,
                  color: tier.colors.textPrimary,
                  fontFamily: tier.typography.fontFamily,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Team up, challenge, compete!',
                style: TextStyle(
                  fontSize: tier.typography.bodySize,
                  color: tier.colors.textSecondary,
                  fontFamily: tier.typography.fontFamily,
                ),
              ),
              const SizedBox(height: 20),

              // ── Daily Challenge card (shown even without a clan) ───
              if (_dailyPuzzle != null)
                _buildDailyPuzzlePreview(tier),
              if (_dailyPuzzle != null) const SizedBox(height: 16),

              // ── Streak info ─────────────────────────────────────────
              if (_streakData != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: tier.colors.cardBg,
                    borderRadius: BorderRadius.circular(tier.shape.cardRadius),
                    border: Border.all(color: tier.colors.topicCardBorder),
                  ),
                  child: Row(
                    children: [
                      const Text('\u{1F525}', style: TextStyle(fontSize: 28)),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${_streakData!.currentStreak} day streak',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: tier.colors.textPrimary,
                            ),
                          ),
                          Text(
                            'Keep solving puzzles daily!',
                            style: TextStyle(
                              fontSize: 13,
                              color: tier.colors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              if (_streakData != null) const SizedBox(height: 20),

              // ── Clan promo ──────────────────────────────────────────
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      tier.colors.primary.withOpacity(0.08),
                      tier.colors.primary.withOpacity(0.03),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(tier.shape.cardRadius),
                  border: Border.all(
                    color: tier.colors.primary.withOpacity(0.2),
                  ),
                ),
                child: Column(
                  children: [
                    const Text('⚔️', style: TextStyle(fontSize: 48)),
                    const SizedBox(height: 12),
                    Text(
                      'Join a Clan!',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w800,
                        color: tier.colors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      'Team up with friends, solve puzzles together, '
                      'and compete on the leaderboard!',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 14,
                        color: tier.colors.textSecondary,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── Create / Join buttons (at bottom) ───────────────────
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
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  /// Daily puzzle preview card for the no-clan landing page.
  Widget _buildDailyPuzzlePreview(KiwiTier tier) {
    final puzzle = _dailyPuzzle!;
    return GestureDetector(
      onTap: _navigateToDailyPuzzle,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              const Color(0xFF1A1A2E),
              const Color(0xFF16213E),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(tier.shape.cardRadius),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF1A1A2E).withOpacity(0.2),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text('\u{1F9E9}', style: TextStyle(fontSize: 22)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Daily Challenge',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                      fontFamily: tier.typography.fontFamily,
                    ),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: KiwiColors.gemGold.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    'Grade $_selectedGrade',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: KiwiColors.gemGold,
                      fontFamily: tier.typography.fontFamily,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              puzzle.title,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: Colors.white.withOpacity(0.9),
                fontFamily: tier.typography.fontFamily,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              puzzle.storyNarrative.length > 80
                  ? '${puzzle.storyNarrative.substring(0, 80)}...'
                  : puzzle.storyNarrative,
              style: TextStyle(
                fontSize: 13,
                color: Colors.white.withOpacity(0.6),
                fontFamily: tier.typography.fontFamily,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: KiwiColors.gemGold.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Center(
                child: Text(
                  'Tap to Solve \u{2728}',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.gemGold,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToQuestions({
    required String topicId,
    required String topicName,
    String? curriculum,
    String? chapter,
  }) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionScreenV2(
          topicId: topicId,
          topicName: topicName,
          userId: widget.userId,
          grade: _selectedGrade,
          curriculum: curriculum,
          chapter: chapter,
          companionService: _companionService,
          onBackToHome: () {
            Navigator.of(context).pop();
            _loadProfile();
          },
        ),
      ),
    );
  }

  void _navigateToDiagnostic() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => BenchmarkTestScreen(
          userId: widget.userId,
          grade: _selectedGrade,
          childName: _studentName.isNotEmpty ? _studentName : null,
          benchmarkType: 'diagnostic',
          onComplete: () {
            Navigator.of(context).pop();
            // Refresh growth data after diagnostic
            setState(() {});
          },
        ),
      ),
    );
  }

  void _onGradeChanged(int grade) {
    if (grade == _selectedGrade) return;
    setState(() => _selectedGrade = grade);
  }

  Future<void> _signOut() async {
    await AuthService().signOut();
  }

  void _onTabTapped(int index) async {
    if (index == 4 && !_parentPinVerified) {
      final verified = await PinGate.show(context);
      if (!verified || !mounted) return;
      setState(() => _parentPinVerified = true);
    }
    setState(() => _selectedTab = index);
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
              // Tab 0 — Olympiad (smart practice + daily worksheets)
              OlympiadTabScreen(
                selectedGrade: _selectedGrade,
                onGradeChanged: _onGradeChanged,
                onStartPractice: (topicId, topicName) => _navigateToQuestions(
                  topicId: topicId,
                  topicName: topicName,
                ),
              ),
              // Tab 1 — School (multi-curriculum chapter browser)
              CurriculumScreen(
                userId: widget.userId,
                selectedGrade: _selectedGrade,
                onGradeChanged: _onGradeChanged,
                onChapterTap: (topicId, topicName, {String? curriculum}) =>
                    _navigateToQuestions(
                  topicId: topicId,
                  topicName: topicName,
                  curriculum: curriculum,
                  chapter: topicName,
                ),
                companionService: _companionService,
              ),
              // Tab 2 — Growth (diagnostic + improvement journey)
              GrowthTabScreen(
                selectedGrade: _selectedGrade,
                onGradeChanged: _onGradeChanged,
                userId: widget.userId,
                onStartDiagnostic: () => _navigateToDiagnostic(),
                onStartPractice: (topicId, topicName) => _navigateToQuestions(
                  topicId: topicId,
                  topicName: topicName,
                ),
              ),
              // Tab 3 — Clan
              _clan != null
                  ? ClanHubScreen(
                      clan: _clan!,
                      activeChallenge: _activeChallenge,
                      challengeProgress: _challengeProgress,
                      // Engagement data
                      dailyPuzzle: _dailyPuzzle,
                      streakData: _streakData,
                      leagueStatus: _leagueStatus,
                      clanWar: _clanWar,
                      rewardData: _rewardData,
                      activePledge: _activePledge,
                      // Callbacks
                      onOpenChallenge: _navigateToChallenge,
                      onOpenLeaderboard: _navigateToLeaderboard,
                      onLeaveClan: _handleLeaveClan,
                      onCopyInviteCode: _copyInviteCode,
                      onSolveDailyPuzzle: _navigateToDailyPuzzle,
                      onClaimDailyReward: _handleClaimDailyReward,
                      onOpenMysteryBox: _handleOpenMysteryBox,
                      onOpenRewards: _navigateToRewards,
                      onMakePledge: _handleMakePledge,
                    )
                  : _buildClanLanding(tier),
              // Tab 4 — Parent Dashboard (PIN-protected)
              _parentPinVerified
                  ? ParentDashboardScreen(
                      userId: widget.userId,
                      childName: _studentName.isNotEmpty
                          ? _studentName
                          : (_profile.displayName != 'Kiwi Learner' ? _profile.displayName : null),
                      embedded: true,
                      curriculum: _profile.curriculum,
                    )
                  : const Scaffold(body: Center(child: CircularProgressIndicator())),
              // Tab 5 — Profile (stats, invite, sign out)
              ProfileScreen(
                userId: widget.userId,
                studentName: _studentName.isNotEmpty
                    ? _studentName
                    : (_profile.displayName != 'Kiwi Learner'
                        ? _profile.displayName
                        : ''),
                grade: _selectedGrade,
                xpTotal: _profile.xpTotal,
                topicsMastered: _profile.topicsMastered,
                currentStreak: _streakData?.currentStreak ?? 0,
                totalGems: _rewardData?.totalGems ?? 0,
                kiwiCoins: _profile.kiwiCoins,
                masteryGems: _profile.masteryGems,
                avatar: _profile.avatar,
                onSignOut: _signOut,
                onRestartOnboarding: _restartOnboarding,
                onAvatarChanged: _onAvatarChanged,
              ),
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
      // Bottom nav: Olympiad / School / Growth / Clan / Parent / Profile
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
                _buildNavItem(0, Icons.emoji_events_rounded, 'Olympiad', tier),
                _buildNavItem(1, Icons.school_rounded, 'School', tier),
                _buildNavItem(2, Icons.trending_up_rounded, 'Growth', tier),
                _buildNavItem(3, Icons.groups_rounded, 'Clan', tier),
                _buildNavItem(4, Icons.family_restroom_rounded, 'Parent', tier),
                _buildNavItem(5, Icons.person_rounded, 'Profile', tier),
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
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
        decoration: isSelected
            ? BoxDecoration(
                color: tier.colors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              )
            : null,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 22,
              color: isSelected ? tier.colors.primary : tier.colors.textMuted,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 10,
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
