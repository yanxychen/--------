import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
    text?: string;
}

export default function LoadingSpinner({ text = '加载中...' }: LoadingSpinnerProps) {
    return (
        <div className="flex flex-col items-center justify-center py-16">
            <div className="relative">
                <div className="w-16 h-16 border-4 border-primary-200 rounded-full"></div>
                <div className="w-16 h-16 border-4 border-primary-600 rounded-full border-t-transparent animate-spin absolute top-0"></div>
                <Loader2 className="w-8 h-8 text-primary-600 animate-spin absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className="mt-4 text-gray-600 font-medium">{text}</p>
        </div>
    );
}