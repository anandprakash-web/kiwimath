import 'package:flutter/material.dart';
import '../models/clan.dart';
import '../theme/kiwi_theme.dart';

/// Clan guess board for Picture Unravel challenges.
///
/// Displays past guesses (newest first) and an input row for submitting a new
/// guess. Submission is gated by [canSubmit] (one guess per day).
class GuessBoardWidget extends StatefulWidget {
  final List<GuessEntry> guesses;
  final bool canSubmit;
  final ValueChanged<String> onSubmitGuess;

  const GuessBoardWidget({
    super.key,
    required this.guesses,
    required this.canSubmit,
    required this.onSubmitGuess,
  });

  @override
  State<GuessBoardWidget> createState() => _GuessBoardWidgetState();
}

class _GuessBoardWidgetState extends State<GuessBoardWidget> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  static const int _maxChars = 60;

  bool get _hasText => _controller.text.trim().isNotEmpty;

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _handleSubmit() {
    final text = _controller.text.trim();
    if (text.isEmpty || !widget.canSubmit) return;
    widget.onSubmitGuess(text);
    _controller.clear();
    _focusNode.unfocus();
  }

  @override
  Widget build(BuildContext context) {
    // Sort guesses newest-first.
    final sorted = List<GuessEntry>.from(widget.guesses)
      ..sort((a, b) => b.dayNumber.compareTo(a.dayNumber));

    return Container(
      decoration: BoxDecoration(
        color: KiwiColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // --- Header ---
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 0),
            child: Row(
              children: [
                const Icon(
                  Icons.lightbulb_rounded,
                  size: 18,
                  color: KiwiColors.gemGold,
                ),
                const SizedBox(width: 6),
                const Text(
                  'Guess Board',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: KiwiColors.textDark,
                  ),
                ),
                const Spacer(),
                Text(
                  '${sorted.length} guess${sorted.length == 1 ? '' : 'es'}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ],
            ),
          ),

          const Divider(height: 20, indent: 16, endIndent: 16),

          // --- Guess list ---
          if (sorted.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Text(
                'No guesses yet. Be the first!',
                style: TextStyle(
                  fontSize: 13,
                  fontStyle: FontStyle.italic,
                  color: KiwiColors.textMuted,
                ),
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: sorted.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, index) => _GuessRow(entry: sorted[index]),
            ),

          const SizedBox(height: 8),

          // --- Input area ---
          Container(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 14),
            decoration: const BoxDecoration(
              color: KiwiColors.cream,
              borderRadius: BorderRadius.vertical(
                bottom: Radius.circular(14),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    // Text field
                    Expanded(
                      child: Container(
                        height: 42,
                        decoration: BoxDecoration(
                          color: KiwiColors.cardBg,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: widget.canSubmit
                                ? KiwiColors.kiwiPrimary
                                    .withOpacity(0.3)
                                : const Color(0xFFE0E0E0),
                            width: 1.2,
                          ),
                        ),
                        child: TextField(
                          controller: _controller,
                          focusNode: _focusNode,
                          enabled: widget.canSubmit,
                          maxLength: _maxChars,
                          maxLines: 1,
                          textInputAction: TextInputAction.send,
                          onSubmitted: (_) => _handleSubmit(),
                          onChanged: (_) => setState(() {}),
                          style: const TextStyle(
                            fontSize: 14,
                            color: KiwiColors.textDark,
                          ),
                          decoration: InputDecoration(
                            hintText: widget.canSubmit
                                ? 'What do you think it is?'
                                : 'Already guessed today',
                            hintStyle: const TextStyle(
                              fontSize: 13,
                              color: KiwiColors.textMuted,
                            ),
                            counterText: '',
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 10,
                            ),
                          ),
                        ),
                      ),
                    ),

                    const SizedBox(width: 8),

                    // Submit button
                    Material(
                      color: widget.canSubmit && _hasText
                          ? KiwiColors.kiwiPrimary
                          : const Color(0xFFE0E0E0),
                      borderRadius: BorderRadius.circular(12),
                      child: InkWell(
                        onTap: widget.canSubmit && _hasText
                            ? _handleSubmit
                            : null,
                        borderRadius: BorderRadius.circular(12),
                        child: SizedBox(
                          width: 42,
                          height: 42,
                          child: Icon(
                            Icons.send_rounded,
                            size: 20,
                            color: widget.canSubmit && _hasText
                                ? Colors.white
                                : KiwiColors.textMuted,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 6),

                // Helper text
                Row(
                  children: [
                    Icon(
                      Icons.info_outline_rounded,
                      size: 12,
                      color: KiwiColors.textMuted.withOpacity(0.7),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '1 guess per day  •  $_maxChars chars max',
                      style: TextStyle(
                        fontSize: 11,
                        color:
                            KiwiColors.textMuted.withOpacity(0.7),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Single guess row
// ---------------------------------------------------------------------------

class _GuessRow extends StatelessWidget {
  final GuessEntry entry;

  const _GuessRow({required this.entry});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: KiwiColors.cream,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Member initial avatar
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: KiwiColors.kiwiPrimaryLight,
              border: Border.all(
                color: KiwiColors.kiwiPrimary.withOpacity(0.3),
                width: 1.5,
              ),
            ),
            child: Center(
              child: Text(
                entry.initial.toUpperCase(),
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: KiwiColors.kiwiPrimaryDark,
                ),
              ),
            ),
          ),

          const SizedBox(width: 10),

          // Guess text
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  entry.guessText,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                    color: KiwiColors.textDark,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  entry.submittedAt,
                  style: const TextStyle(
                    fontSize: 11,
                    color: KiwiColors.textMuted,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(width: 8),

          // Day number badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: KiwiColors.xpPurple.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Day ${entry.dayNumber}',
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w700,
                color: KiwiColors.xpPurple,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
