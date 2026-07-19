import { V1Output, V1Case } from '../types';
import { V1_HEADERS, DEFAULT_NUMBER_PRECISION } from '../constants';

export function toMarkdown(
    output: V1Output,
    options: {
        includeHeader?: boolean;
        numberPrecision?: number;
    } = {}
): string {
    const { includeHeader = true, numberPrecision = DEFAULT_NUMBER_PRECISION } = options;

    const headers = V1_HEADERS;
    const rows = output.data.map((c) => caseToRow(c, numberPrecision));

    const lines: string[] = [];

    if (includeHeader) {
        lines.push(`| ${headers.join(' | ')} |`);
        lines.push(`| ${headers.map(() => '---').join(' | ')} |`);
    }

    rows.forEach((row) => {
        lines.push(`| ${row.join(' | ')} |`);
    });

    return lines.join('\n');
}

function caseToRow(c: V1Case, precision: number): string[] {
    return [
        c.referenceLocation,
        c.landArea,
        formatNumber(c.buildingArea, precision),
        formatNumber(c.marketValue, precision),
        formatNumber(c.unitPrice, precision, true),
        c.source,
        c.remark.replace(/\n/g, '<br>'),
        c.priceType,
    ];
}

function formatNumber(num: number, precision: number, withThousands: boolean = false): string {
    if (withThousands) {
        return num.toLocaleString('zh-CN', {
            minimumFractionDigits: precision,
            maximumFractionDigits: precision,
        });
    }
    return num.toFixed(precision);
}