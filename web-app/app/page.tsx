'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import SearchForm from '@/components/SearchForm';
import { Building2, TrendingUp, FileSearch, Shield } from 'lucide-react';

export default function Home() {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(false);

    const handleSearch = async (address: string, propertyType: string) => {
        setIsLoading(true);
        try {
            const searchParams = new URLSearchParams({
                address: encodeURIComponent(address),
                propertyType,
            });
            router.push(`/results?${searchParams.toString()}`);
        } catch (error) {
            console.error('跳转失败:', error);
            alert('操作失败，请稍后重试');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-primary-600 via-primary-700 to-gray-900">
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-20 left-10 w-72 h-72 bg-gold-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-20 right-10 w-96 h-96 bg-primary-400/10 rounded-full blur-3xl"></div>
            </div>

            <div className="relative z-10 container mx-auto px-4 py-12">
                <header className="text-center mb-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-white/10 backdrop-blur-sm rounded-2xl mb-6">
                        <Building2 className="w-8 h-8 text-gold-400" />
                    </div>
                    <h1 className="text-4xl font-bold text-white mb-4">
                        不良资产估值参考案例搜索工具
                    </h1>
                    <p className="text-lg text-gray-300 max-w-2xl mx-auto">
                        基于淘宝司法拍卖数据，为金融机构和评估机构提供专业的抵押物估值参考
                    </p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 max-w-4xl mx-auto">
                    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
                        <div className="w-12 h-12 bg-gold-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                            <TrendingUp className="w-6 h-6 text-gold-400" />
                        </div>
                        <h3 className="text-white font-semibold mb-2">精准估值</h3>
                        <p className="text-gray-300 text-sm">基于真实司法拍卖数据</p>
                    </div>
                    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
                        <div className="w-12 h-12 bg-gold-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                            <FileSearch className="w-6 h-6 text-gold-400" />
                        </div>
                        <h3 className="text-white font-semibold mb-2">智能搜索</h3>
                        <p className="text-gray-300 text-sm">一键搜索同类资产案例</p>
                    </div>
                    <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 text-center">
                        <div className="w-12 h-12 bg-gold-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                            <Shield className="w-6 h-6 text-gold-400" />
                        </div>
                        <h3 className="text-white font-semibold mb-2">专业报告</h3>
                        <p className="text-gray-300 text-sm">标准V1格式8列报告</p>
                    </div>
                </div>

                <SearchForm onSearch={handleSearch} isLoading={isLoading} />

                <footer className="mt-16 text-center text-gray-400 text-sm">
                    <p>数据来源：淘宝司法拍卖 | 仅供估值参考</p>
                </footer>
            </div>
        </div>
    );
}