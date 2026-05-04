import 'package:flutter/material.dart';
import '../models/clan.dart';
import '../theme/kiwi_theme.dart';

/// Horizontal row of avatar circles representing clan members' daily activity.
///
/// Members who have practiced today show a green checkmark overlay; members who
/// haven't are dimmed. A summary label ("X/Y practiced today") sits below.
class SquadActivityBar extends StatelessWidget {
  final List<DailySquadMember> members;

  const SquadActivityBar({
    super.key,
    required this.members,
  });

  @override
  Widget build(BuildContext context) {
    final practicedCount =
        members.where((m) => m.practicedToday).length;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
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
          // --- Avatar row ---
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                for (var i = 0; i < members.length; i++) ...[
                  if (i > 0) const SizedBox(width: 10),
                  _MemberAvatar(member: members[i]),
                ],
              ],
            ),
          ),

          const SizedBox(height: 10),

          // --- Summary label ---
          Row(
            children: [
              Icon(
                practicedCount == members.length
                    ? Icons.emoji_events_rounded
                    : Icons.groups_rounded,
                size: 16,
                color: practicedCount == members.length
                    ? KiwiColors.gemGold
                    : KiwiColors.textMuted,
              ),
              const SizedBox(width: 6),
              Text(
                '$practicedCount/${members.length} practiced today',
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: KiwiColors.textMid,
                ),
              ),
              if (practicedCount == members.length) ...[
                const SizedBox(width: 6),
                const Text(
                  '\u{1F389}',
                  style: TextStyle(fontSize: 14),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Single member avatar with optional check overlay.
// ---------------------------------------------------------------------------

class _MemberAvatar extends StatelessWidget {
  final DailySquadMember member;

  const _MemberAvatar({required this.member});

  @override
  Widget build(BuildContext context) {
    const double avatarSize = 42;
    final avatarColor = _parseHexColor(member.color);

    return SizedBox(
      width: avatarSize + 4, // room for the check badge
      height: avatarSize + 4,
      child: Stack(
        children: [
          // Circle with initial
          Positioned.fill(
            child: Opacity(
              opacity: member.practicedToday ? 1.0 : 0.4,
              child: Container(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: member.practicedToday
                      ? avatarColor.withOpacity(0.15)
                      : const Color(0xFFE0E0E0),
                  border: Border.all(
                    color: member.practicedToday
                        ? avatarColor
                        : const Color(0xFFBDBDBD),
                    width: 2,
                  ),
                ),
                child: Center(
                  child: Text(
                    member.initial.toUpperCase(),
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: member.practicedToday
                          ? avatarColor
                          : KiwiColors.textMuted,
                    ),
                  ),
                ),
              ),
            ),
          ),

          // Green check badge
          if (member.practicedToday)
            Positioned(
              right: 0,
              bottom: 0,
              child: Container(
                width: 16,
                height: 16,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF4CAF50),
                  border: Border.all(
                    color: KiwiColors.cardBg,
                    width: 1.5,
                  ),
                ),
                child: const Icon(
                  Icons.check_rounded,
                  size: 10,
                  color: Colors.white,
                ),
              ),
            ),
        ],
      ),
    );
  }

  static Color _parseHexColor(String hex) {
    final cleaned = hex.replaceFirst('#', '').trim();
    if (cleaned.length == 6) {
      final value = int.tryParse('FF$cleaned', radix: 16);
      if (value != null) return Color(value);
    } else if (cleaned.length == 8) {
      final value = int.tryParse(cleaned, radix: 16);
      if (value != null) return Color(value);
    }
    return KiwiColors.kiwiPrimary;
  }
}
