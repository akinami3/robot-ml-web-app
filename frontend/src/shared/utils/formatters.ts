export const formatPercentage = (value: number, digits = 1): string => `${(value * 100).toFixed(digits)}%`;

export const formatTimestamp = (iso: string): string => new Date(iso).toLocaleString();
