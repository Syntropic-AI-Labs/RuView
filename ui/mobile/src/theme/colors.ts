// Syntropic Sense Design System Palette (Healthcare & Calming Ambient Care)
// Primary: Deep Slate & Indigo (#0F172A, #1E293B)
// Accents: Calming Sage & Emerald Teal (#0D9488, #14B8A6, #10B981)
// Alerts: Clear Amber Warning (#F59E0B) and Rose Red Emergency (#EF4444)

export const palette = {
  bg: '#0F172A',
  surface: '#1E293B',
  surfaceAlt: '#334155',
  border: '#334155',
  accent: '#0D9488',
  accentDim: '#115E59',
  accentGlow: '#14B8A6',
  textPrimary: '#F8FAFC',
  textSecondary: '#94A3B8',
  connected: '#10B981',
  disconnected: '#EF4444',
  signalHigh: '#EF4444',
  signalMid: '#10B981',
  signalLow: '#3B82F6',
  simulated: '#F59E0B',
  success: '#10B981',
  warn: '#F59E0B',
  danger: '#EF4444',
  muted: '#64748B',
} as const;

export const darkTheme = {
  bg: '#0F172A',
  surface: '#1E293B',
  surfaceAlt: '#334155',
  border: '#334155',
  textPrimary: '#F8FAFC',
  textSecondary: '#94A3B8',
  accent: '#0D9488',
  accentDim: '#115E59',
  accentGlow: '#14B8A6',
  connected: '#10B981',
  disconnected: '#EF4444',
  signalHigh: '#EF4444',
  signalMid: '#10B981',
  signalLow: '#3B82F6',
  simulated: '#F59E0B',
  success: '#10B981',
  warn: '#F59E0B',
  danger: '#EF4444',
  muted: '#64748B',
} as const;

export const lightTheme = {
  bg: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceAlt: '#F1F5F9',
  border: '#E2E8F0',
  textPrimary: '#0F172A',
  textSecondary: '#475569',
  accent: '#0D9488',
  accentDim: '#CCFBF1',
  accentGlow: '#14B8A6',
  connected: '#059669',
  disconnected: '#DC2626',
  signalHigh: '#DC2626',
  signalMid: '#059669',
  signalLow: '#2563EB',
  simulated: '#D97706',
  success: '#059669',
  warn: '#D97706',
  danger: '#DC2626',
  muted: '#94A3B8',
} as const;

export type ThemeColors = typeof darkTheme;
