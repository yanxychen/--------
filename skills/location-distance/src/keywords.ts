import type { KeywordExtractionResult } from './types';
import { ADDRESS_SUFFIXES } from './constants';

export class KeywordExtractor {
  extract(address: string): KeywordExtractionResult {
    const cleanAddr = this.cleanAddress(address);

    const city = this.extractCity(cleanAddr);
    const district = this.extractDistrict(cleanAddr);
    const community = this.extractCommunity(cleanAddr);
    const fullCommunity = this.extractFullCommunity(cleanAddr);
    const business = this.extractBusiness(cleanAddr);

    const keywords: string[] = [];

    if (fullCommunity && fullCommunity !== community) {
      keywords.push(fullCommunity);
    }
    if (community) {
      keywords.push(community);
    }
    if (business) {
      keywords.push(business);
    }
    if (district) {
      keywords.push(district);
    }
    if (city) {
      keywords.push(city);
    }

    const uniqueKeywords = [...new Set(keywords.filter(k => k.length >= 2))];

    return {
      keywords: uniqueKeywords,
      levels: {
        fullCommunity,
        community,
        business,
        district,
        city,
      },
    };
  }

  private cleanAddress(address: string): string {
    return address
      .replace(/[\s,，。、；;]/g, '')
      .replace(/^[A-Za-z0-9\-]+号?/, '');
  }

  private extractCity(address: string): string {
    const match = address.match(/(.+?市)/);
    return match?.[1] || '';
  }

  private extractDistrict(address: string): string {
    const match = address.match(/(.+?[区县])/);
    if (!match) return '';

    let result = match[1];
    const cityMatch = address.match(/(.+?市)/);
    if (cityMatch && result.startsWith(cityMatch[1])) {
      result = result.replace(cityMatch[1], '');
    }
    return result;
  }

  private extractCommunity(address: string): string {
    const suffixes = ADDRESS_SUFFIXES.COMMUNITY;

    for (const suffix of suffixes) {
      const regex = new RegExp(`([\u4e00-\u9fa5\\d]{2,20}${suffix})`);
      const match = address.match(regex);
      if (match) {
        return match[1];
      }
    }

    return '';
  }

  private extractFullCommunity(address: string): string {
    const community = this.extractCommunity(address);
    if (!community) return '';

    const buildingRegex = new RegExp(`${community}[\\d\\-]+[栋座号楼]?`);
    const match = address.match(buildingRegex);
    if (match) {
      return match[0];
    }

    return community;
  }

  private extractBusiness(address: string): string {
    const roadPattern = /([\u4e00-\u9fa5]{2,10}[路街道])/g;
    const matches = address.match(roadPattern);
    if (matches && matches.length > 0) {
      return matches[0];
    }
    return '';
  }
}
