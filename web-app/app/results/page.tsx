'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ResultTable from '@/components/ResultTable';
import type { Case, SearchResponse } from '@/lib/searchService';

export default function ResultsPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
    const [searchAddress, setSearchAddress] = useState('');
    const [searchPropertyType, setSearchPropertyType] = useState('commercial');
    const [isExporting, setIsExporting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const hasSearchedRef = useRef(false);

    useEffect(() => {
        const address = searchParams.get('address');
        const propertyType = searchParams.get('propertyType');
        const area = searchParams.get('area');

        if (address && propertyType) {
            const decodedAddress = decodeURIComponent(address);
            setSearchAddress(decodedAddress);
            setSearchPropertyType(propertyType);
            
            if (!hasSearchedRef.current) {
                hasSearchedRef.current = true;
                doSearch(decodedAddress, propertyType, area ? parseFloat(area) : undefined);
            }
        } else {
            router.push('/');
        }
    }, [searchParams, router]);

    const doSearch = async (address: string, propertyType: string, area?: number) => {
        setIsLoading(true);
        setError('');
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address,
                    propertyType,
                    area,
                }),
            });

            const result = await response.json();
            setSearchResult(result);
            if (!result.success) {
                setError(result.message || '搜索失败');
            }
        } catch (err) {
            console.error('搜索失败:', err);
            setError('搜索失败，请稍后重试');
        } finally {
            setIsLoading(false);
        }
    };

    const handleBack = () => {
        router.push('/');
    };

    const handleExport = async () => {
        if (!searchResult?.allCases) return;
        setIsExporting(true);
        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cases: searchResult.allCases,
                    filename: '抵押物估值案例',
                }),
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
                a.download = `抵押物估值案例_${timestamp}.xlsx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                alert('导出失败');
            }
        } catch (error) {
            console.error('导出失败:', error);
            alert('导出失败');
        } finally {
            setIsExporting(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center max-w-md px-4">
                    <div className="w-16 h-16 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-700 text-lg font-medium mb-2">正在搜索案例，请稍候...</p>
                    <p className="text-gray-500 text-sm">
                        正在从淘宝司法拍卖获取最新数据，包括建筑面积、起拍时间、距离等详细信息。
                        <br />
                        根据网络情况，大约需要 3-8 分钟。
                    </p>
                    <div className="mt-6 bg-gray-100 rounded-full h-2 overflow-hidden">
                        <div className="bg-primary-600 h-full animate-pulse" style={{ width: '60%' }}></div>
                    </div>
                    <p className="text-gray-400 text-xs mt-2">请勿关闭或刷新页面</p>
                </div>
            </div>
        );
    }

    if (error || !searchResult) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-500 text-lg mb-4">{error || '未知错误'}</p>
                    <button
                        onClick={handleBack}
                        className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                    >
                        返回搜索
                    </button>
                </div>
            </div>
        );
    }

    const top3Cases = searchResult.top3 || [];
    const allCases = searchResult.allCases || [];

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto px-4 py-8">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-primary-600 mb-2">估值参考案例搜索结果</h1>
                    <p className="text-gray-600">以下是符合条件的司法拍卖案例</p>
                </header>

                <ResultTable
                    top3Cases={top3Cases}
                    allCases={allCases}
                    searchAddress={searchAddress}
                    searchPropertyType={searchPropertyType}
                    onBack={handleBack}
                    isExporting={isExporting}
                    onExport={handleExport}
                    selfAuctionCount={searchResult.selfAuctionCount}
                    totalCount={searchResult.totalCount || allCases.length}
                />
            </div>
        </div>
    );
}
