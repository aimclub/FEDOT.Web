export const cl = (
  ...classes: Array<string | boolean | undefined | null>
): string => classes.map((item) => item || undefined).join(" ");
