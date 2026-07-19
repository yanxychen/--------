import { ADDRESS_NOISE_PATTERNS, ADDRESS_NORMALIZE_MAP } from './constants';

export class AddressMatcher {
  calculateSimilarity(addr1: string, addr2: string): number {
    const norm1 = this.normalize(addr1);
    const norm2 = this.normalize(addr2);

    if (!norm1 || !norm2) return 0;
    if (norm1 === norm2) return 1;

    const core1 = this.extractCoreAddress(norm1);
    const core2 = this.extractCoreAddress(norm2);

    if (core1 && core2 && core1 === core2) {
      return 0.95;
    }

    const jaccard = this.jaccardSimilarity(norm1, norm2);
    const levenshtein = this.levenshteinSimilarity(norm1, norm2);

    return Math.max(jaccard, levenshtein);
  }

  private normalize(address: string): string {
    let result = address.toLowerCase().trim();

    for (const pattern of ADDRESS_NOISE_PATTERNS) {
      result = result.replace(pattern, '');
    }

    for (const [from, to] of Object.entries(ADDRESS_NORMALIZE_MAP)) {
      result = result.split(from).join(to);
    }

    result = result.replace(/[\s,，。、；;【】\[\]()（）]/g, '');

    return result;
  }

  private extractCoreAddress(address: string): string | null {
    const patterns = [
      /(.+?小区.+?座)/,
      /(.+?花园.+?座)/,
      /(.+?苑.+?座)/,
      /(.+?府.+?座)/,
      /(.+?城.+?座)/,
      /(.+?庭.+?座)/,
      /(.+?公馆.+?座)/,
      /(.+?路\d+号)/,
      /(.+?街\d+号)/,
    ];

    for (const pattern of patterns) {
      const match = address.match(pattern);
      if (match) {
        return match[1];
      }
    }

    return null;
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

  private levenshteinSimilarity(a: string, b: string): number {
    const lenA = a.length;
    const lenB = b.length;

    if (lenA === 0) return lenB === 0 ? 1 : 0;
    if (lenB === 0) return 0;

    const dp: number[][] = [];
    for (let i = 0; i <= lenA; i++) {
      dp[i] = [i];
    }
    for (let j = 0; j <= lenB; j++) {
      dp[0][j] = j;
    }

    for (let i = 1; i <= lenA; i++) {
      for (let j = 1; j <= lenB; j++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        dp[i][j] = Math.min(
          dp[i - 1][j] + 1,
          dp[i][j - 1] + 1,
          dp[i - 1][j - 1] + cost
        );
      }
    }

    const maxLen = Math.max(lenA, lenB);
    return maxLen === 0 ? 1 : 1 - dp[lenA][lenB] / maxLen;
  }
}
