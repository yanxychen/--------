import type { FilterCase } from './types';

export class TimeFilter {
  filter(
    cases: FilterCase[],
    maxDays: number,
    selfAuctionItemIds: string[] = []
  ): {
    passed: FilterCase[];
    filtered: FilterCase[];
  } {
    const passed: FilterCase[] = [];
    const filtered: FilterCase[] = [];
    const now = new Date();

    for (const c of cases) {
      if (selfAuctionItemIds.includes(c.itemId)) {
        passed.push(c);
        continue;
      }

      if (!c.auctionTime) {
        filtered.push(c);
        continue;
      }

      const days = this.calculateDaysAgo(c.auctionTime, now);

      if (days <= maxDays) {
        passed.push(c);
      } else {
        filtered.push(c);
      }
    }

    return { passed, filtered };
  }

  private calculateDaysAgo(timeStr: string, now: Date): number {
    const match = timeStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
    if (!match) {
      return 0;
    }

    const auctionDate = new Date(
      parseInt(match[1]),
      parseInt(match[2]) - 1,
      parseInt(match[3])
    );

    const diffMs = now.getTime() - auctionDate.getTime();
    return Math.floor(diffMs / (1000 * 60 * 60 * 24));
  }
}
