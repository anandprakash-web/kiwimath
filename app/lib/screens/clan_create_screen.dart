import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/kiwi_theme.dart';
import '../models/clan.dart';

/// Parent-gated clan creation flow.
///
/// 1. Parent gate — simple multiplication question.
/// 2. Clan name input with validation.
/// 3. Crest shape picker (6 emojis).
/// 4. Crest colour picker (8 colours).
/// 5. Live preview + "Create Clan!" button.
class ClanCreateScreen extends StatefulWidget {
  final int grade;
  final String leaderUid;
  final void Function(String name, String crestShape, String crestColor)
      onCreate;
  final VoidCallback onBack;

  const ClanCreateScreen({
    super.key,
    required this.grade,
    required this.leaderUid,
    required this.onCreate,
    required this.onBack,
  });

  @override
  State<ClanCreateScreen> createState() => _ClanCreateScreenState();
}

class _ClanCreateScreenState extends State<ClanCreateScreen> {
  // ---- parent gate ----
  bool _gateUnlocked = false;
  late int _gateA;
  late int _gateB;
  final _gateController = TextEditingController();
  String? _gateError;

  // ---- creation form ----
  final _nameController = TextEditingController();
  String? _nameError;
  String _selectedShape = 'bolt';
  String _selectedColor = '#FF6D00';

  static const _shapes = <String, String>{
    'bolt': '⚡',
    'lion': '\u{1F981}',
    'wave': '\u{1F30A}',
    'rocket': '\u{1F680}',
    'blossom': '\u{1F338}',
    'dolphin': '\u{1F42C}',
  };

  static const _colors = <String>[
    '#FF6D00',
    '#7C4DFF',
    '#448AFF',
    '#FF4081',
    '#00E5FF',
    '#76FF03',
    '#FFD600',
    '#FF8A65',
  ];

  @override
  void initState() {
    super.initState();
    _generateGateQuestion();
  }

  void _generateGateQuestion() {
    final rng = Random();
    _gateA = rng.nextInt(5) + 5; // 5-9
    _gateB = rng.nextInt(5) + 4; // 4-8
  }

  @override
  void dispose() {
    _gateController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Validators
  // ---------------------------------------------------------------------------

  void _checkGate() {
    final answer = int.tryParse(_gateController.text.trim());
    if (answer == null) {
      setState(() => _gateError = 'Type a number!');
      return;
    }
    if (answer != _gateA * _gateB) {
      setState(() => _gateError = 'Hmm, not quite. Try again!');
      return;
    }
    setState(() {
      _gateError = null;
      _gateUnlocked = true;
    });
  }

  String? _validateName(String name) {
    if (name.trim().isEmpty) return 'Your clan needs a name!';
    if (name.trim().length < 3) return 'At least 3 characters, please.';
    if (name.trim().length > 20) return '20 characters max.';
    return null;
  }

  void _submit() {
    final error = _validateName(_nameController.text);
    if (error != null) {
      setState(() => _nameError = error);
      return;
    }
    setState(() => _nameError = null);
    widget.onCreate(
      _nameController.text.trim(),
      _selectedShape,
      _selectedColor,
    );
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: KiwiColors.cream,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: KiwiColors.textDark),
          onPressed: widget.onBack,
        ),
        title: const Text(
          'Create Your Clan',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: KiwiColors.textDark,
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: _gateUnlocked ? _buildCreationForm() : _buildParentGate(),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Parent Gate
  // ---------------------------------------------------------------------------

  Widget _buildParentGate() {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Illustration / emoji
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: KiwiColors.kiwiPrimaryLight,
                borderRadius: BorderRadius.circular(24),
              ),
              alignment: Alignment.center,
              child: const Text('\u{1F512}', style: TextStyle(fontSize: 40)),
            ),
            const SizedBox(height: 20),
            const Text(
              'Ask Your Parent!',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: KiwiColors.textDark,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'A grown-up needs to answer this\nquestion before you can create a clan.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: KiwiColors.textMid,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 28),
            // Question card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: KiwiColors.cardBg,
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.06),
                    blurRadius: 10,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Text(
                    'What is $_gateA × $_gateB?',
                    style: const TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.w900,
                      color: KiwiColors.textDark,
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _gateController,
                    keyboardType: TextInputType.number,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: KiwiColors.textDark,
                    ),
                    decoration: InputDecoration(
                      hintText: '?',
                      hintStyle: const TextStyle(color: KiwiColors.textMuted),
                      filled: true,
                      fillColor: KiwiColors.kiwiPrimaryLight,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        vertical: 14,
                        horizontal: 16,
                      ),
                      errorText: _gateError,
                    ),
                    onSubmitted: (_) => _checkGate(),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _checkGate,
                style: ElevatedButton.styleFrom(
                  backgroundColor: KiwiColors.kiwiPrimary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                  elevation: 0,
                ),
                child: const Text(
                  'Check Answer',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Creation Form
  // ---------------------------------------------------------------------------

  Widget _buildCreationForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ---- Clan Name ----
          const _SectionLabel(text: 'Clan Name'),
          const SizedBox(height: 8),
          TextField(
            controller: _nameController,
            maxLength: 20,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: KiwiColors.textDark,
            ),
            onChanged: (_) {
              if (_nameError != null) setState(() => _nameError = null);
            },
            decoration: InputDecoration(
              hintText: 'e.g. The Math Wizards',
              hintStyle: const TextStyle(color: KiwiColors.textMuted),
              filled: true,
              fillColor: KiwiColors.cardBg,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide(
                  color: KiwiColors.kiwiPrimary.withOpacity(0.3),
                ),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide(
                  color: KiwiColors.kiwiPrimary.withOpacity(0.2),
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: const BorderSide(
                  color: KiwiColors.kiwiPrimary,
                  width: 2,
                ),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 14,
              ),
              errorText: _nameError,
            ),
          ),
          const SizedBox(height: 20),

          // ---- Crest Picker ----
          const _SectionLabel(text: 'Pick a Crest'),
          const SizedBox(height: 10),
          _buildCrestGrid(),
          const SizedBox(height: 24),

          // ---- Colour Picker ----
          const _SectionLabel(text: 'Pick a Colour'),
          const SizedBox(height: 10),
          _buildColorRow(),
          const SizedBox(height: 28),

          // ---- Preview ----
          const _SectionLabel(text: 'Preview'),
          const SizedBox(height: 10),
          _buildPreview(),
          const SizedBox(height: 28),

          // ---- Create Button ----
          SizedBox(
            width: double.infinity,
            height: 56,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [KiwiColors.kiwiPrimary, KiwiColors.kiwiPrimaryDark],
                ),
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: KiwiColors.kiwiPrimary.withOpacity(0.35),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: ElevatedButton(
                onPressed: _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text(
                  'Create Clan! \u{1F389}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Crest Grid (6 shapes, 2 rows x 3 cols)
  // ---------------------------------------------------------------------------

  Widget _buildCrestGrid() {
    final entries = _shapes.entries.toList();
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 1.3,
      ),
      itemCount: entries.length,
      itemBuilder: (_, i) {
        final key = entries[i].key;
        final emoji = entries[i].value;
        final selected = key == _selectedShape;
        return GestureDetector(
          onTap: () => setState(() => _selectedShape = key),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              color: selected
                  ? KiwiColors.kiwiPrimaryLight
                  : KiwiColors.cardBg,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: selected
                    ? KiwiColors.kiwiPrimary
                    : Colors.grey.shade200,
                width: selected ? 2.5 : 1,
              ),
              boxShadow: selected
                  ? [
                      BoxShadow(
                        color: KiwiColors.kiwiPrimary.withOpacity(0.2),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ]
                  : [],
            ),
            alignment: Alignment.center,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(emoji, style: const TextStyle(fontSize: 28)),
                const SizedBox(height: 2),
                Text(
                  key[0].toUpperCase() + key.substring(1),
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: selected
                        ? KiwiColors.kiwiPrimaryDark
                        : KiwiColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Colour Picker Row
  // ---------------------------------------------------------------------------

  Widget _buildColorRow() {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: _colors.map((hex) {
        final color = _hexToColor(hex);
        final selected = hex == _selectedColor;
        return GestureDetector(
          onTap: () => setState(() => _selectedColor = hex),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              border: Border.all(
                color: selected ? KiwiColors.textDark : Colors.transparent,
                width: selected ? 3 : 0,
              ),
              boxShadow: selected
                  ? [
                      BoxShadow(
                        color: color.withOpacity(0.4),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ]
                  : [],
            ),
            child: selected
                ? const Icon(Icons.check_rounded, color: Colors.white, size: 20)
                : null,
          ),
        );
      }).toList(),
    );
  }

  // ---------------------------------------------------------------------------
  // Live Preview
  // ---------------------------------------------------------------------------

  Widget _buildPreview() {
    final emoji = _shapes[_selectedShape] ?? '⚡';
    final bgColor = _hexToColor(_selectedColor);
    final name = _nameController.text.trim().isEmpty
        ? 'Your Clan'
        : _nameController.text.trim();

    return Center(
      child: Column(
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: bgColor,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: bgColor.withOpacity(0.35),
                  blurRadius: 14,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Text(emoji, style: const TextStyle(fontSize: 38)),
          ),
          const SizedBox(height: 10),
          Text(
            name,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: KiwiColors.textDark,
            ),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Util
  // ---------------------------------------------------------------------------

  static Color _hexToColor(String hex) {
    final cleaned = hex.replaceAll('#', '');
    return Color(int.parse('FF$cleaned', radix: 16));
  }
}

// =============================================================================
// Small reusable section label
// =============================================================================

class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel({required this.text});

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w800,
        color: KiwiColors.textDark,
      ),
    );
  }
}
