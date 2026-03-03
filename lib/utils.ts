import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toLocaleString()
}

export function formatMonth(month: string): string {
  const [year, monthNum] = month.split('-')
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${months[parseInt(monthNum) - 1]} ${year}`
}

export function getMonthRange(months: string[]): string {
  if (months.length === 0) return ''
  const first = formatMonth(months[0])
  const last = formatMonth(months[months.length - 1])
  return `${first} - ${last}`
}
