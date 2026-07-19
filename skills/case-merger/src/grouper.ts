import type { AuctionCase } from './types';
import { ADDRESS_NOISE_PATTERNS, GROUP_KEY_PATTERNS } from './constants';

export class CaseGrouper {
  private addressSimilarityThreshold: number;
  private areaTolerance: number;

  constructor(addressSimilarityThreshold: number, areaTolerance: number) {
    this.addressSimilarityThreshold = addressSimilarityThreshold;
    this.areaTolerance = areaTolerance;
  }

  group(cases: AuctionCase[]): AuctionCase[][] {
    const groups: AuctionCase[][] = [];
    const used = new Set<string>();

    for (let i = 0; i < cases.length; i++) {
      if (used.has(cases[i].itemId)) continue;

      const group: AuctionCase[] = [cases[i]];
      used.add(cases[i].itemId);

      for (let j = i + 1; j < cases.length; j++) {
        if (used.has(cases[j].itemId)) continue;

        if (this.isSameProperty(cases[i], cases[j])) {
          group.push(cases[j]);
          used.add(cases[j].itemId);
        }
      }

      groups.push(group);
    }

    return groups;
  }

  private isSameProperty(a: AuctionCase, b: AuctionCase): boolean {
    const addressSim = this.calculateAddressSimilarity(a.fullAddress, b.fullAddress);
    const areaMatch = this.isAreaMatch(a.buildingArea, b.buildingArea);

    if (addressSim >= this.addressSimilarityThreshold && areaMatch) {
      return true;
    }

    if (addressSim >= 0.9 && (!a.buildingArea || !b.buildingArea)) {
      return true;
    }

    return false;
  }

  private calculateAddressSimilarity(addr1: string, addr2: string): number {
    const norm1 = this.normalizeAddress(addr1);
    const norm2 = this.normalizeAddress(addr2);

    if (!norm1 || !norm2) return 0;
    if (norm1 === norm2) return 1;

    const core1 = this.extractCoreAddress(norm1);
    const core2 = this.extractCoreAddress(norm2);

    if (core1 && core2 && core1 === core2) {
      return 0.95;
    }

    return this.jaccardSimilarity(norm1, norm2);
  }

  private normalizeAddress(address: string): string {
    let result = address.toLowerCase().trim();

    for (const pattern of ADDRESS_NOISE_PATTERNS) {
      result = result.replace(pattern, '');
    }

    result = result.replace(/[\s,，。、；;【】\[\]()（）]/g, '');

    return result;
  }

  private extractCoreAddress(address: string): string | null {
    const communityMatch = address.match(GROUP_KEY_PATTERNS.COMMUNITY);
    const buildingMatch = address.match(GROUP_KEY_PATTERNS.BUILDING);

    if (communityMatch && buildingMatch) {
      return communityMatch[1] + buildingMatch[1];
    }

    if (communityMatch) {
      return communityMatch[1];
    }

    return null;
  }

  private isAreaMatch(area1: number, area2: number): boolean {
    if (!area1 || !area2 || area1 <= 0 || area2 <= 0) {
      return true;
    }

    const diff = Math.abs(area1 - area2);
    const avg = (area1 + area2) / 2;
    return diff / avg <= this.areaTolerance;
  }

  private jaccardSimilarity(a: string, b: string): number {
    const setA = new Set(a);
    const setB = new Set(b);

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
