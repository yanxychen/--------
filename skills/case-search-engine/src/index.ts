import type {
  SearchRequest,
  SearchResult,
  SearchLogEntry,
  AuctionCase,
  SearchEngineConfig,
  Platform,
} from './types';
import { DEFAULT_CONFIG } from './constants';
import { TaobaoSearcher } from './taobao-searcher';
import { JdSearcher } from './jd-searcher';
import { Deduplicator } from './deduplicator';

export class CaseSearchEngine {
  private config: SearchEngineConfig;
  private taobaoSearcher: TaobaoSearcher;
  private jdSearcher: JdSearcher;
  private deduplicator: Deduplicator;

  constructor(config: Partial<SearchEngineConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.taobaoSearcher = new TaobaoSearcher();
    this.jdSearcher = new JdSearcher();
    this.deduplicator = new Deduplicator();
  }

  async search(request: SearchRequest): Promise<SearchResult> {
    const {
      keywords,
      propertyType,
      assetType,
      maxPages = this.config.maxPages,
      pageSize = this.config.pageSize,
      platforms,
    } = request;

    const searchLog: SearchLogEntry[] = [];
    const allCases: AuctionCase[] = [];

    const targetPlatforms: Platform[] = platforms || [
      ...(this.config.taobaoEnabled ? ['taobao' as const] : []),
      ...(this.config.jdEnabled ? ['jd' as const] : []),
    ];

    for (const keyword of keywords) {
      for (const platform of targetPlatforms) {
        for (let page = 1; page <= maxPages; page++) {
          const startTime = Date.now();
          let success = true;
          let error: string | undefined;
          let resultCount = 0;

          try {
            const cases = await this.searchPlatform(platform, keyword, {
              propertyType,
              assetType,
              page,
              pageSize,
            });

            resultCount = cases.length;
            allCases.push(...cases);
          } catch (e) {
            success = false;
            error = e instanceof Error ? e.message : String(e);
          }

          searchLog.push({
            keyword,
            platform,
            page,
            resultCount,
            duration: Date.now() - startTime,
            success,
            error,
          });
        }
      }
    }

    let finalCases = allCases;
    if (this.config.deduplicate) {
      this.deduplicator.reset();
      finalCases = this.deduplicator.deduplicate(allCases);
    }

    return {
      cases: finalCases,
      totalCount: finalCases.length,
      platforms: targetPlatforms,
      searchLog,
    };
  }

  private async searchPlatform(
    platform: Platform,
    keyword: string,
    options: { propertyType: string; assetType: string; page: number; pageSize: number }
  ): Promise<AuctionCase[]> {
    switch (platform) {
      case 'taobao':
        return this.taobaoSearcher.search(keyword, options);
      case 'jd':
        return this.jdSearcher.search(keyword, options);
      default:
        return [];
    }
  }

  setTaobaoStorageState(state: string) {
    this.taobaoSearcher.setStorageState(state);
  }
}

export {
  type SearchRequest,
  type SearchResult,
  type AuctionCase,
  type SearchLogEntry,
  type SearchEngineConfig,
  type Platform,
};
