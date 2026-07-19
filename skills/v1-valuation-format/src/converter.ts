import {
    V1Case,
    V1Output,
    FieldMapping,
    AuctionRecord,
    FormatOptions,
    ScoringCase,
    ScoredCase,
    FormatFromScoredInput,
} from './types';
import {
    DEFAULT_FIELD_MAPPING,
    DEFAULT_NUMBER_PRECISION,
    DEFAULT_LAND_AREA,
    DEFAULT_PRICE_TYPE,
    SELF_AUCTION_PRICE_TYPE,
    SELF_AUCTION_PREFIX,
    NO_DATA_PLACEHOLDER,
    FORMAT_VERSION,
    V1_HEADERS,
    ROUND_ORDER,
} from './constants';

export class V1FormatConverter {
    private fieldMapping: FieldMapping;
    private numberPrecision: number;
    private showScore: boolean;

    constructor(options?: FormatOptions) {
        this.fieldMapping = { ...DEFAULT_FIELD_MAPPING, ...options?.fieldMapping };
        this.numberPrecision = options?.numberPrecision ?? DEFAULT_NUMBER_PRECISION;
        this.showScore = options?.showScore ?? false;
    }

    convert(cases: any[]): V1Output {
        const data = cases.map((c, index) => this.convertSingleCase(c, index));
        return {
            formatVersion: FORMAT_VERSION,
            headers: [...V1_HEADERS],
            data,
            total: data.length,
            selfAuctionCount: 0,
            scoredCaseCount: data.length,
        };
    }

    convertFromScored(input: FormatFromScoredInput): V1Output {
        const { scoredCases, selfAuctionCases = [], options } = input;
        const selfAuctionFirst = options?.selfAuctionFirst ?? true;

        const formattedSelfAuction = selfAuctionCases.map((c, index) =>
            this.convertScoringCase(c, true, index)
        );
        const formattedScored = scoredCases.map((c, index) =>
            this.convertScoredCase(c, false, index)
        );

        const data = selfAuctionFirst
            ? [...formattedSelfAuction, ...formattedScored]
            : [...formattedScored, ...formattedSelfAuction];

        return {
            formatVersion: FORMAT_VERSION,
            headers: [...V1_HEADERS],
            data,
            total: data.length,
            selfAuctionCount: formattedSelfAuction.length,
            scoredCaseCount: formattedScored.length,
        };
    }

    private convertScoringCase(
        caseItem: ScoringCase,
        isSelfAuction: boolean,
        index: number
    ): V1Case {
        const referenceLocation = caseItem.fullAddress || `${index + 1}、未知位置`;
        const landArea = DEFAULT_LAND_AREA;
        const buildingArea = caseItem.buildingArea && caseItem.buildingArea > 0
            ? this.round(caseItem.buildingArea)
            : NO_DATA_PLACEHOLDER;
        const marketValue = caseItem.marketValue && caseItem.marketValue > 0
            ? this.round(caseItem.marketValue / 10000)
            : NO_DATA_PLACEHOLDER;

        let unitPrice: number | string = NO_DATA_PLACEHOLDER;
        if (
            typeof buildingArea === 'number' &&
            typeof marketValue === 'number' &&
            buildingArea > 0 &&
            marketValue > 0
        ) {
            unitPrice = this.round((marketValue * 10000) / buildingArea);
        }

        const source = caseItem.sourceUrl || '';
        const remark = this.buildRemarkFromCase(caseItem, isSelfAuction);
        const priceType = DEFAULT_PRICE_TYPE;

        return {
            referenceLocation,
            landArea,
            buildingArea,
            marketValue,
            unitPrice,
            source,
            remark,
            priceType,
        };
    }

    private convertScoredCase(
        caseItem: ScoredCase,
        isSelfAuction: boolean,
        index: number
    ): V1Case {
        const baseCase = this.convertScoringCase(caseItem, isSelfAuction, index);

        if (this.showScore) {
            const scoreLine = `评分：${caseItem.totalScore.toFixed(1)}分（距离${caseItem.distanceScore.toFixed(1)}+面积${caseItem.areaScore.toFixed(1)}+时间${caseItem.timeScore.toFixed(1)}）`;
            baseCase.remark = scoreLine + '\n' + baseCase.remark;
        }

        return baseCase;
    }

    private convertSingleCase(rawCase: any, index: number): V1Case {
        const fm = this.fieldMapping;

        const referenceLocation = this.getStringValue(
            rawCase,
            fm.referenceLocation!,
            `${index + 1}、未知位置`
        );

        const landArea = this.getStringValue(rawCase, fm.landArea!, DEFAULT_LAND_AREA);

        const buildingAreaRaw = this.getNumberValue(rawCase, fm.buildingArea!, 0);
        const buildingArea = buildingAreaRaw > 0 ? this.round(buildingAreaRaw) : NO_DATA_PLACEHOLDER;

        const marketValueRaw = this.getNumberValue(rawCase, fm.marketValue!, 0);
        const marketValue = marketValueRaw > 0 ? this.round(marketValueRaw) : NO_DATA_PLACEHOLDER;

        let unitPrice: number | string = NO_DATA_PLACEHOLDER;
        const unitPriceRaw = this.getNumberValue(rawCase, fm.unitPrice!, 0);
        if (unitPriceRaw > 0) {
            unitPrice = this.round(unitPriceRaw);
        } else if (
            typeof buildingArea === 'number' &&
            typeof marketValue === 'number' &&
            buildingArea > 0 &&
            marketValue > 0
        ) {
            unitPrice = this.round((marketValue * 10000) / buildingArea);
        }

        const source = this.getStringValue(rawCase, fm.source!, '');

        let remark = this.getStringValue(rawCase, fm.remark!, '');
        if (!remark && rawCase[fm.auctionRecords!]) {
            remark = this.buildRemarkFromRecords(rawCase[fm.auctionRecords!]);
        }

        const priceType = this.getStringValue(rawCase, fm.priceType!, DEFAULT_PRICE_TYPE);

        return {
            referenceLocation,
            landArea,
            buildingArea,
            marketValue,
            unitPrice,
            source,
            remark,
            priceType,
        };
    }

    private buildRemarkFromCase(caseItem: ScoringCase, isSelfAuction: boolean): string {
        const lines: string[] = [];

        if (caseItem.auctionRecords && caseItem.auctionRecords.length > 0) {
            const recordLines = this.buildRemarkFromRecords(caseItem.auctionRecords);
            lines.push(recordLines);
        } else {
            const round = caseItem.auctionRound || '一拍';
            const date = this.formatDate(caseItem.auctionTime);
            const status = caseItem.auctionStatus || '未知';
            const startPrice = caseItem.marketValue || 0;
            lines.push(`${round}：${date}，起拍价：${this.formatPrice(startPrice)}元，状态：${status}`);
        }

        const distance = caseItem.drivingDistance ?? caseItem.straightDistance;
        if (distance !== undefined && distance !== null && distance > 0) {
            const distanceKm = (distance / 1000).toFixed(1);
            lines.push(`距离抵押物约${distanceKm}公里`);
        }

        return lines.join('\n');
    }

    private buildRemarkFromRecords(records: AuctionRecord[]): string {
        const sorted = [...records].sort((a, b) => {
            const aIndex = ROUND_ORDER.indexOf(a.round);
            const bIndex = ROUND_ORDER.indexOf(b.round);
            return aIndex - bIndex;
        });

        const lines = sorted.map((r) => {
            let line = `${r.round}：${r.date}，起拍价：${this.formatPrice(r.startPrice)}元，状态：${r.status}`;
            if (r.endPrice && r.endPrice > 0 && r.status === '已成交') {
                line += `，成交价：${this.formatPrice(r.endPrice)}元`;
            }
            return line;
        });

        return lines.join('\n');
    }

    private formatDate(dateStr: string): string {
        if (!dateStr) return '未知日期';
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return '未知日期';
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}年${month}月${day}日`;
    }

    private formatPrice(price: number): string {
        if (!price || price <= 0) return '0';
        return price.toLocaleString('zh-CN', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
    }

    private getStringValue(obj: any, key: string, defaultValue: string): string {
        if (obj == null) return defaultValue;
        const value = obj[key];
        if (value == null || value === '') return defaultValue;
        return String(value);
    }

    private getNumberValue(obj: any, key: string, defaultValue: number): number {
        if (obj == null) return defaultValue;
        const value = obj[key];
        if (value == null || value === '') return defaultValue;
        const num = Number(value);
        return isNaN(num) ? defaultValue : num;
    }

    private round(num: number): number {
        const factor = Math.pow(10, this.numberPrecision);
        return Math.round(num * factor) / factor;
    }
}

export function convertToV1(cases: any[], options?: FormatOptions): V1Output {
    const converter = new V1FormatConverter(options);
    return converter.convert(cases);
}

export function convertFromScored(input: FormatFromScoredInput): V1Output {
    const converter = new V1FormatConverter(input.options);
    return converter.convertFromScored(input);
}