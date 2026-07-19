import { NextRequest, NextResponse } from 'next/server';
import { exportToExcel } from '@/lib/exportService';
import { Case } from '@/lib/searchService';

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

        const buffer = exportToExcel(cases, filename);
        const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const finalFilename = `${filename}_${timestamp}.xlsx`;

        const uint8Array = new Uint8Array(buffer);

        return new NextResponse(uint8Array, {
            headers: {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': `attachment; filename="${finalFilename}"`,
            },
        });
    } catch (error) {
        console.error('导出错误:', error);
        return NextResponse.json(
            { success: false, message: '导出失败' },
            { status: 500 }
        );
    }
}