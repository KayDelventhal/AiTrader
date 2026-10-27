export const horizonLabels = {
  intraday: 'Intraday',
  days_weeks: 'Days to weeks',
  weeks_months: 'Weeks to months',
} as const

export function horizonLabel(value?: string | null) {
  return value && value in horizonLabels ? horizonLabels[value as keyof typeof horizonLabels] : 'Unspecified in this older run'
}
