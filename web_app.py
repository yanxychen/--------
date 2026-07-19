import os
import sys
from flask import Flask, request, jsonify, send_file
import threading
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def run_search(address, property_type, area=None):
    try:
        from asset_search_api import search_cases
        result = search_cases(address, property_type, area)
        return result
    except Exception as e:
        print(f"搜索失败: {e}")
        return None

@app.route('/api/valuate', methods=['POST'])
def valuate():
    try:
        data = request.get_json()
        address = data.get('address', '')
        property_type = data.get('propertyType', 'commercial')
        area = data.get('area')
        
        if not address:
            return jsonify({
                'success': False,
                'message': '地址不能为空',
                'data': []
            }), 400
        
        print(f"收到搜索请求: {address}, 类型: {property_type}, 面积: {area}")
        
        search_result = run_search(address, property_type, area)
        
        if search_result:
            return jsonify(search_result)
        else:
            return jsonify({
                'success': False,
                'message': '搜索失败，请稍后重试',
                'data': []
            }), 500
            
    except Exception as e:
        print(f"API错误: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': []
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/', methods=['GET'])
def index():
    return "不良资产估值参考案例搜索服务 - API运行中"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
