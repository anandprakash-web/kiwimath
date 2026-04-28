/// CompanionPickerScreen — onboarding step 2 where kids choose their companion.
///
/// Shows all 5 companions in a horizontal carousel with signature colors,
/// names, and roles. The kid taps one to select it, then confirms.
library;

import 'package:flutter/material.dart';
import '../models/companion.dart';
import '../services/companion_service.dart';
import '../widgets/companion_view.dart';

class CompanionPickerScreen extends StatefulWidget {
  final CompanionService companionService;
  final VoidCallback onComplete;

  const CompanionPickerScreen({
    super.key,
    required this.companionService,
    required this.onComplete,
  });

  @override
  State<CompanionPickerScreen> createState() => _CompanionPickerScreenState();
}

class _CompanionPickerScreenState extends State<CompanionPickerScreen>
    with SingleTickerProviderStateMixin {
  CompanionId? _selectedId;
  bool _isChoosing = false;
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _onConfirm() async {
    if (_selectedId == null) return;
    setState(() => _isChoosing = true);

    final success = await widget.companionService.choosePrimary(_selectedId!);
    if (!mounted) return;

    if (success) {
      widget.onComplete();
    } else {
      setState(() => _isChoosing = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Could not choose that companion. Try again!'),
          backgroundColor: Colors.orange.shade700,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final config = widget.companionService.config;
    if (config == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFF0FFF0), Color(0xFFE8F5E9), Color(0xFFDCEDC8)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              const SizedBox(height: 32),

              // Title
              const Text(
                'Choose your companion!',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF2E7D32),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'They’ll help you on your math adventure',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFF558B2F),
                ),
              ),

              const SizedBox(height: 32),

              // Companion grid
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: GridView.builder(
                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      childAspectRatio: 0.85,
                      mainAxisSpacing: 12,
                      crossAxisSpacing: 12,
                    ),
                    itemCount: config.cast.length,
                    itemBuilder: (context, index) {
                      final companion = config.cast[index];
                      final isSelected = _selectedId == companion.id;
                      final isShipped = companion.shipped;

                      return GestureDetector(
                        onTap: isShipped
                            ? () => setState(() => _selectedId = companion.id)
                            : null,
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
                          curve: Curves.easeOut,
                          decoration: BoxDecoration(
                            color: isSelected
                                ? companion.signatureColorSoft
                                : Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: isSelected
                                  ? companion.signatureColor
                                  : Colors.grey.shade200,
                              width: isSelected ? 3 : 1.5,
                            ),
                            boxShadow: isSelected
                                ? [
                                    BoxShadow(
                                      color: companion.signatureColor
                                          .withValues(alpha: 0.3),
                                      blurRadius: 16,
                                      spreadRadius: 2,
                                    ),
                                  ]
                                : [
                                    BoxShadow(
                                      color: Colors.black.withValues(alpha: 0.05),
                                      blurRadius: 8,
                                      offset: const Offset(0, 2),
                                    ),
                                  ],
                          ),
                          child: Opacity(
                            opacity: isShipped ? 1.0 : 0.4,
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                // Companion avatar
                                CompanionView(
                                  surface: CompanionSurface.onboardingStep2Picker,
                                  config: config,
                                  size: 64,
                                ),
                                const SizedBox(height: 10),

                                // Name
                                Text(
                                  companion.name,
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w700,
                                    color: companion.signatureColorText,
                                  ),
                                ),
                                const SizedBox(height: 4),

                                // Role
                                Text(
                                  _roleLabel(companion.role),
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: companion.signatureColorText
                                        .withValues(alpha: 0.7),
                                  ),
                                ),

                                // "Coming soon" for unshipped
                                if (!isShipped) ...[
                                  const SizedBox(height: 6),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: Colors.grey.shade200,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: const Text(
                                      'Coming soon',
                                      style: TextStyle(
                                        fontSize: 9,
                                        color: Colors.grey,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ),

              // Confirm button
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                child: SizedBox(
                  width: double.infinity,
                  child: AnimatedBuilder(
                    animation: _pulseController,
                    builder: (context, child) {
                      final scale = _selectedId != null
                          ? 1.0 + (_pulseController.value * 0.02)
                          : 1.0;
                      return Transform.scale(scale: scale, child: child);
                    },
                    child: ElevatedButton(
                      onPressed:
                          _selectedId != null && !_isChoosing ? _onConfirm : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: _selectedId != null
                            ? config.cast
                                .firstWhere((c) => c.id == _selectedId)
                                .signatureColor
                            : Colors.grey.shade300,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        elevation: _selectedId != null ? 4 : 0,
                        textStyle: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: _isChoosing
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Text(_selectedId != null
                              ? 'Choose ${config.cast.firstWhere((c) => c.id == _selectedId).name}!'
                              : 'Tap a companion to choose'),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _roleLabel(String role) {
    switch (role) {
      case 'curious_explorer':
        return 'Curious Explorer';
      case 'careful_checker':
        return 'Careful Checker';
      case 'quiet_thinker':
        return 'Quiet Thinker';
      case 'spark':
        return 'Celebration Spark';
      case 'organiser':
        return 'Step Organiser';
      default:
        return role;
    }
  }
}
