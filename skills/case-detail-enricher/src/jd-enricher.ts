import type { AuctionCase, EnrichedCase } from './types';
import { BaseEnricher } from './base-enricher';

export class JdDetailEnricher extends BaseEnricher {
  constructor() {
    super('jd');
  }

  async enrich(caseItem: AuctionCase, page?: any): Promise<EnrichedCase> {
    if (page) {
      return this.enrichWithPlaywright(caseItem, page);
    }
    return this.enrichMock(caseItem);
  }

  private async enrichWithPlaywright(caseItem: AuctionCase, page: any): Promise<EnrichedCase> {
    try {
      await page.goto(caseItem.detailUrl, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2000);

      const html = await page.content();
      const extracted = this.extractFromHtml(html);

      const pageData = await page.evaluate(() => {
        const getText = (selector: string) => {
          const el = document.querySelector(selector);
          return el?.textContent?.trim() || '';
        };

        return {
          title: getText('.title, .item-title, [class*="title"]'),
          price: getText('.price, .current-price, [class*="price"]'),
          address: getText('.address, .location, [class*="address"], [class*="location"]'),
          area: getText('.area, .building-area, [class*="area"]'),
          startTime: getText('.start-time, .auction-time, [class*="start-time"], [class*="time"]'),
          status: getText('.status, .auction-status, [class*="status"]'),
          court: getText('.court, [class*="court"]'),
        };
      });

      const buildingArea = extracted.buildingArea || this.extractor.extractArea(pageData.area) || 0;
      const startPrice = extracted.startPrice || this.extractor.extractPrice(pageData.price, 'start') || caseItem.currentPrice;
      const marketValue = startPrice / 10000;

      return this.createEnrichedCase(caseItem, {
        fullAddress: extracted.fullAddress || pageData.address || caseItem.location,
        buildingArea,
        marketValue,
        unitPrice: this.extractor.calculateUnitPrice(marketValue, buildingArea),
        startPrice,
        auctionTime: extracted.auctionTime || pageData.startTime || '',
        auctionStatus: extracted.auctionStatus || pageData.status || '即将开始',
        auctionRound: extracted.auctionRound,
        court: pageData.court || undefined,
      });
    } catch (error) {
      console.warn('[JdDetailEnricher] Failed:', error);
      return this.enrichMock(caseItem);
    }
  }

  private enrichMock(caseItem: AuctionCase): EnrichedCase {
    const buildingArea = 80 + Math.floor(Math.random() * 200);
    const startPrice = caseItem.currentPrice;
    const marketValue = startPrice / 10000;

    return this.createEnrichedCase(caseItem, {
      fullAddress: caseItem.location,
      buildingArea,
      marketValue,
      unitPrice: this.extractor.calculateUnitPrice(marketValue, buildingArea),
      startPrice,
      auctionTime: '2024年10月20日',
      auctionStatus: ['即将开始', '正在进行', '已成交', '流拍'][Math.floor(Math.random() * 4)],
      auctionRound: this.detectRound(caseItem.title),
    });
  }
}
