import { useMaskingStore } from '@/stores/masking'

/**
 * Composable for data masking in viewer components.
 * Provides a reactive `maskValue(key, value)` helper that returns
 * the masked string when a rule matches, or the original value otherwise.
 */
export function useDataMasking() {
  const maskingStore = useMaskingStore()

  function maskValue(key: string, value: string): string {
    const maskChar = maskingStore.getMask(key)
    if (!maskChar) return value
    // Replace all characters with the mask char
    return maskChar.repeat(Math.min(value.length, 20)) + (value.length > 20 ? '...' : '')
  }

  function isMasked(key: string): boolean {
    return maskingStore.isMasked(key)
  }

  return { maskValue, isMasked, maskingStore }
}
