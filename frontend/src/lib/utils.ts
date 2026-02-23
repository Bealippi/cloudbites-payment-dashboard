import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(amount: number, currency: string): string {
  const map: Record<string, string> = {
    USD: 'en-US', EUR: 'de-DE', BRL: 'pt-BR', MXN: 'es-MX', COP: 'es-CO',
  };
  return new Intl.NumberFormat(map[currency] || 'en-US', {
    style: 'currency',
    currency,
  }).format(amount);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

export function formatDateFull(iso: string): string {
  return new Date(iso).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

export const STATUS_COLORS: Record<string, string> = {
  SUCCEEDED: 'bg-green-100 text-green-800',
  PENDING: 'bg-yellow-100 text-yellow-800',
  DECLINED: 'bg-red-100 text-red-800',
  ERROR: 'bg-red-100 text-red-800',
  REFUNDED: 'bg-purple-100 text-purple-800',
  CANCELED: 'bg-gray-100 text-gray-600',
  EXPIRED: 'bg-gray-100 text-gray-600',
  AUTHORIZED: 'bg-blue-100 text-blue-800',
  NOT_FOUND: 'bg-red-100 text-red-800',
};

export const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'bg-red-600 text-white',
  HIGH: 'bg-orange-500 text-white',
  MEDIUM: 'bg-yellow-400 text-yellow-900',
  LOW: 'bg-gray-300 text-gray-700',
};

export const SEVERITY_BORDER: Record<string, string> = {
  CRITICAL: 'border-l-4 border-l-red-500',
  HIGH: 'border-l-4 border-l-orange-400',
  MEDIUM: 'border-l-4 border-l-yellow-400',
};
