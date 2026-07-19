import '@/styles/globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: '不良资产估值参考案例搜索工具',
    description: '基于淘宝司法拍卖数据的专业抵押物估值参考工具',
    icons: {
        icon: '/favicon.ico',
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="zh-CN">
            <body>{children}</body>
        </html>
    );
}