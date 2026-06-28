import '../util/equality.dart';
import 'enums.dart';
import 'selectors.dart';

/// A redundant, layered anchor — the heart of the design.
///
/// Three independent ways to find the same span are stored together so the
/// [AnchorResolver] can degrade gracefully:
///   1. [structural] — fast, exact, brittle.
///   2. [quote]      — reflow-proof, the workhorse.
///   3. [position]   — disambiguates repeats / last resort.
class Anchor {
  final String sectionId;
  final StructuralSelector? structural;
  final TextQuoteSelector? quote;
  final TextPositionSelector? position;
  final AnchorState state;

  const Anchor({
    required this.sectionId,
    this.structural,
    this.quote,
    this.position,
    this.state = AnchorState.resolved,
  });

  Anchor copyWith({
    String? sectionId,
    StructuralSelector? structural,
    TextQuoteSelector? quote,
    TextPositionSelector? position,
    AnchorState? state,
  }) =>
      Anchor(
        sectionId: sectionId ?? this.sectionId,
        structural: structural ?? this.structural,
        quote: quote ?? this.quote,
        position: position ?? this.position,
        state: state ?? this.state,
      );

  Map<String, dynamic> toJson() => {
        'sectionId': sectionId,
        if (structural != null) 'structural': structural!.toJson(),
        if (quote != null) 'quote': quote!.toJson(),
        if (position != null) 'position': position!.toJson(),
        'state': state.name,
      };

  factory Anchor.fromJson(Map<String, dynamic> j) => Anchor(
        sectionId: j['sectionId'] as String,
        structural: j['structural'] == null
            ? null
            : StructuralSelector.fromJson(
                Map<String, dynamic>.from(j['structural'] as Map)),
        quote: j['quote'] == null
            ? null
            : TextQuoteSelector.fromJson(
                Map<String, dynamic>.from(j['quote'] as Map)),
        position: j['position'] == null
            ? null
            : TextPositionSelector.fromJson(
                Map<String, dynamic>.from(j['position'] as Map)),
        state: j['state'] == null
            ? AnchorState.resolved
            : AnchorState.values.byName(j['state'] as String),
      );

  @override
  bool operator ==(Object other) =>
      other is Anchor && deepEquals(toJson(), other.toJson());
  @override
  int get hashCode =>
      Object.hash(sectionId, state, quote?.exact, position?.start);
}
