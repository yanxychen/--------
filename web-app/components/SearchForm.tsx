import { useState, useEffect } from 'react';
import { Search, MapPin, Building, Loader2 } from 'lucide-react';

interface SearchFormProps {
    onSearch: (address: string, propertyType: string) => void;
    isLoading: boolean;
}

const propertyTypes = [
    { value: 'commercial', label: '商业', icon: Building },
    { value: 'residential', label: '住宅', icon: Building },
    { value: 'other', label: '其他', icon: Building },
];

const addressSuggestions = [
    '赤峰市红山区西屯办事处昭乌达路北段路西1号楼',
    '赤峰市红山区南新街办事处长青街居委会新华小区74号楼',
    '红山区站前办事处钢铁西街居委会',
    '赛罕区昭乌达路175号汇商广场商务楼',
];

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
    const [address, setAddress] = useState('');
    const [propertyType, setPropertyType] = useState('commercial');
    const [showSuggestions, setShowSuggestions] = useState(false);

    const filteredSuggestions = addressSuggestions.filter(s =>
        s.toLowerCase().includes(address.toLowerCase())
    );

    useEffect(() => {
        setShowSuggestions(address.length > 0 && filteredSuggestions.length > 0);
    }, [address, filteredSuggestions]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (address.trim() && !isLoading) {
            onSearch(address.trim(), propertyType);
        }
    };

    const handleSuggestionClick = (suggestion: string) => {
        setAddress(suggestion);
        setShowSuggestions(false);
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-8">
                <div className="space-y-6">
                    <div>
                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                            <MapPin className="w-4 h-4 mr-2 text-primary-600" />
                            抵押物地址
                        </label>
                        <div className="relative">
                            <input
                                type="text"
                                value={address}
                                onChange={(e) => setAddress(e.target.value)}
                                placeholder="请输入抵押物详细地址..."
                                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-600 focus:border-transparent transition-all"
                                disabled={isLoading}
                            />
                            {showSuggestions && (
                                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-xl shadow-lg max-h-60 overflow-y-auto">
                                    {filteredSuggestions.map((suggestion, index) => (
                                        <button
                                            key={index}
                                            type="button"
                                            onClick={() => handleSuggestionClick(suggestion)}
                                            className="w-full px-4 py-2 text-left hover:bg-primary-50 transition-colors text-sm"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div>
                        <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                            <Building className="w-4 h-4 mr-2 text-primary-600" />
                            物业类型
                        </label>
                        <div className="flex gap-4">
                            {propertyTypes.map((pt) => {
                                const Icon = pt.icon;
                                return (
                                    <label
                                        key={pt.value}
                                        className={`flex items-center justify-center px-6 py-3 rounded-xl border-2 cursor-pointer transition-all ${
                                            propertyType === pt.value
                                                ? 'border-primary-600 bg-primary-50 text-primary-700'
                                                : 'border-gray-200 hover:border-primary-300'
                                        }`}
                                    >
                                        <input
                                            type="radio"
                                            name="propertyType"
                                            value={pt.value}
                                            checked={propertyType === pt.value}
                                            onChange={(e) => setPropertyType(e.target.value)}
                                            className="sr-only"
                                            disabled={isLoading}
                                        />
                                        <Icon className="w-5 h-5 mr-2" />
                                        <span className="font-medium">{pt.label}</span>
                                    </label>
                                );
                            })}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={!address.trim() || isLoading}
                        className={`w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-semibold text-white transition-all ${
                            isLoading || !address.trim()
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-primary-600 hover:bg-primary-700 shadow-lg hover:shadow-xl'
                        }`}
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                搜索中...
                            </>
                        ) : (
                            <>
                                <Search className="w-5 h-5" />
                                一键搜索
                            </>
                        )}
                    </button>
                </div>
            </form>

            {!isLoading && (
                <div className="mt-6 text-center text-sm text-gray-500">
                    <p>示例地址：赤峰市红山区西屯办事处昭乌达路北段路西1号楼</p>
                </div>
            )}
        </div>
    );
}