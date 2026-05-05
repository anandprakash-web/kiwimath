import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/kiwi_theme.dart';

/// Profile tab — emoji avatar, student stats, math quote, invite, sign out.
class ProfileScreen extends StatefulWidget {
  final String userId;
  final String studentName;
  final int grade;
  final int xpTotal;
  final int topicsMastered;
  final int currentStreak;
  final int totalGems;
  final int kiwiCoins;
  final int masteryGems;
  final String avatar; // emoji key or 'kiwi_default'
  final VoidCallback onSignOut;
  final VoidCallback onRestartOnboarding;
  final void Function(String emoji) onAvatarChanged;

  const ProfileScreen({
    super.key,
    required this.userId,
    required this.studentName,
    required this.grade,
    this.xpTotal = 0,
    this.topicsMastered = 0,
    this.currentStreak = 0,
    this.totalGems = 0,
    this.kiwiCoins = 0,
    this.masteryGems = 0,
    this.avatar = 'kiwi_default',
    required this.onSignOut,
    required this.onRestartOnboarding,
    required this.onAvatarChanged,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _showAvatarPicker = false;

  // ── Avatar emoji options — Roblox-style fun characters ──────────────────
  static const List<Map<String, String>> _avatarOptions = [
    // Animals
    {'emoji': '\u{1F43B}', 'label': 'Bear'},         // 🐻
    {'emoji': '\u{1F431}', 'label': 'Cat'},           // 🐱
    {'emoji': '\u{1F436}', 'label': 'Dog'},           // 🐶
    {'emoji': '\u{1F42F}', 'label': 'Tiger'},         // 🐯
    {'emoji': '\u{1F981}', 'label': 'Lion'},          // 🦁
    {'emoji': '\u{1F43C}', 'label': 'Panda'},         // 🐼
    {'emoji': '\u{1F428}', 'label': 'Koala'},         // 🐨
    {'emoji': '\u{1F98A}', 'label': 'Fox'},           // 🦊
    {'emoji': '\u{1F430}', 'label': 'Bunny'},         // 🐰
    {'emoji': '\u{1F427}', 'label': 'Penguin'},       // 🐧
    {'emoji': '\u{1F43A}', 'label': 'Wolf'},          // 🐺
    {'emoji': '\u{1F984}', 'label': 'Unicorn'},       // 🦄
    // Cool characters
    {'emoji': '\u{1F47E}', 'label': 'Alien'},         // 👾
    {'emoji': '\u{1F916}', 'label': 'Robot'},         // 🤖
    {'emoji': '\u{1F47B}', 'label': 'Ghost'},         // 👻
    {'emoji': '\u{1F920}', 'label': 'Cowboy'},        // 🤠
    {'emoji': '\u{1F978}', 'label': 'Ninja'},         // 🥷 (disguised face)
    {'emoji': '\u{1F9D9}', 'label': 'Wizard'},        // 🧙
    // Space & nature
    {'emoji': '\u{1F680}', 'label': 'Rocket'},        // 🚀
    {'emoji': '\u{2B50}', 'label': 'Star'},           // ⭐
    {'emoji': '\u{1F525}', 'label': 'Fire'},          // 🔥
    {'emoji': '\u{1F308}', 'label': 'Rainbow'},       // 🌈
    {'emoji': '\u{1F33B}', 'label': 'Sunflower'},     // 🌻
    {'emoji': '\u{1F40B}', 'label': 'Whale'},         // 🐋
  ];

  // ── Quotes from mathematicians and puzzle masters ──────────────────────
  static const List<Map<String, String>> _quotes = [
    {
      'text': 'A mathematician is a device for turning coffee into theorems.',
      'author': 'Paul Erdős',
    },
    {
      'text':
          'An equation means nothing to me unless it expresses a thought of God.',
      'author': 'Srinivasa Ramanujan',
    },
    {
      'text': 'If you can\'t solve a problem, then there is an easier problem you can solve: find it.',
      'author': 'George Pólya',
    },
    {
      'text':
          'The only way to learn mathematics is to do mathematics.',
      'author': 'Paul Halmos',
    },
    {
      'text': 'Pure mathematics is, in its way, the poetry of logical ideas.',
      'author': 'Albert Einstein',
    },
    {
      'text':
          'Do not worry about your difficulties in mathematics. I can assure you mine are still greater.',
      'author': 'Albert Einstein',
    },
    {
      'text': 'Mathematics is not about numbers, equations, or algorithms: it is about understanding.',
      'author': 'William Paul Thurston',
    },
    {
      'text': 'The essence of mathematics lies in its freedom.',
      'author': 'Georg Cantor',
    },
    {
      'text': 'God made the integers; all else is the work of man.',
      'author': 'Leopold Kronecker',
    },
    {
      'text': 'In mathematics the art of proposing a question must be held of higher value than solving it.',
      'author': 'Georg Cantor',
    },
    {
      'text':
          'The puzzle is not a riddle to be solved once, but a garden to be tended daily.',
      'author': 'Raymond Smullyan',
    },
    {
      'text':
          'A good puzzle, like a good theorem, is beautiful because it is surprising.',
      'author': 'Raymond Smullyan',
    },
    {
      'text': 'Mathematics, rightly viewed, possesses not only truth, but supreme beauty.',
      'author': 'Bertrand Russell',
    },
    {
      'text': 'The book of nature is written in the language of mathematics.',
      'author': 'Galileo Galilei',
    },
    {
      'text':
          'Without mathematics, there\'s nothing you can do. Everything around you is mathematics.',
      'author': 'Shakuntala Devi',
    },
  ];

  Map<String, String> get _todaysQuote {
    final dayOfYear = DateTime.now().difference(DateTime(DateTime.now().year)).inDays;
    return _quotes[dayOfYear % _quotes.length];
  }

  /// Resolve the stored avatar string to an emoji for display.
  String get _currentEmoji {
    if (widget.avatar == 'kiwi_default' || widget.avatar.isEmpty) return '';
    // If the avatar is stored as the emoji itself, return it directly
    return widget.avatar;
  }

  @override
  Widget build(BuildContext context) {
    final tier = KiwiTier.forGrade(widget.grade);
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;
    final quote = _todaysQuote;
    final displayName =
        widget.studentName.isNotEmpty ? widget.studentName : 'Kiwi Learner';

    // Generate avatar initials (fallback when no emoji selected)
    final initials = displayName
        .split(' ')
        .where((w) => w.isNotEmpty)
        .take(2)
        .map((w) => w[0].toUpperCase())
        .join();

    final hasEmoji = _currentEmoji.isNotEmpty;

    return Scaffold(
      backgroundColor: colors.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            children: [
              // ── Welcome header ──────────────────────────────────────────
              const SizedBox(height: 8),
              // Avatar circle — tappable to open emoji picker
              GestureDetector(
                onTap: () => setState(() => _showAvatarPicker = !_showAvatarPicker),
                child: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Container(
                      width: 84,
                      height: 84,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [colors.primary, colors.primaryDark],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: colors.primary.withOpacity(0.3),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Center(
                        child: hasEmoji
                            ? Text(
                                _currentEmoji,
                                style: const TextStyle(fontSize: 40),
                              )
                            : Text(
                                initials,
                                style: TextStyle(
                                  fontSize: 28,
                                  fontWeight: FontWeight.w800,
                                  color: Colors.white,
                                  fontFamily: typo.fontFamily,
                                ),
                              ),
                      ),
                    ),
                    // Edit badge
                    Positioned(
                      bottom: -2,
                      right: -2,
                      child: Container(
                        width: 28,
                        height: 28,
                        decoration: BoxDecoration(
                          color: KiwiColors.gemGold,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: colors.background,
                            width: 2.5,
                          ),
                        ),
                        child: const Icon(
                          Icons.edit_rounded,
                          size: 14,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Hello, $displayName!',
                style: TextStyle(
                  fontSize: typo.headlineSize + 2,
                  fontWeight: FontWeight.w800,
                  color: colors.textPrimary,
                  fontFamily: typo.fontFamily,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Grade ${widget.grade} Explorer',
                style: TextStyle(
                  fontSize: typo.bodySize,
                  color: colors.textMuted,
                  fontFamily: typo.fontFamily,
                ),
              ),

              // ── Emoji Avatar Picker ───────────────────────────────────
              if (_showAvatarPicker) ...[
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: colors.cardBg,
                    borderRadius: BorderRadius.circular(shape.cardRadius),
                    border: Border.all(color: colors.topicCardBorder, width: 1),
                    boxShadow: [
                      BoxShadow(
                        color: colors.primary.withOpacity(0.08),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            'Choose Your Avatar',
                            style: TextStyle(
                              fontSize: typo.bodySize,
                              fontWeight: FontWeight.w700,
                              color: colors.textPrimary,
                              fontFamily: typo.fontFamily,
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text('\u{2728}', style: TextStyle(fontSize: 16)), // ✨
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Tap to pick your favorite!',
                        style: TextStyle(
                          fontSize: typo.chipSize,
                          color: colors.textMuted,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                      const SizedBox(height: 14),
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 6,
                          crossAxisSpacing: 8,
                          mainAxisSpacing: 8,
                          childAspectRatio: 1,
                        ),
                        itemCount: _avatarOptions.length,
                        itemBuilder: (context, index) {
                          final option = _avatarOptions[index];
                          final emoji = option['emoji']!;
                          final isSelected = emoji == _currentEmoji;
                          return GestureDetector(
                            onTap: () {
                              widget.onAvatarChanged(emoji);
                              setState(() => _showAvatarPicker = false);
                              HapticFeedback.lightImpact();
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    'Avatar updated to ${option['label']}! $emoji',
                                  ),
                                  duration: const Duration(seconds: 2),
                                ),
                              );
                            },
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 150),
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? colors.primary.withOpacity(0.2)
                                    : colors.cardBg,
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: isSelected
                                      ? colors.primary
                                      : colors.topicCardBorder,
                                  width: isSelected ? 2 : 1,
                                ),
                              ),
                              child: Center(
                                child: Text(
                                  emoji,
                                  style: const TextStyle(fontSize: 28),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 20),

              // ── Daily Math Quote ────────────────────────────────────────
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      const Color(0xFF1A1A2E),
                      const Color(0xFF16213E),
                    ],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(shape.cardRadius),
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
                        const Text('\u{2728}',
                            style: TextStyle(fontSize: 16)),
                        const SizedBox(width: 6),
                        Text(
                          'Quote of the Day',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: Colors.white.withOpacity(0.6),
                            letterSpacing: 1.2,
                            fontFamily: typo.fontFamily,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      '"${quote['text']}"',
                      style: TextStyle(
                        fontSize: typo.bodySize + 1,
                        fontStyle: FontStyle.italic,
                        color: Colors.white.withOpacity(0.92),
                        fontFamily: typo.fontFamily,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerRight,
                      child: Text(
                        '\u{2014} ${quote['author']}',
                        style: TextStyle(
                          fontSize: typo.chipSize,
                          color: KiwiColors.gemGold.withOpacity(0.85),
                          fontWeight: FontWeight.w600,
                          fontFamily: typo.fontFamily,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── Stats grid (3x2) ─────────────────────────────────────
              Row(
                children: [
                  Expanded(
                    child: _StatCard(
                      icon: Icons.bolt_rounded,
                      value: '${widget.xpTotal}',
                      label: 'Total XP',
                      color: KiwiColors.sky,
                      tier: tier,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _StatCard(
                      icon: Icons.verified_rounded,
                      value: '${widget.topicsMastered}',
                      label: 'Topics Mastered',
                      color: KiwiColors.kiwiGreen,
                      tier: tier,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _StatCard(
                      icon: Icons.local_fire_department_rounded,
                      value: '${widget.currentStreak}',
                      label: 'Day Streak',
                      color: KiwiColors.streakWarm,
                      tier: tier,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _StatCard(
                      icon: Icons.diamond_rounded,
                      value: '${widget.totalGems}',
                      label: 'Gems',
                      color: KiwiColors.gemGold,
                      tier: tier,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _StatCard(
                      icon: Icons.monetization_on_rounded,
                      value: '${widget.kiwiCoins}',
                      label: 'Kiwi Coins',
                      color: const Color(0xFFFF6F00),
                      tier: tier,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _StatCard(
                      icon: Icons.auto_awesome_rounded,
                      value: '${widget.masteryGems}',
                      label: 'Mastery Gems',
                      color: const Color(0xFF7B1FA2),
                      tier: tier,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // ── Invite a Friend ────────────────────────────────────────
              _InviteFriendCard(
                tier: tier,
                onTap: () => _shareInvite(context),
              ),
              const SizedBox(height: 10),

              // ── Edit Profile ───────────────────────────────────────────
              _ActionTile(
                icon: Icons.edit_rounded,
                iconColor: KiwiColors.teal,
                title: 'Edit Profile',
                subtitle: 'Change name or grade',
                tier: tier,
                onTap: widget.onRestartOnboarding,
              ),
              const SizedBox(height: 10),

              // ── Sign Out ───────────────────────────────────────────────
              _ActionTile(
                icon: Icons.logout_rounded,
                iconColor: KiwiColors.coral,
                title: 'Sign Out',
                subtitle: 'Switch to a different account',
                tier: tier,
                onTap: () => _confirmSignOut(context),
              ),
              const SizedBox(height: 32),

              // ── App version ────────────────────────────────────────────
              Text(
                'Kiwimath v1.0',
                style: TextStyle(
                  fontSize: 12,
                  color: colors.textMuted.withOpacity(0.5),
                  fontFamily: typo.fontFamily,
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  void _shareInvite(BuildContext context) {
    const message =
        'Hey! I\'m learning math on Kiwimath \u{2014} it\'s like a puzzle adventure! '
        'Join me: https://kiwimath.app/invite';
    Clipboard.setData(const ClipboardData(text: message));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Invite link copied! Share it with friends.')),
    );
  }

  void _confirmSignOut(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign Out?'),
        content: const Text('Your progress is saved and will be here when you come back.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              widget.onSignOut();
            },
            child: const Text('Sign Out', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}

// =============================================================================
// Stat card
// =============================================================================
class _StatCard extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;
  final KiwiTier tier;

  const _StatCard({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
    required this.tier,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 14),
      decoration: BoxDecoration(
        color: colors.cardBg,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        border: Border.all(color: colors.topicCardBorder, width: 1),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.08),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, size: 26, color: color),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: colors.textPrimary,
              fontFamily: typo.fontFamily,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              fontSize: typo.chipSize,
              color: colors.textMuted,
              fontFamily: typo.fontFamily,
            ),
          ),
        ],
      ),
    );
  }
}

// =============================================================================
// Action tile
// =============================================================================
class _ActionTile extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String subtitle;
  final KiwiTier tier;
  final VoidCallback onTap;

  const _ActionTile({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.subtitle,
    required this.tier,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return Material(
      color: colors.cardBg,
      borderRadius: BorderRadius.circular(shape.cardRadius),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(shape.cardRadius),
            border: Border.all(color: colors.topicCardBorder, width: 1),
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, size: 22, color: iconColor),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: typo.bodySize,
                        fontWeight: FontWeight.w700,
                        color: colors.textPrimary,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontSize: typo.chipSize,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.chevron_right_rounded,
                color: colors.textMuted,
                size: 22,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// =============================================================================
// Kawaii-style invite card — fun & exciting for kids
// =============================================================================
class _InviteFriendCard extends StatelessWidget {
  final KiwiTier tier;
  final VoidCallback onTap;

  const _InviteFriendCard({required this.tier, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = tier.colors;
    final typo = tier.typography;
    final shape = tier.shape;

    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(shape.cardRadius),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(shape.cardRadius),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                const Color(0xFFFFF0F5), // lavender blush
                const Color(0xFFFFF8E7), // warm cream
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(shape.cardRadius),
            border: Border.all(
              color: const Color(0xFFFFD1DC), // soft pink border
              width: 1.5,
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFFFFB7C5).withOpacity(0.15),
                blurRadius: 10,
                offset: const Offset(0, 3),
              ),
            ],
          ),
          child: Row(
            children: [
              // Kawaii emoji cluster
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: const Color(0xFFFFE4EC).withOpacity(0.8),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Stack(
                  alignment: Alignment.center,
                  children: [
                    Positioned(
                      top: 4,
                      right: 6,
                      child: Text('\u{2728}', // ✨
                          style: TextStyle(fontSize: 12)),
                    ),
                    Text('\u{1F91D}', // 🤝
                        style: TextStyle(fontSize: 26)),
                    Positioned(
                      bottom: 4,
                      left: 6,
                      child: Text('\u{1F338}', // 🌸
                          style: TextStyle(fontSize: 10)),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text.rich(
                      TextSpan(
                        children: [
                          TextSpan(
                            text: 'Invite a Friend ',
                            style: TextStyle(
                              fontSize: typo.bodySize,
                              fontWeight: FontWeight.w700,
                              color: colors.textPrimary,
                              fontFamily: typo.fontFamily,
                            ),
                          ),
                          const TextSpan(
                            text: '\u{1F496}\u{1F31F}', // 💖🌟
                            style: TextStyle(fontSize: 14),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      'Learn together, grow together! \u{1F33B}', // 🌻
                      style: TextStyle(
                        fontSize: typo.chipSize,
                        color: colors.textMuted,
                        fontFamily: typo.fontFamily,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFD1DC).withOpacity(0.4),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.share_rounded,
                  color: Color(0xFFE75480),
                  size: 18,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
