/// How a book may be acquired in the Store.
///
/// All fields are optional so a title can be free, coins-only, money-only, or
/// **both** (the student chooses at checkout). A `CatalogBook` with no
/// `pricing` at all is treated as already owned (e.g. a school-issued book) and
/// never shows in the Store.
///
/// Money is stored in **minor units** (paise / cents) to avoid floating-point
/// rounding — ₹149.00 is `amountMinor: 14900, currency: 'INR'`. Coins are the
/// kiwiapp's virtual currency.
class BookPricing {
  final bool isFree;
  final int? coins;
  final int? amountMinor;
  final String? currency; // ISO-4217, e.g. 'INR', 'USD'

  const BookPricing({
    this.isFree = false,
    this.coins,
    this.amountMinor,
    this.currency,
  });

  /// Free for everyone (claimed, not paid).
  static const BookPricing free = BookPricing(isFree: true);

  bool get payableWithCoins => !isFree && (coins ?? 0) > 0;

  bool get payableWithMoney =>
      !isFree && (amountMinor ?? 0) > 0 && currency != null;

  /// True when the book must be acquired (it isn't free).
  bool get isPaid => !isFree && (payableWithCoins || payableWithMoney);

  /// A simple display string for the money price, e.g. `₹149` / `$4.99`.
  /// Hosts can replace this with locale-aware formatting.
  String? get moneyLabel {
    if (!payableWithMoney) return null;
    final symbol = _symbols[currency] ?? '$currency ';
    final whole = amountMinor! ~/ 100;
    final cents = amountMinor! % 100;
    return cents == 0
        ? '$symbol$whole'
        : '$symbol$whole.${cents.toString().padLeft(2, '0')}';
  }

  static const Map<String, String> _symbols = {
    'INR': '₹',
    'USD': r'$',
    'EUR': '€',
    'GBP': '£',
  };

  Map<String, dynamic> toJson() => {
        'isFree': isFree,
        if (coins != null) 'coins': coins,
        if (amountMinor != null) 'amountMinor': amountMinor,
        if (currency != null) 'currency': currency,
      };

  factory BookPricing.fromJson(Map<String, dynamic> j) => BookPricing(
        isFree: j['isFree'] as bool? ?? false,
        coins: (j['coins'] as num?)?.toInt(),
        amountMinor: (j['amountMinor'] as num?)?.toInt(),
        currency: j['currency'] as String?,
      );

  @override
  bool operator ==(Object other) =>
      other is BookPricing &&
      other.isFree == isFree &&
      other.coins == coins &&
      other.amountMinor == amountMinor &&
      other.currency == currency;

  @override
  int get hashCode => Object.hash(isFree, coins, amountMinor, currency);
}
