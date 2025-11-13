export const log = (...args: unknown[]): void => {
  if (import.meta.env.DEV) {
    console.debug("[robot-ml]", ...args);
  }
};
