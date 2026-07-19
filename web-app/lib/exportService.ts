import * as XLSX from 'xlsx';
import { Case } from './searchService';

function safeFormatNumber(value: number | string | undefined | null, decimals: number = 2): string {
    if (value === undefined || value === null) return '-';
    if (typeof value === 'string') return value;
    if (isNaN(value) || !isFinite(value)) return '-';
    if (value === 0) return '-';
    return value.toFixed(decimals);
}

export function exportToExcel(cases: Case[], filename: string = '抵押物估值案例'): Buffer {
    const header = [
        '参照物位置',
        '土地面积 (㎡)',
        '建筑面积 (㎡)',
        '市场价值(万元)',
        '建筑单价(元/㎡)',
        '数据来源',
        '备注',
        '价格类型',
    ];

    const rows = cases.map(c => [
        c.referenceLocation,
        c.landArea || '-',
        safeFormatNumber(c.buildingArea),
        safeFormatNumber(c.marketValue),
        safeFormatNumber(c.unitPrice),
        c.source,
        c.remark,
        c.priceType,
    ]);

    const worksheetData = [header, ...rows];
    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

    worksheet['!cols'] = [
        { wch: 60 },
        { wch: 15 },
        { wch: 15 },
        { wch: 15 },
        { wch: 18 },
        { wch: 40 },
        { wch: 80 },
        { wch: 15 },
    ];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, '估值案例');

    return XLSX.write(workbook, { type: 'buffer', bookType: 'xlsx' });
}