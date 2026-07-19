import type {
  SearchRequest,
  SearchResult,
  SearchMeta,
  StepStatus,
  V1CaseRow,
  SearchResultCase,
  ScoredCase,
  PropertyType,
  OutputFormat,
} from './types';
import { STEP_NAMES, DEFAULT_MIN_CASES, DEFAULT_OUTPUT_FORMAT, PROPERTY_TYPE_MAP } from './constants';

export interface SubSkillHandlers {
  runLocationDistance: (address: string) => Promise<{
    longitude: number;
    latitude: number;
    keywords: string[];
  }>;
  runCaseSearch: (keywords: string[], propertyType: PropertyType) => Promise<SearchResultCase[]>;
  runAssetTypeMatch: (cases: SearchResultCase[], propertyType: PropertyType) => Promise<SearchResultCase[]>;
  runDetailEnrich: (cases: SearchResultCase[]) => Promise<SearchResultCase[]>;
  runSelfAuctionDetect: (cases: SearchResultCase[], address: string) => Promise<string[]>;
  runCaseMerge: (cases: SearchResultCase[]) => Promise<SearchResultCase[]>;
  runCaseFilter: (cases: SearchResultCase[], propertyType: PropertyType, selfAuctionIds: string[], minCases: number) => Promise<SearchResultCase[]>;
  runCaseScoring: (cases: SearchResultCase[], propertyType: PropertyType, targetArea: number, selfAuctionIds: string[]) => Promise<{
    scoredCases: ScoredCase[];
    selfAuctionCases: SearchResultCase[];
  }>;
  runV1Format: (scoredCases: ScoredCase[], selfAuctionCases: SearchResultCase[], output: OutputFormat) => Promise<{
    markdown: string;
    data: V1CaseRow[];
  }>;
}

export class ValuationCaseSearch {
  private handlers: SubSkillHandlers;

  constructor(handlers: SubSkillHandlers) {
    this.handlers = handlers;
  }

  async run(request: SearchRequest): Promise<SearchResult> {
    const startTime = Date.now();
    const steps: StepStatus[] = STEP_NAMES.map((name, index) => ({
      name,
      index,
      status: 'pending',
    }));

    const outputFormat = request.options?.output ?? DEFAULT_OUTPUT_FORMAT;
    const minCases = request.options?.minCases ?? DEFAULT_MIN_CASES;
    const propertyType = this.resolvePropertyType(request.propertyType);
    const targetArea = request.buildingArea ?? 0;

    let keywords: string[] = [];
    let cases: SearchResultCase[] = [];
    let selfAuctionIds: string[] = [];
    let scoredCases: ScoredCase[] = [];
    let selfAuctionCases: SearchResultCase[] = [];
    let formattedData: V1CaseRow[] = [];
    let markdown = '';

    // Step 1: 定位抵押物
    steps[0].status = 'running';
    try {
      const loc = await this.handlers.runLocationDistance(request.address);
      keywords = loc.keywords;
      steps[0].status = 'done';
      steps[0].durationMs = Date.now() - startTime;
    } catch (e: any) {
      steps[0].status = 'error';
      steps[0].error = e.message;
    }

    // Step 2: 多平台搜索
    const step2Start = Date.now();
    steps[1].status = 'running';
    try {
      cases = await this.handlers.runCaseSearch(keywords, propertyType);
      steps[1].status = 'done';
      steps[1].durationMs = Date.now() - step2Start;
    } catch (e: any) {
      steps[1].status = 'error';
      steps[1].error = e.message;
    }

    // Step 3: 类型匹配
    const step3Start = Date.now();
    steps[2].status = 'running';
    try {
      cases = await this.handlers.runAssetTypeMatch(cases, propertyType);
      steps[2].status = 'done';
      steps[2].durationMs = Date.now() - step3Start;
    } catch (e: any) {
      steps[2].status = 'error';
      steps[2].error = e.message;
    }

    // Step 4: 详情页补全
    const step4Start = Date.now();
    steps[3].status = 'running';
    try {
      cases = await this.handlers.runDetailEnrich(cases);
      steps[3].status = 'done';
      steps[3].durationMs = Date.now() - step4Start;
    } catch (e: any) {
      steps[3].status = 'error';
      steps[3].error = e.message;
    }

    // Step 5: 识别自身拍卖
    const step5Start = Date.now();
    steps[4].status = 'running';
    try {
      selfAuctionIds = await this.handlers.runSelfAuctionDetect(cases, request.address);
      steps[4].status = 'done';
      steps[4].durationMs = Date.now() - step5Start;
    } catch (e: any) {
      steps[4].status = 'error';
      steps[4].error = e.message;
    }

    // Step 6: 合并多次拍卖
    const step6Start = Date.now();
    steps[5].status = 'running';
    try {
      cases = await this.handlers.runCaseMerge(cases);
      steps[5].status = 'done';
      steps[5].durationMs = Date.now() - step6Start;
    } catch (e: any) {
      steps[5].status = 'error';
      steps[5].error = e.message;
    }

    // Step 7: 过滤
    const step7Start = Date.now();
    steps[6].status = 'running';
    try {
      cases = await this.handlers.runCaseFilter(cases, propertyType, selfAuctionIds, minCases);
      steps[6].status = 'done';
      steps[6].durationMs = Date.now() - step7Start;
    } catch (e: any) {
      steps[6].status = 'error';
      steps[7].error = e.message;
    }

    // Step 8: 评分排序
    const step8Start = Date.now();
    steps[7].status = 'running';
    try {
      const scoringResult = await this.handlers.runCaseScoring(cases, propertyType, targetArea, selfAuctionIds);
      scoredCases = scoringResult.scoredCases;
      selfAuctionCases = scoringResult.selfAuctionCases;
      steps[7].status = 'done';
      steps[7].durationMs = Date.now() - step8Start;
    } catch (e: any) {
      steps[7].status = 'error';
      steps[7].error = e.message;
    }

    // Step 9: 格式化输出
    const step9Start = Date.now();
    steps[8].status = 'running';
    try {
      const formatResult = await this.handlers.runV1Format(scoredCases, selfAuctionCases, outputFormat);
      markdown = formatResult.markdown;
      formattedData = formatResult.data;
      steps[8].status = 'done';
      steps[8].durationMs = Date.now() - step9Start;
    } catch (e: any) {
      steps[8].status = 'error';
      steps[8].error = e.message;
    }

    const meta: SearchMeta = {
      totalDurationMs: Date.now() - startTime,
      steps,
      totalCases: cases.length,
      scoredCases: scoredCases.length,
      selfAuctionCases: selfAuctionCases.length,
      filteredCases: formattedData.length,
    };

    return {
      markdown,
      data: formattedData,
      meta,
    };
  }

  private resolvePropertyType(type: string): PropertyType {
    return PROPERTY_TYPE_MAP[type] || 'special';
  }
}
