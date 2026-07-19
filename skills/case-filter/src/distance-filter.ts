import type { FilterCase } from './types';

export class DistanceFilter {
  filter(
    cases: FilterCase[],
    threshold: number,
    mode: 'rough' | 'fine' = 'fine',
    selfAuctionItemIds: string[] = []
  ): {
    passed: FilterCase[];
    filtered: FilterCase[];
  } {
    const passed: FilterCase[] = [];
    const filtered: FilterCase[] = [];

    for (const c of cases) {
      if (selfAuctionItemIds.includes(c.itemId)) {
        passed.push(c);
        continue;
      }

      const distance = mode === 'fine'
        ? c.drivingDistance ?? c.straightDistance
        : c.straightDistance ?? c.drivingDistance;

      if (distance === undefined || distance === null) {
        filtered.push(c);
        continue;
      }

      if (distance <= threshold) {
        passed.push(c);
      } else {
        filtered.push(c);
      }
    }

    return { passed, filtered };
  }
}
