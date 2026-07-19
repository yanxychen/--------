import type { AuctionCase, SearchOptions, Platform } from './types';

export abstract class BaseSearcher {
  protected platform: Platform;
  protected baseUrl: string;

  constructor(platform: Platform, baseUrl: string) {
    this.platform = platform;
    this.baseUrl = baseUrl;
  }

  abstract search(keyword: string, options: SearchOptions): Promise<AuctionCase[]>;

  protected createCase(data: Partial<AuctionCase> & { itemId: string; title: string }): AuctionCase {
    return {
      itemId: data.itemId,
      platform: this.platform,
      title: data.title,
      currentPrice: data.currentPrice || 0,
      location: data.location || '',
      detailUrl: data.detailUrl || '',
      searchKeyword: data.searchKeyword || '',
      auctionStatus: data.auctionStatus,
      category: data.category,
      startPrice: data.startPrice,
      endTime: data.endTime,
      bidCount: data.bidCount,
    };
  }

  protected extractPrice(text: string): number {
    const match = text.replace(/,/g, '').match(/[\d.]+/);
    return match ? parseFloat(match[0]) : 0;
  }

  protected cleanHtml(html: string): string {
    return html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
  }
}
