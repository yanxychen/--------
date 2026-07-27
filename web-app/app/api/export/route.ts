import { NextRequest, NextResponse } from 'next/server';
import * as XLSX from 'xlsx';

export interface Case {
    id: string;
    referenceLocation: string;
    landArea: string;
    buildingArea: number;
    marketValue: number;
    unitPrice: number;
    source: string;
    sourceText?: string;
    remark: string;
    priceType: string;
    distanceKm?: number;
    link?: string;
}

function safeFormatNumber(value: number | string | undefined | null, decimals: number = 2): string {
    if (value === undefined || value === null) return '-';
    if (typeof value === 'string') return value;
    if (isNaN(value) || !isFinite(value)) return '-';
    if (value === 0) return '-';
    return value.toFixed(decimals);
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const cases: Case[] = body.cases || [];
        const filename = body.filename || '抵押物估值案例';

        if (cases.length === 0) {
            return NextResponse.json(
                { success: false, message: '没有可导出的数据' },
                { status: 400 }
            );
        }

        const header = [
            '参照物位置',
            '土地面积 (m²)',
            '建筑面积 (m²)',
            '市场价值(万元)',
            '建筑单价(元/m²)',
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

        const uint8 = XLSX.write(workbook, { type: 'array', bookType: 'xlsx' });
        const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const finalFilename = `${filename}_${timestamp}.xlsx`;

        return new NextResponse(uint8, {
            headers: {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': `attachment; filename="${finalFilename}"`,
            },
        });
    } catch (error) {
        console.error('导出错误:', error);
        return NextResponse.json(
            { success: false, message: '导出失败，请稍后重试' },
            { status: 500 }
        );
    }
}
