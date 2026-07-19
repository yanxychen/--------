import type { EnrichedCase, AuctionCase, Platform } from './types';
import { DataExtractor } from './data-extractor';
import { PRICE_TYPE_DEFAULT, AUCTION_ROUNDS } from './constants';

export abstract class BaseEnricher {
  protected platform: Platform;
  protected extractor: DataExtractor;

  constructor(platform: Platform) {
    this.platform = platform;
    this.extractor = new DataExtractor();
  }

  abstract enrich(caseItem: AuctionCase, page?: any): Promise<EnrichedCase>;

  protected createEnrichedCase(
    baseCase: AuctionCase,
    data: Partial<EnrichedCase>
  ): EnrichedCase {
    const buildingArea = data.buildingArea || 0;
    const marketValue = data.marketValue || baseCase.currentPrice / 10000;
    const unitPrice = this.extractor.calculateUnitPrice(marketValue, buildingArea);

    return {
      ...baseCase,
      fullAddress: data.fullAddress || baseCase.location,
      buildingArea,
      landArea: data.landArea,
      marketValue,
      unitPrice,
      startPrice: data.startPrice || baseCase.currentPrice,
      auctionTime: data.auctionTime || '',
      auctionStatus: data.auctionStatus || baseCase.auctionStatus || '即将开始',
      auctionRound: data.auctionRound || this.detectRound(baseCase.title),
      priceType: data.priceType || PRICE_TYPE_DEFAULT,
      bidCount: data.bidCount,
      court: data.court,
      endTime: data.endTime,
      assessmentPrice: data.assessmentPrice,
    };
  }

  protected detectRound(title: string): string {
    if (/二拍|第二次|再次拍卖/.test(title)) return AUCTION_ROUNDS.SECOND;
    if (/变卖/.test(title)) return AUCTION_ROUNDS.SALE;
    return AUCTION_ROUNDS.FIRST;
  }

  protected extractFromHtml(html: string): Partial<EnrichedCase> {
    const result: Partial<EnrichedCase> = {};

    const cleanText = html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();

    const area = this.extractor.extractArea(cleanText);
    if (area) result.buildingArea = area;

    const date = this.extractor.extractDate(cleanText);
    if (date) result.auctionTime = date;

    const startPrice = this.extractor.extractPrice(cleanText, 'start');
    if (startPrice) {
      result.startPrice = startPrice;
      result.marketValue = startPrice / 10000;
    }

    const status = this.extractor.extractAuctionStatus(cleanText);
    if (status) result.auctionStatus = status;

    const round = this.extractor.extractAuctionRound(cleanText);
    if (round) result.auctionRound = round;

    const address = this.extractor.extractFullAddress(cleanText);
    if (address) result.fullAddress = address;

    return result;
  }

  protected delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
