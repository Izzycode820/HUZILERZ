/**
 * Format a number as currency in FCFA (Central African CFA Franc)
 * Uses French number formatting with spaces as thousand separators
 *
 * @param amount - The amount to format (string or number)
 * @returns Formatted currency string (e.g., "155 598")
 *
 * @example
 * formatCurrency("155598") => "155 598"
 * formatCurrency(155598.50) => "155 598.5"
 */
export function formatCurrency(amount: string | number): string {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;

  // Handle invalid numbers
  if (isNaN(numAmount)) {
    return '0';
  }

  return new Intl.NumberFormat('fr-FR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(numAmount);
}

/**
 * Format a number as currency with FCFA prefix
 *
 * @param amount - The amount to format (string or number)
 * @returns Formatted currency string with FCFA (e.g., "FCFA 155 598")
 *
 * @example
 * formatCurrencyWithSymbol("155598") => "FCFA 155 598"
 */
export function formatCurrencyWithSymbol(amount: string | number): string {
  return `FCFA ${formatCurrency(amount)}`;
}
