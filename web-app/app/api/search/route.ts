import { NextRequest, NextResponse } from 'next/server';
import { searchCases, SearchRequest } from '@/lib/searchService';

export async function POST(request: NextRequest) {
    try {
        const body: SearchRequest = await request.json();
        
        if (!body.address || !body.propertyType) {
            return NextResponse.json(
                { success: false, message: '缺少必要参数' },
                { status: 400 }
            );
        }

        const result = await searchCases(body);
        return NextResponse.json(result);
    } catch (error) {
        console.error('API搜索错误:', error);
        return NextResponse.json(
            { success: false, message: '服务器内部错误' },
            { status: 500 }
        );
    }
}