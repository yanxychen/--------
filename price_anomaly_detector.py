from typing import List, Tuple, Optional


class PriceAnomalyDetector:
    """价格异常检测"""

    def __init__(self, threshold_ratio: float = 0.5):
        """
        Args:
            threshold_ratio: 偏离中位数的比例阈值，默认0.5（即±50%）
        """
        self.threshold_ratio = threshold_ratio

    def detect(self, prices: List[float]) -> Tuple[Optional[float], List[int], List[int]]:
        """检测价格异常

        Args:
            prices: 价格列表

        Returns:
            (正常中位数, 偏高索引列表, 偏低索引列表)
        """
        if not prices or len(prices) < 3:
            return None, [], []

        # 过滤掉无效价格
        valid_prices = [(i, p) for i, p in enumerate(prices) if p and p > 0]
        if len(valid_prices) < 3:
            return None, [], []

        # 按价格排序
        sorted_prices = sorted(valid_prices, key=lambda x: x[1])
        price_values = [p for _, p in sorted_prices]

        # IQR 法计算离群值
        n = len(price_values)
        q1_idx = n // 4
        q3_idx = (3 * n) // 4

        q1 = price_values[q1_idx]
        q3 = price_values[q3_idx]
        iqr = q3 - q1

        # 正常范围
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # 筛选正常价格
        normal_prices = [p for p in price_values if lower_bound <= p <= upper_bound]

        if not normal_prices:
            return None, [], []

        # 计算正常价格的中位数
        normal_prices.sort()
        mid = len(normal_prices) // 2
        if len(normal_prices) % 2 == 0:
            median = (normal_prices[mid - 1] + normal_prices[mid]) / 2
        else:
            median = normal_prices[mid]

        # 判断异常
        high_indices = []
        low_indices = []

        for i, p in valid_prices:
            if p > median * (1 + self.threshold_ratio):
                high_indices.append(i)
            elif p < median * (1 - self.threshold_ratio):
                low_indices.append(i)

        return median, high_indices, low_indices

    def mark_cases(self, cases: List[dict], price_key: str = 'unit_price') -> List[dict]:
        """给案例列表标记价格异常

        Args:
            cases: 案例列表
            price_key: 价格字段名

        Returns:
            标记后的案例列表（增加 price_anomaly 字段：'high'/'low'/None）
        """
        prices = []
        for case in cases:
            p = case.get(price_key)
            if p and isinstance(p, (int, float)) and p > 0:
                prices.append(p)
            else:
                prices.append(None)

        valid_prices = [p for p in prices if p is not None]
        if len(valid_prices) < 3:
            for case in cases:
                case['price_anomaly'] = None
            return cases

        median, high_indices, low_indices = self.detect(prices)

        for i, case in enumerate(cases):
            if i in high_indices:
                case['price_anomaly'] = 'high'
            elif i in low_indices:
                case['price_anomaly'] = 'low'
            else:
                case['price_anomaly'] = None

        return cases
