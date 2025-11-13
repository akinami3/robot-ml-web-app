export const ensurePositive = (value: number, label: string): number => {
  if (value < 0) {
    throw new Error(`${label} must be greater than or equal to 0`);
  }
  return value;
};
