import type { AuctionCase, SearchOptions } from './types';
import { BaseSearcher } from './base-searcher';
import { JD_BASE_URL } from './constants';

export class JdSearcher extends BaseSearcher {
  constructor() {
    super('jd', JD_BASE_URL);
  }

  async search(keyword: string, options: SearchOptions): Promise<AuctionCase[]> {
    try {
      const searchKeyword = `${keyword} ${options.assetType}`;
      const url = `${this.baseUrl}/search?keyword=${encodeURIComponent(searchKeyword)}&page=${options.page}`;

      const cases: AuctionCase[] = [];

      for (let i = 0; i < 3; i++) {
        const mockCase = this.createMockCase(keyword, i, options.page, options.assetType);
        cases.push(mockCase);
      }

      return cases;
    } catch (error) {
      console.warn('[JdSearcher] Search failed:', error);
      return [];
    }
  }

  private createMockCase(keyword: string, index: number, page: number, assetType: string): AuctionCase {
    const id = `jd_${keyword}_${page}_${index}_${Date.now()}`;
    return this.createCase({
      itemId: id,
      title: `${keyword} ${assetType}拍卖 [京东] ${index + 1}`,
      currentPrice: Math.floor(Math.random() * 5000000) + 500000,
      location: `佛山市禅城区${keyword}周边`,
      detailUrl: `${this.baseUrl}/auction/${id}.html`,
      searchKeyword: keyword,
      auctionStatus: ['即将开始', '正在进行', '已结束'][index % 3],
      category: assetType,
    });
  }

  async searchWithPlaywright(
    keyword: string,
    options: SearchOptions,
    page: any
  ): Promise<AuctionCase[]> {
    try {
      const searchKeyword = `${keyword} ${options.assetType}`;
      const url = `${this.baseUrl}/search?keyword=${encodeURIComponent(searchKeyword)}&page=${options.page}`;

      await page.goto(url, { waitUntil: 'domcontentloaded' });

      const items = await page.evaluate(() => {
        const elements = document.querySelectorAll('.auction-item, .item, [data-sku]');
        return Array.from(elements).map(el => {
          const id = el.getAttribute('data-sku') || el.getAttribute('data-id') || '';
          const titleEl = el.querySelector('.title, .item-title, [class*="title"]');
          const priceEl = el.querySelector('.price, .current-price, [class*="price"]');
          const locationEl = el.querySelector('.location, .item-location, [class*="location"]');
          const linkEl = el.querySelector('a');

          return {
            itemId: id,
            title: titleEl?.textContent?.trim() || '',
            price: priceEl?.textContent?.trim() || '',
            location: locationEl?.textContent?.trim() || '',
            detailUrl: linkEl?.getAttribute('href') || '',
          };
        });
      });

      return items
        .filter(item => item.itemId && item.title)
        .map(item => this.createCase({
          itemId: item.itemId,
          title: item.title,
          currentPrice: this.extractPrice(item.price),
          location: item.location,
          detailUrl: item.detailUrl.startsWith('http') ? item.detailUrl : `https:${item.detailUrl}`,
          searchKeyword: keyword,
          category: options.assetType,
        }));
    } catch (error) {
      console.warn('[JdSearcher] Playwright search failed:', error);
      return [];
    }
  }
}
