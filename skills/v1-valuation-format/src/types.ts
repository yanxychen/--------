export const FORMAT_VERSION = 'v1.0.0';

export const V1_HEADERS = [
    '参照物位置',
    '土地面积 (㎡)',
    '建筑面积 (㎡)',
    '市场价值(万元)',
    '建筑单价(元/㎡)',
    '数据来源',
    '备注',
    '价格类型',
] as const;

export type V1Header = typeof V1_HEADERS[number];

export const V1_COLUMN_COUNT = V1_HEADERS.length;

export interface V1Case {
    referenceLocation: string;
    landArea: string;
    buildingArea: number | string;
    marketValue: number | string;
    unitPrice: number | string;
    source: string;
    remark: string;
    priceType: string;
}

export interface V1Output {
    formatVersion: string;
    headers: string[];
    data: V1Case[];
    total: number;
    selfAuctionCount: number;
    scoredCaseCount: number;
}

export interface AuctionRecord {
    round: string;
    date: string;
    startPrice: number;
    endPrice?: number;
    status: string;
}

export interface ScoreBreakdown {
    itemId: string;
    distanceScore: number;
    areaScore: number;
    timeScore: number;
    totalScore: number;
    distance: number;
    areaDiffRatio: number;
    daysAgo: number;
}

export interface ScoringCase {
    itemId: string;
    platform: 'taobao' | 'jd';
    title: string;
    fullAddress: string;
    buildingArea: number;
    marketValue: number;
    auctionTime: string;
    auctionStatus: string;
    auctionRound: string;
    drivingDistance?: number;
    straightDistance?: number;
    sourceUrl: string;
    auctionRecords?: AuctionRecord[];
}

export interface ScoredCase extends ScoringCase {
    totalScore: number;
    distanceScore: number;
    areaScore: number;
    timeScore: number;
    scoreBreakdown: ScoreBreakdown;
}

export interface FieldMapping {
    referenceLocation?: string;
    landArea?: string;
    buildingArea?: string;
    marketValue?: string;
    unitPrice?: string;
    source?: string;
    remark?: string;
    priceType?: string;
    auctionRecords?: string;
    drivingDistance?: string;
    straightDistance?: string;
    auctionTime?: string;
    auctionRound?: string;
    auctionStatus?: string;
}

export interface FormatOptions {
    fieldMapping?: FieldMapping;
    output?: 'markdown' | 'json' | 'excel' | 'html';
    includeHeader?: boolean;
    numberPrecision?: number;
    selfAuctionFirst?: boolean;
    showScore?: boolean;
}

export interface MarkdownFormatOptions extends FormatOptions {
    output: 'markdown';
}

export interface JsonFormatOptions extends FormatOptions {
    output: 'json';
}

export interface ExcelFormatOptions extends FormatOptions {
    output: 'excel';
    filename?: string;
}

export interface HtmlFormatOptions extends FormatOptions {
    output: 'html';
    clickableLinks?: boolean;
}

export type FormatOutput = string | V1Output | ArrayBuffer;

export interface FormatFromScoredInput {
    scoredCases: ScoredCase[];
    selfAuctionCases?: ScoringCase[];
    options?: FormatOptions;
}