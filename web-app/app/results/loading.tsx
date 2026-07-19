import LoadingSpinner from '@/components/LoadingSpinner';

export default function Loading() {
    return (
        <div className="min-h-screen bg-gray-50">
            <div className="container mx-auto px-4 py-12">
                <LoadingSpinner text="加载搜索结果..." />
            </div>
        </div>
    );
}