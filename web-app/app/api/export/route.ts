import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const cases = body.cases || [];

        if (cases.length === 0) {
            return NextResponse.json(
                { success: false, message: '没有可导出的数据' },
                { status: 400 }
            );
        }

        // 代理到 Render 后端
        const PYTHON_API_URL = process.env.PYTHON_API_URL || 'https://npl-backed.onrender.com/api/search';
        const exportUrl = PYTHON_API_URL.replace('/api/search', '/api/export');

        const response = await fetch(exportUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cases }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            return NextResponse.json(
                { success: false, message: err.message || '导出失败' },
                { status: 500 }
            );
        }

        // 直接透传 Excel 文件
        const buffer = await response.arrayBuffer();
        const filename = `抵押物估值案例_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.xlsx`;

        return new NextResponse(buffer, {
            headers: {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'Content-Disposition': `attachment; filename="${filename}"`,
            },
        });
    } catch (error) {
        console.error('导出代理错误:', error);
        return NextResponse.json(
            { success: false, message: '导出失败，请稍后重试' },
            { status: 500 }
        );
    }
}
