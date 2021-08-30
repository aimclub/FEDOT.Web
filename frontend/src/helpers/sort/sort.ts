export const sortByY = <T extends { y: number }>(value: T[]): T[] => {
  return value.sort((a, b) => {
    return b.y - a.y;
  });
};
