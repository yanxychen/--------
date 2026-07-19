import { V1Output, V1Case } from '../types';
import { V1_HEADERS, DEFAULT_NUMBER_PRECISION, COLUMN_WIDTHS } from '../constants';

export function toExcelData(
    output: V1Output,
    options: {
        includeHeader?: boolean;
        numberPrecision?: number;
    } = {}
): { headers: string[]; rows: string[][]; colWidths: number[] } {
    const { includeHeader = true, numberPrecision = DEFAULT_NUMBER_PRECISION } = options;

    const headers = [...V1_HEADERS];
    const rows = output.data.map((c) => caseToRow(c, numberPrecision));
    const colWidths = Object.values(COLUMN_WIDTHS);

    return {
        headers: includeHeader ? headers : [],
        rows,
        colWidths,
    };
}

function caseToRow(c: V1Case, precision: number): string[] {
    return [
        c.referenceLocation,
        c.landArea,
        c.buildingArea.toFixed(precision),
        c.marketValue.toFixed(precision),
        c.unitPrice.toLocaleString('zh-CN', {
            minimumFractionDigits: precision,
            maximumFractionDigits: precision,
        }),
        c.source,
        c.remark,
        c.priceType,
    ];
}

export function toExcelAOA(
    output: V1Output,
    options: {
        includeHeader?: boolean;
        numberPrecision?: number;
    } = {}
): (string | number)[][] {
    const { includeHeader = true, numberPrecision = DEFAULT_NUMBER_PRECISION } = options;

    const result: (string | number)[][] = [];

    if (includeHeader) {
        result.push([...V1_HEADERS]);
    }

    output.data.forEach((c) => {
        result.push([
            c.referenceLocation,
            c.landArea,
            roundNumber(c.buildingArea, numberPrecision),
            roundNumber(c.marketValue, numberPrecision),
            roundNumber(c.unitPrice, numberPrecision),
            c.source,
            c.remark,
            c.priceType,
        ]);
    });

    return result;
}

function roundNumber(num: number, precision: number): number {
    const factor = Math.pow(10, precision);
    return Math.round(num * factor) / factor;
}