import 'package:flutter/material.dart';

import '../models/clan.dart';
import '../theme/kiwi_theme.dart';
import '../widgets/pixel_grid_widget.dart';
import '../widgets/guess_board_widget.dart';

/// Picture challenge screen — pixel grid puzzle + guess board.
///
/// Two tabs:
///   1. **Puzzle** — pixel grid placeholder, points breakdown, reveal bar,
///      answer submission (leader only).
///   2. **Guess Board** — collaborative guess list with input.
class PictureChallengeScreen extends StatefulWidget {
  final ChallengeInfo challenge;
  final ChallengeProgress progress;
  final List<GuessEntry> guesses;
  final bool isLeader;
  final String userUid;
  final void Function(String answer) onSubmitAnswer;
  final void Function(String guess) onSubmitGuess;
  final VoidCallback onBack;

  const PictureChallengeScreen({
    super.key,
    required this.challenge,
    required this.progress,
    required this.guesses,
    required this.isLeader,
    required this.userUid,
    required this.onSubmitAnswer,
    required this.onSubmitGuess,
    required this.onBack,
  });

  @override
  State<PictureChallengeScreen> createState() => _PictureChallengeScreenState();
}

class _PictureChallengeScreenState extends State<PictureChallengeScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;
  final _answerController = TextEditingController();
  final _guessController = TextEditingController();
  bool _isEditing = false;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
    if (widget.progress.currentAnswer != null) {
      _answerController.text = widget.progress.currentAnswer!;
    }
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _answerController.dispose();
    _guessController.dispose();
    super.dispose();
  }

  // ── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildTabBar(),
            Expanded(
              child: TabBarView(
                controller: _tabCtrl,
                children: [
                  _buildPuzzleTab(),
                  _buildGuessBoardTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Header ───────────────────────────────────────────────────────────────

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(8, 12, 16, 14),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(20)),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: widget.onBack,
            icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.challenge.title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  '${widget.challenge.puzzleType.replaceAll('_', ' ')} '
                  '\u{2022} ${widget.challenge.difficultyTier}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white.withOpacity(0.8),
                  ),
                ),
              ],
            ),
          ),
          _daysRemainingBadge(),
        ],
      ),
    );
  }

  Widget _daysRemainingBadge() {
    final days = widget.challenge.daysRemaining;
    final urgent = days <= 1;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: urgent
            ? Colors.redAccent.withOpacity(0.2)
            : Colors.white.withOpacity(0.2),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: urgent ? Colors.redAccent : Colors.white.withOpacity(0.4),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.timer_outlined,
            size: 14,
            color: urgent ? Colors.redAccent : Colors.white,
          ),
          const SizedBox(width: 4),
          Text(
            '$days day${days == 1 ? '' : 's'}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: urgent ? Colors.redAccent : Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  // ── Tab Bar ──────────────────────────────────────────────────────────────

  Widget _buildTabBar() {
    return Container(
      margin: const EdgeInsets.fromLTRB(24, 16, 24, 4),
      decoration: BoxDecoration(
        color: KiwiColors.kiwiPrimaryLight,
        borderRadius: BorderRadius.circular(14),
      ),
      child: TabBar(
        controller: _tabCtrl,
        indicator: BoxDecoration(
          color: KiwiColors.kiwiPrimary,
          borderRadius: BorderRadius.circular(14),
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        dividerColor: Colors.transparent,
        labelColor: Colors.white,
        unselectedLabelColor: KiwiColors.kiwiPrimaryDark,
        labelStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w700,
        ),
        unselectedLabelStyle: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
        tabs: const [
          Tab(text: '\u{1F9E9} Puzzle'),
          Tab(text: '\u{1F4AC} Guess Board'),
        ],
      ),
    );
  }

  // ── Puzzle Tab ───────────────────────────────────────────────────────────

  Widget _buildPuzzleTab() {
    final p = widget.progress;
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 40),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Pixel grid placeholder
          _buildPixelGridPlaceholder(),
          const SizedBox(height: 20),

          // Points breakdown
          _buildPointsBreakdown(p),
          const SizedBox(height: 20),

          // Reveal percentage bar
          _buildRevealBar(p),
          const SizedBox(height: 24),

          // Answer submission (leader only)
          if (widget.isLeader) _buildAnswerSection(p),
        ],
      ),
    );
  }

  Widget _buildPixelGridPlaceholder() {
    final p = widget.progress;
    return PixelGridWidget(
      gridRows: widget.challenge.gridRows,
      gridCols: widget.challenge.gridCols,
      blocksRevealed: p.blocksRevealed,
      blockOrder: p.blockOrder,
    );
  }

  Widget _buildPointsBreakdown(ChallengeProgress p) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Points Breakdown',
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textDark,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              _pointChip('\u{1F9E0} Brain', p.brainPoints, KiwiColors.xpPurple),
              const SizedBox(width: 10),
              _pointChip('\u{1F4DD} Quiz', p.quizPoints, KiwiColors.sky),
              const SizedBox(width: 10),
              _pointChip('\u{1F4AA} Brawn', p.brawnPoints, KiwiColors.kiwiPrimary),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              const Text(
                'Total Clan Points',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: KiwiColors.textMid,
                ),
              ),
              const Spacer(),
              Text(
                '${p.totalClanPoints}',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.kiwiPrimary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _pointChip(String label, int value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '$value',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRevealBar(ChallengeProgress p) {
    final pct = p.revealPercentage.clamp(0.0, 100.0);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                'Reveal Progress',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.textDark,
                ),
              ),
              const Spacer(),
              Text(
                '${pct.toStringAsFixed(1)}%',
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                  color: KiwiColors.kiwiPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: pct / 100,
              minHeight: 12,
              backgroundColor: KiwiColors.kiwiPrimaryLight,
              valueColor: const AlwaysStoppedAnimation(KiwiColors.kiwiPrimary),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '${p.blocksRevealed} / ${p.totalBlocks} blocks revealed',
            style: const TextStyle(
              fontSize: 12,
              color: KiwiColors.textMuted,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  // ── Answer Section (Leader Only) ─────────────────────────────────────────

  Widget _buildAnswerSection(ChallengeProgress p) {
    final hasAnswer = p.currentAnswer != null && p.currentAnswer!.isNotEmpty;
    final canSubmit = p.canSubmit;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: canSubmit
              ? KiwiColors.kiwiPrimary.withOpacity(0.3)
              : KiwiColors.textMuted.withOpacity(0.2),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.stars_rounded,
                  size: 20, color: KiwiColors.gemGold),
              const SizedBox(width: 8),
              const Text(
                'Leader Answer',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.textDark,
                ),
              ),
              const Spacer(),
              if (!canSubmit)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: KiwiColors.textMuted.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.lock_outline_rounded,
                          size: 12, color: KiwiColors.textMuted),
                      SizedBox(width: 4),
                      Text(
                        'Locked until 30% revealed',
                        style: TextStyle(
                          fontSize: 11,
                          color: KiwiColors.textMuted,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 14),

          if (!canSubmit) ...[
            // Locked state
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimaryLight.withOpacity(0.5),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                'Keep earning points to reveal more of the picture! '
                'You need at least 30% revealed before submitting an answer.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 13,
                  color: KiwiColors.textMid,
                  height: 1.4,
                ),
              ),
            ),
          ] else if (hasAnswer && !_isEditing) ...[
            // Current answer display
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: KiwiColors.kiwiGreenLight,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: KiwiColors.kiwiGreen.withOpacity(0.3),
                ),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle_rounded,
                      size: 20, color: KiwiColors.kiwiGreen),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Current Answer',
                          style: TextStyle(
                            fontSize: 11,
                            color: KiwiColors.kiwiGreenDark,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          p.currentAnswer!,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w700,
                            color: KiwiColors.kiwiGreenDark,
                          ),
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () => setState(() => _isEditing = true),
                    child: const Text(
                      'Update',
                      style: TextStyle(
                        color: KiwiColors.kiwiPrimary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            // Input field
            TextField(
              controller: _answerController,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: KiwiColors.textDark,
              ),
              decoration: InputDecoration(
                hintText: 'What do you think the picture is?',
                hintStyle: TextStyle(
                  color: KiwiColors.textMuted.withOpacity(0.6),
                ),
                filled: true,
                fillColor: KiwiColors.kiwiPrimaryLight,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 14,
                ),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: _answerController.text.trim().isNotEmpty
                    ? () {
                        widget.onSubmitAnswer(_answerController.text.trim());
                        setState(() => _isEditing = false);
                      }
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: KiwiColors.kiwiPrimary,
                  foregroundColor: Colors.white,
                  disabledBackgroundColor:
                      KiwiColors.kiwiPrimary.withOpacity(0.4),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  elevation: 0,
                ),
                child: Text(
                  hasAnswer ? 'Update Answer' : 'Submit Answer',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ── Guess Board Tab ──────────────────────────────────────────────────────

  Widget _buildGuessBoardTab() {
    return Column(
      children: [
        // Guess list
        Expanded(
          child: widget.guesses.isEmpty
              ? _buildEmptyGuessBoard()
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(24, 16, 24, 8),
                  itemCount: widget.guesses.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (_, i) =>
                      _buildGuessCard(widget.guesses[i]),
                ),
        ),
        // Input
        _buildGuessInput(),
      ],
    );
  }

  Widget _buildEmptyGuessBoard() {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Placeholder for GuessBoardWidget from widgets/guess_board_widget.dart
          Icon(Icons.chat_bubble_outline_rounded,
              size: 48, color: KiwiColors.textMuted),
          SizedBox(height: 12),
          Text(
            'No guesses yet!',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: KiwiColors.textMid,
            ),
          ),
          SizedBox(height: 4),
          Text(
            'Be the first to guess what the picture is',
            style: TextStyle(fontSize: 13, color: KiwiColors.textMuted),
          ),
        ],
      ),
    );
  }

  Widget _buildGuessCard(GuessEntry guess) {
    final isMine = guess.uid == widget.userUid;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isMine
            ? KiwiColors.kiwiPrimaryLight
            : KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: isMine
            ? Border.all(
                color: KiwiColors.kiwiPrimary.withOpacity(0.3),
                width: 1.5,
              )
            : null,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Avatar initial
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: isMine
                  ? KiwiColors.kiwiPrimary
                  : KiwiColors.xpPurple.withOpacity(0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                guess.initial,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                  color: isMine ? Colors.white : KiwiColors.xpPurple,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  guess.guessText,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: KiwiColors.textDark,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Day ${guess.dayNumber}',
                  style: const TextStyle(
                    fontSize: 11,
                    color: KiwiColors.textMuted,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuessInput() {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _guessController,
              style: const TextStyle(
                fontSize: 14,
                color: KiwiColors.textDark,
              ),
              decoration: InputDecoration(
                hintText: 'What do you think it is?',
                hintStyle: TextStyle(
                  color: KiwiColors.textMuted.withOpacity(0.6),
                ),
                filled: true,
                fillColor: KiwiColors.kiwiPrimaryLight,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 12,
                ),
              ),
              onSubmitted: (_) => _submitGuess(),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 48,
            height: 48,
            child: ElevatedButton(
              onPressed: _submitGuess,
              style: ElevatedButton.styleFrom(
                backgroundColor: KiwiColors.kiwiPrimary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(14),
                ),
                padding: EdgeInsets.zero,
                elevation: 0,
              ),
              child: const Icon(Icons.send_rounded, size: 20),
            ),
          ),
        ],
      ),
    );
  }

  void _submitGuess() {
    final text = _guessController.text.trim();
    if (text.isEmpty) return;
    widget.onSubmitGuess(text);
    _guessController.clear();
  }
}
