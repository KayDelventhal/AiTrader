export const euro = (value: string | number) => new Intl.NumberFormat('en-IE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }).format(Number(value))
export const pct = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
export const date = (value: string | number) => new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Europe/Berlin' }).format(typeof value === 'number' ? value * 1000 : new Date(value))
