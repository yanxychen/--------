import { V1Output, V1Case } from '../types';
import { V1_HEADERS, DEFAULT_NUMBER_PRECISION, COLUMN_WIDTHS } from '../constants';

export function toHtml(
    output: V1Output,
    options: {
        includeHeader?: boolean;
        numberPrecision?: number;
        clickableLinks?: boolean;
        withStyles?: boolean;
    } = {}
): string {
    const {
        includeHeader = true,
        numberPrecision = DEFAULT_NUMBER_PRECISION,
        clickableLinks = true,
        withStyles = true,
    } = options;

    const headers = V1_HEADERS;
    const rows = output.data;

    const colWidths = Object.values(COLUMN_WIDTHS);

    let html = '';

    if (withStyles) {
        html += `<style>
.v1-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.v1-table th, .v1-table td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; vertical-align: top; }
.v1-table th { background-color: #f3f4f6; font-weight: 600; }
.v1-table tr:nth-child(even) { background-color: #f9fafb; }
.v1-table .link { color: #2563eb; text-decoration: underline; word-break: break-all; font-size: 12px; }
.v1-table .remark { white-space: pre-line; }
.v1-table .number { text-align: right; font-variant-numeric: tabular-nums; }
</style>
`;
    }

    html += '<table class="v1-table">';

    if (includeHeader) {
        html += '<thead><tr>';
        headers.forEach((h, i) => {
            html += `<th style="width: ${colWidths[i]}em">${h}</th>`;
        });
        html += '</tr></thead>';
    }

    html += '<tbody>';
    rows.forEach((c) => {
        html += '<tr>';
        html += `<td>${escapeHtml(c.referenceLocation)}</td>`;
        html += `<td>${escapeHtml(c.landArea)}</td>`;
        html += `<td class="number">${formatNumber(c.buildingArea, numberPrecision)}</td>`;
        html += `<td class="number">${formatNumber(c.marketValue, numberPrecision)}</td>`;
        html += `<td class="number">${formatNumber(c.unitPrice, numberPrecision, true)}</td>`;
        html += '<td>';
        if (clickableLinks && c.source) {
            html += `<a href="${escapeAttr(c.source)}" target="_blank" rel="noopener noreferrer" class="link">${escapeHtml(c.source)}</a>`;
        } else {
            html += escapeHtml(c.source);
        }
        html += '</td>';
        html += `<td class="remark">${escapeHtml(c.remark)}</td>`;
        html += `<td>${escapeHtml(c.priceType)}</td>`;
        html += '</tr>';
    });
    html += '</tbody>';

    html += '</table>';

    return html;
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

function escapeHtml(str: string): string {
    const div = document?.createElement('div');
    if (div) {
        div.textContent = str;
        return div.innerHTML;
    }
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeAttr(str: string): string {
    return str.replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}