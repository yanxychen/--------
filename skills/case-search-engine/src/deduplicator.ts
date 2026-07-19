import type { AuctionCase, Platform } from './types';
import { DEDUP_CONFIG } from './constants';

export class Deduplicator {
  private seenIds = new Set<string>();
  private seenTitleLocation = new Map<string, AuctionCase>();

  reset() {
    this.seenIds.clear();
    this.seenTitleLocation.clear();
  }

  deduplicate(cases: AuctionCase[]): AuctionCase[] {
    const result: AuctionCase[] = [];

    for (const caseItem of cases) {
      const idKey = `${caseItem.platform}_${caseItem.itemId}`;
      if (this.seenIds.has(idKey)) {
        continue;
      }

      const tlKey = this.getTitleLocationKey(caseItem.title, caseItem.location);
      const existing = this.seenTitleLocation.get(tlKey);

      if (existing && this.isDuplicate(existing, caseItem)) {
        continue;
      }

      this.seenIds.add(idKey);
      this.seenTitleLocation.set(tlKey, caseItem);
      result.push(caseItem);
    }

    return result;
  }

  private getTitleLocationKey(title: string, location: string): string {
    const cleanTitle = this.normalize(title).slice(0, 20);
    const cleanLocation = this.normalize(location).slice(0, 20);
    return `${cleanTitle}_${cleanLocation}`;
  }

  private normalize(text: string): string {
    return text
      .toLowerCase()
      .replace(/[\s,，。、；;【】\[\]()（）]/g, '')
      .replace(/[号栋座室单元楼]/g, '');
  }

  private isDuplicate(a: AuctionCase, b: AuctionCase): boolean {
    if (a.platform === b.platform) {
      return a.itemId === b.itemId;
    }

    const titleSimilarity = this.calculateSimilarity(a.title, b.title);
    const locationSimilarity = this.calculateSimilarity(a.location, b.location);

    return (
      titleSimilarity >= DEDUP_CONFIG.titleSimilarityThreshold &&
      locationSimilarity >= DEDUP_CONFIG.locationSimilarityThreshold
    );
  }

  private calculateSimilarity(a: string, b: string): number {
    if (!a || !b) return 0;

    const setA = new Set(this.normalize(a));
    const setB = new Set(this.normalize(b));

    let intersection = 0;
    for (const char of setA) {
      if (setB.has(char)) {
        intersection++;
      }
    }

    const union = setA.size + setB.size - intersection;
    return union === 0 ? 0 : intersection / union;
  }
}
