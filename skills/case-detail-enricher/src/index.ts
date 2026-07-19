import type {
  EnrichRequest,
  EnrichResult,
  AuctionCase,
  EnrichedCase,
  FailLogEntry,
  DetailEnricherConfig,
} from './types';
import { DEFAULT_CONFIG } from './constants';
import { TaobaoDetailEnricher } from './taobao-enricher';
import { JdDetailEnricher } from './jd-enricher';

export class CaseDetailEnricher {
  private config: DetailEnricherConfig;
  private taobaoEnricher: TaobaoDetailEnricher;
  private jdEnricher: JdDetailEnricher;
  private playwrightPage: any = null;

  constructor(config: Partial<DetailEnricherConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.taobaoEnricher = new TaobaoDetailEnricher();
    this.jdEnricher = new JdDetailEnricher();
  }

  setPlaywrightPage(page: any) {
    this.playwrightPage = page;
  }

  async enrich(request: EnrichRequest): Promise<EnrichResult> {
    const { cases, maxRetries, concurrency, delay } = {
      ...this.config,
      ...request,
    };

    const enrichedCases: EnrichedCase[] = [];
    const failLog: FailLogEntry[] = [];
    let enrichCount = 0;
    let failCount = 0;

    for (let i = 0; i < cases.length; i += concurrency) {
      const batch = cases.slice(i, i + concurrency);
      const batchResults = await Promise.all(
        batch.map(c => this.enrichSingle(c, maxRetries))
      );

      for (const result of batchResults) {
        if (result.success) {
          enrichedCases.push(result.case!);
          enrichCount++;
        } else {
          failLog.push(result.failLog!);
          failCount++;
        }
      }

      if (i + concurrency < cases.length && delay > 0) {
        await this.sleep(delay);
      }
    }

    return {
      enrichedCases,
      enrichCount,
      failCount,
      failLog,
    };
  }

  private async enrichSingle(
    caseItem: AuctionCase,
    maxRetries: number
  ): Promise<{ success: boolean; case?: EnrichedCase; failLog?: FailLogEntry }> {
    let lastError: Error | null = null;
    let retryCount = 0;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const enricher = caseItem.platform === 'taobao'
          ? this.taobaoEnricher
          : this.jdEnricher;

        const result = await enricher.enrich(caseItem, this.playwrightPage);

        if (result.buildingArea > 0 && result.auctionTime) {
          return { success: true, case: result };
        }

        if (result.buildingArea > 0) {
          return { success: true, case: result };
        }

        throw new Error('未能获取关键数据');
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        retryCount = attempt + 1;

        if (attempt < maxRetries) {
          await this.sleep(1000 * (attempt + 1));
        }
      }
    }

    return {
      success: false,
      failLog: {
        itemId: caseItem.itemId,
        platform: caseItem.platform,
        title: caseItem.title,
        error: lastError?.message || '未知错误',
        retryCount,
      },
    };
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

export {
  type EnrichRequest,
  type EnrichResult,
  type AuctionCase,
  type EnrichedCase,
  type FailLogEntry,
  type DetailEnricherConfig,
};
