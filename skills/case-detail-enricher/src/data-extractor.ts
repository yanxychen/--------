import { DATE_PATTERNS, AREA_PATTERNS, PRICE_PATTERNS } from './constants';

export class DataExtractor {
  extractArea(text: string): number | null {
    for (const pattern of AREA_PATTERNS) {
      const match = text.match(pattern);
      if (match) {
        const numStr = match[1].replace(/[,，\s㎡平方米m²M²]/g, '');
        const num = parseFloat(numStr);
        if (!isNaN(num) && num > 0) {
          return num;
        }
      }
    }
    return null;
  }

  extractDate(text: string): string | null {
    for (const pattern of DATE_PATTERNS) {
      const match = text.match(pattern);
      if (match) {
        return this.normalizeDate(match[1]);
      }
    }
    return null;
  }

  extractPrice(text: string, priceType: 'start' | 'current' | 'deal' = 'start'): number | null {
    const patterns = PRICE_PATTERNS;
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        const numStr = match[1].replace(/[,，\s]/g, '');
        const num = parseFloat(numStr);
        if (!isNaN(num) && num > 0) {
          return num;
        }
      }
    }
    return null;
  }

  extractAuctionRound(text: string): string {
    if (/一拍|第一次拍卖|首次拍卖/.test(text)) return '一拍';
    if (/二拍|第二次拍卖|再次拍卖/.test(text)) return '二拍';
    if (/变卖|变卖阶段/.test(text)) return '变卖';
    return '一拍';
  }

  extractAuctionStatus(text: string, currentTime?: Date): string {
    if (/已成交|成交成功|竞价成功/.test(text)) return '已成交';
    if (/流拍|竞价失败|无人出价/.test(text)) return '流拍';
    if (/变卖失败/.test(text)) return '变卖失败';
    if (/正在进行|竞价中|出价中/.test(text)) return '正在进行';
    if (/即将开始|未开始|开拍/.test(text)) return '即将开始';
    if (/已结束|结束/.test(text)) return '已成交';
    return '即将开始';
  }

  extractFullAddress(text: string): string | null {
    const patterns = [
      /地址[：:]\s*([^\n\r，,]+)/,
      /坐落[：:]\s*([^\n\r，,]+)/,
      /位置[：:]\s*([^\n\r，,]+)/,
      /位于[：:]\s*([^\n\r，,]+)/,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1].trim().length > 5) {
        return match[1].trim();
      }
    }
    return null;
  }

  calculateUnitPrice(marketValue: number, buildingArea: number): number {
    if (!marketValue || !buildingArea || buildingArea <= 0) return 0;
    return (marketValue * 10000) / buildingArea;
  }

  private normalizeDate(dateStr: string): string {
    let normalized = dateStr.trim();

    normalized = normalized
      .replace(/年/g, '-')
      .replace(/月/g, '-')
      .replace(/日/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    const match = normalized.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (match) {
      const year = match[1];
      const month = match[2].padStart(2, '0');
      const day = match[3].padStart(2, '0');
      return `${year}年${parseInt(month)}月${parseInt(day)}日`;
    }

    return normalized;
  }
}
