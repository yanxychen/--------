from flask import Flask, request, jsonify, render_template_string, send_file, send_from_directory
import json
import uuid
import os
import time
import glob
from datetime import datetime
from asset_valuation_tool import AssetValuationTool
from excel_renderer import ExcelRenderer

app = Flask(__name__)
tool = AssetValuationTool(gaode_api_key="d7d06a2c20dacd8c861173b82cf70d71")
renderer = ExcelRenderer()

TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_files')
os.makedirs(TEMP_DIR, exist_ok=True)

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))


def cleanup_temp_files():
    now = time.time()
    for filename in os.listdir(TEMP_DIR):
        filepath = os.path.join(TEMP_DIR, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < now - 3600:
                try:
                    os.remove(filepath)
                except:
                    pass


def get_all_excel_files():
    """获取所有可下载文件列表（xlsx, md, pdf）"""
    files = []
    # workspace根目录 - 支持多种格式
    for ext in ['*.xlsx', '*.md', '*.pdf']:
        for f in glob.glob(os.path.join(WORKSPACE_DIR, ext)):
            files.append({
                'name': os.path.basename(f),
                'path': f,
                'size': os.path.getsize(f),
                'mtime': datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'workspace'
            })
    # temp_files目录
    for f in glob.glob(os.path.join(TEMP_DIR, '*.xlsx')):
        files.append({
            'name': os.path.basename(f),
            'path': f,
            'size': os.path.getsize(f),
            'mtime': datetime.fromtimestamp(os.path.getmtime(f)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'temp'
        })
    files.sort(key=lambda x: x['mtime'], reverse=True)
    return files


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>不良资产估值工具 - 网页测试版</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #409DAD 0%, #2c7a8c 100%);
            color: white;
            padding: 25px 30px;
        }
        .header h1 {
            margin: 0 0 8px 0;
            font-size: 28px;
            font-weight: 600;
        }
        .header p {
            margin: 0;
            opacity: 0.9;
            font-size: 15px;
        }
        .content {
            padding: 30px;
        }
        .form-section {
            background: #f8fafc;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid #e2e8f0;
        }
        .form-section h2 {
            margin-top: 0;
            margin-bottom: 20px;
            color: #2d3748;
            font-size: 20px;
            font-weight: 600;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .form-group {
            margin-bottom: 18px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #4a5568;
            font-size: 14px;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px 14px;
            border: 1px solid #cbd5e0;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.2s;
            background: white;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #409DAD;
            box-shadow: 0 0 0 3px rgba(64, 157, 173, 0.1);
        }
        .form-group input:disabled,
        .form-group select:disabled {
            background: #edf2f7;
            color: #a0aec0;
            cursor: not-allowed;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 28px;
            background: #409DAD;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }
        .btn:hover {
            background: #36899a;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(64, 157, 173, 0.2);
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn:disabled {
            background: #cbd5e0;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .btn-secondary {
            background: #718096;
        }
        .btn-secondary:hover {
            background: #5a6c82;
        }
        .btn-group {
            display: flex;
            gap: 12px;
            margin-top: 25px;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #409DAD;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result-section {
            display: none;
            margin-top: 30px;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e2e8f0;
        }
        .result-header h2 {
            margin: 0;
            color: #2d3748;
            font-size: 20px;
        }
        .stats {
            display: flex;
            gap: 25px;
            margin-bottom: 25px;
            padding: 20px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            flex-wrap: wrap;
        }
        .stat-item {
            text-align: center;
            flex: 1;
            min-width: 120px;
        }
        .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: #409DAD;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 13px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .table-container {
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            min-width: 800px;
        }
        thead {
            background: #409DAD;
        }
        th {
            padding: 14px 16px;
            text-align: left;
            color: white;
            font-weight: 500;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        th:last-child {
            border-right: none;
        }
        tbody tr {
            border-bottom: 1px solid #e2e8f0;
            transition: background 0.2s;
        }
        tbody tr:hover {
            background: #f8fafc;
        }
        tbody tr:last-child {
            border-bottom: none;
        }
        td {
            padding: 14px 16px;
            font-size: 14px;
            color: #4a5568;
            vertical-align: top;
            word-break: break-all;
        }
        .no-data {
            text-align: center;
            padding: 40px;
            color: #a0aec0;
            font-style: italic;
        }
        .download-section {
            margin-top: 25px;
            padding: 20px;
            background: #f0f9ff;
            border-radius: 8px;
            border: 1px solid #bae6fd;
        }
        .download-section h3 {
            margin-top: 0;
            margin-bottom: 15px;
            color: #0369a1;
            font-size: 16px;
        }
        .download-buttons {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .error-message {
            background: #fed7d7;
            color: #9b2c2c;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #fc8181;
            display: none;
        }
        .success-message {
            background: #c6f6d5;
            color: #22543d;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #9ae6b4;
            display: none;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #718096;
            font-size: 13px;
        }
        @media (max-width: 768px) {
            .content { padding: 20px; }
            .form-grid { grid-template-columns: 1fr; }
            .btn-group { flex-direction: column; }
            .stats { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>不良资产估值工具</h1>
            <p>输入抵押物信息，获取参考案例及估值分析</p>
        </div>
        
        <div class="content">
            <div class="form-section">
                <h2>抵押物信息</h2>
                <form id="valuationForm">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="address">抵押物地址 *</label>
                            <input type="text" id="address" name="address" 
                                   placeholder="如：北京市朝阳区建国门外大街1号" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="asset_type">资产类型 *</label>
                            <select id="asset_type" name="asset_type" required>
                                <option value="">请选择资产类型</option>
                                <option value="住宅">住宅</option>
                                <option value="商业">商业</option>
                                <option value="工业">工业</option>
                                <option value="土地">土地</option>
                                <option value="特殊资产">特殊资产</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="sub_type">二级分类</label>
                            <select id="sub_type" name="sub_type" disabled>
                                <option value="">请先选择资产类型</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="building_area">建筑面积 (m²)</label>
                            <input type="number" id="building_area" name="building_area" 
                                   placeholder="可选" step="0.01" min="0">
                        </div>
                        
                        <div class="form-group">
                            <label for="land_area">土地面积 (m²)</label>
                            <input type="number" id="land_area" name="land_area" 
                                   placeholder="可选" step="0.01" min="0">
                        </div>
                    </div>
                    
                    <div class="btn-group">
                        <button type="submit" class="btn" id="submitBtn">
                            开始估值
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="resetForm()">
                            重置表单
                        </button>
                    </div>
                </form>
            </div>
            
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <p>正在搜索案例并计算估值，请稍候...</p>
            </div>
            
            <div class="error-message" id="errorMessage"></div>
            <div class="success-message" id="successMessage"></div>
            
            <div class="result-section" id="resultSection">
                <div class="result-header">
                    <h2>估值结果</h2>
                    <div class="btn-group">
                        <button class="btn" onclick="downloadExcel()" id="excelBtn">
                            下载Excel
                        </button>
                        <button class="btn btn-secondary" onclick="downloadJSON()" id="jsonBtn">
                            下载JSON
                        </button>
                    </div>
                </div>
                
                <div class="stats" id="stats">
                </div>
                
                <div class="table-container">
                    <table id="resultTable">
                        <thead>
                            <tr>
                                <th>参照物位置</th>
                                <th>土地面积(m²)</th>
                                <th>建筑面积(m²)</th>
                                <th>市场价值(万元)</th>
                                <th>建筑单价(元/㎡)</th>
                                <th>数据来源</th>
                                <th>备注</th>
                                <th>价格类型</th>
                            </tr>
                        </thead>
                        <tbody id="resultTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 不良资产估值工具 | 版本 1.0.0 | 数据来源：京东拍卖、淘宝司法拍卖</p>
        </div>
    </div>

    <script>
        let currentResultId = null;

        const subTypeMap = {
            '住宅': [],
            '商业': [
                {value: '商铺', label: '商铺'},
                {value: '商场', label: '商场'},
                {value: '办公用房', label: '办公用房'},
                {value: '酒店', label: '酒店'},
                {value: '住宅底商', label: '住宅底商'}
            ],
            '工业': [
                {value: '工业房地产', label: '工业房地产'},
                {value: '工业用地', label: '工业用地'}
            ],
            '土地': [
                {value: '住宅用地', label: '住宅用地'},
                {value: '商业用地', label: '商业用地'},
                {value: '工业用地', label: '工业用地'},
                {value: '综合用地', label: '综合用地'}
            ],
            '特殊资产': [
                {value: '采矿权', label: '采矿权'},
                {value: '林权', label: '林权'},
                {value: '海域使用权', label: '海域使用权'}
            ]
        };

        document.getElementById('asset_type').addEventListener('change', function() {
            const type = this.value;
            const subTypeSelect = document.getElementById('sub_type');
            if (type && subTypeMap[type] && subTypeMap[type].length > 0) {
                subTypeSelect.disabled = false;
                subTypeSelect.innerHTML = '<option value="">请选择二级分类（可选）</option>';
                subTypeMap[type].forEach(item => {
                    subTypeSelect.innerHTML += `<option value="${item.value}">${item.label}</option>`;
                });
            } else {
                subTypeSelect.disabled = true;
                subTypeSelect.innerHTML = '<option value="">无需二级分类</option>';
            }
        });

        document.getElementById('valuationForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            hideMessage('errorMessage');
            hideMessage('successMessage');
            document.getElementById('resultSection').style.display = 'none';
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('submitBtn').disabled = true;
            
            const formData = new FormData(this);
            const params = {};
            for (let [key, value] of formData.entries()) {
                if (value) params[key] = value;
            }
            
            if (params.building_area) params.building_area = parseFloat(params.building_area);
            if (params.land_area) params.land_area = parseFloat(params.land_area);
            
            try {
                const response = await fetch('/api/valuate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(params)
                });
                
                const result = await response.json();
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('submitBtn').disabled = false;
                
                if (result.status === 'success') {
                    currentResultId = result.result_id;
                    showMessage('successMessage', `成功找到 ${result.cases.length} 个参考案例`);
                    updateStats(result);
                    updateTable(result.cases);
                    document.getElementById('resultSection').style.display = 'block';
                } else if (result.status === 'no_cases') {
                    showMessage('errorMessage', result.message || '未找到匹配的参考案例');
                } else {
                    showMessage('errorMessage', result.error || '搜索失败，请稍后重试');
                }
            } catch (err) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('submitBtn').disabled = false;
                showMessage('errorMessage', '网络错误：' + err.message);
            }
        });

        function updateStats(result) {
            const stats = result.statistics || {};
            const cases = result.cases || [];
            const statsDiv = document.getElementById('stats');
            
            let html = '';
            html += `<div class="stat-item"><div class="stat-value">${cases.length}</div><div class="stat-label">案例数量</div></div>`;
            
            if (stats.reference_avg_price) {
                html += `<div class="stat-item"><div class="stat-value">${stats.reference_avg_price}</div><div class="stat-label">参考均价(元/㎡)</div></div>`;
            }
            
            if (stats.normal_case_count !== undefined) {
                html += `<div class="stat-item"><div class="stat-value">${stats.normal_case_count}</div><div class="stat-label">有效案例</div></div>`;
            }
            
            if (stats.price_range) {
                html += `<div class="stat-item"><div class="stat-value" style="font-size:18px;">${stats.price_range}</div><div class="stat-label">价格区间</div></div>`;
            }
            
            if (stats.avg_market_value) {
                html += `<div class="stat-item"><div class="stat-value" style="font-size:18px;">${stats.avg_market_value}</div><div class="stat-label">平均市值(万元)</div></div>`;
            }
            
            statsDiv.innerHTML = html;
        }

        function updateTable(cases) {
            const tbody = document.getElementById('resultTableBody');
            
            if (!cases || cases.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="no-data">暂无数据</td></tr>';
                return;
            }
            
            let html = '';
            cases.forEach(c => {
                html += '<tr>';
                html += `<td>${escapeHtml(c['参照物位置'] || '')}</td>`;
                html += `<td>${escapeHtml(c['土地面积(m²)'] || '')}</td>`;
                html += `<td>${escapeHtml(c['建筑面积(m²)'] || '')}</td>`;
                html += `<td>${escapeHtml(c['市场价值(万元)'] || '')}</td>`;
                html += `<td>${escapeHtml(c['建筑单价(元/㎡)'] || '')}</td>`;
                const source = c['数据来源'] || '';
                if (source && source.startsWith('http')) {
                    html += `<td><a href="${source}" target="_blank" style="color:#409DAD;">查看来源</a></td>`;
                } else {
                    html += `<td>${escapeHtml(source)}</td>`;
                }
                html += `<td>${escapeHtml(c['备注'] || '')}</td>`;
                html += `<td>${escapeHtml(c['价格类型'] || '普通司法拍卖')}</td>`;
                html += '</tr>';
            });
            
            tbody.innerHTML = html;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showMessage(id, message) {
            const el = document.getElementById(id);
            el.textContent = message;
            el.style.display = 'block';
        }

        function hideMessage(id) {
            document.getElementById(id).style.display = 'none';
        }

        function resetForm() {
            document.getElementById('valuationForm').reset();
            document.getElementById('sub_type').disabled = true;
            document.getElementById('sub_type').innerHTML = '<option value="">请先选择资产类型</option>';
            document.getElementById('resultSection').style.display = 'none';
            hideMessage('errorMessage');
            hideMessage('successMessage');
            currentResultId = null;
        }

        function downloadExcel() {
            if (!currentResultId) {
                alert('请先进行估值搜索');
                return;
            }
            window.location.href = `/api/download/excel/${currentResultId}`;
        }

        function downloadJSON() {
            if (!currentResultId) {
                alert('请先进行估值搜索');
                return;
            }
            window.location.href = `/api/download/json/${currentResultId}`;
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    cleanup_temp_files()
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/valuate', methods=['POST'])
def valuate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'error': '请求数据为空'}), 400
        
        address = data.get('address', '').strip()
        if not address:
            return jsonify({'status': 'error', 'error': '地址不能为空'}), 400
        
        asset_type = data.get('asset_type', '').strip()
        if not asset_type:
            return jsonify({'status': 'error', 'error': '资产类型不能为空'}), 400
        
        sub_type = data.get('sub_type') or None
        building_area = data.get('building_area')
        land_area = data.get('land_area')
        max_results = data.get('max_results', 20)
        
        if building_area is not None:
            try:
                building_area = float(building_area)
            except:
                building_area = None
        
        if land_area is not None:
            try:
                land_area = float(land_area)
            except:
                land_area = None
        
        result = tool.search_cases(
            address=address,
            asset_type=asset_type,
            sub_type=sub_type,
            building_area=building_area,
            land_area=land_area,
            max_results=max_results
        )
        
        if result.get('status') == 'success':
            result_id = str(uuid.uuid4())
            
            json_path = os.path.join(TEMP_DIR, f'{result_id}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            
            excel_path = os.path.join(TEMP_DIR, f'{result_id}.xlsx')
            cases = result.get('cases', [])
            stats = result.get('statistics', {})
            title = f"不良资产估值 - {address} - {asset_type}"
            renderer.render_to_excel(
                cases=cases,
                output_path=excel_path,
                title=title,
                statistics=stats
            )
            
            result['result_id'] = result_id
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/download/excel/<result_id>')
def download_excel(result_id):
    try:
        filename = f'{result_id}.xlsx'
        filepath = os.path.join(TEMP_DIR, filename)
        if not os.path.exists(filepath):
            return '文件不存在或已过期', 404
        return send_file(
            filepath,
            as_attachment=True,
            download_name='估值结果.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return str(e), 500


@app.route('/api/download/json/<result_id>')
def download_json(result_id):
    try:
        filename = f'{result_id}.json'
        filepath = os.path.join(TEMP_DIR, filename)
        if not os.path.exists(filepath):
            return '文件不存在或已过期', 404
        return send_file(
            filepath,
            as_attachment=True,
            download_name='估值结果.json',
            mimetype='application/json'
        )
    except Exception as e:
        return str(e), 500


FILES_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Excel文件列表 - 不良资产估值工具</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f7fa;
            color: #333;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #409DAD 0%, #2c7a8c 100%);
            color: white;
            padding: 25px 30px;
        }
        .header h1 { margin: 0 0 8px 0; font-size: 24px; font-weight: 600; }
        .header p { margin: 0; opacity: 0.9; font-size: 14px; }
        .content { padding: 30px; }
        .file-list { list-style: none; padding: 0; margin: 0; }
        .file-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 20px;
            border-bottom: 1px solid #e2e8f0;
            transition: background 0.2s;
        }
        .file-item:hover { background: #f8fafc; }
        .file-item:last-child { border-bottom: none; }
        .file-info { flex: 1; }
        .file-name { font-weight: 500; color: #2d3748; font-size: 15px; margin-bottom: 4px; }
        .file-meta { font-size: 12px; color: #718096; }
        .file-actions { display: flex; gap: 10px; }
        .btn {
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            background: #409DAD;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
        }
        .btn:hover { background: #36899a; }
        .btn-secondary {
            background: #718096;
        }
        .btn-secondary:hover { background: #5a6c82; }
        .empty {
            text-align: center;
            padding: 60px 20px;
            color: #a0aec0;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 8px;
        }
        .badge-workspace { background: #c6f6d5; color: #22543d; }
        .badge-temp { background: #bee3f8; color: #2c5282; }
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: #409DAD;
            text-decoration: none;
            font-size: 14px;
        }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Excel文件下载中心</h1>
            <p>点击下载按钮获取估值结果Excel文件</p>
        </div>
        <div class="content">
            <a href="/" class="back-link">← 返回估值工具</a>
            {% if files %}
            <ul class="file-list">
                {% for f in files %}
                <li class="file-item">
                    <div class="file-info">
                        <div class="file-name">
                            {{ f.name }}
                            <span class="badge badge-{{ f.type }}">{{ f.type }}</span>
                        </div>
                        <div class="file-meta">
                            {{ f.mtime }} &nbsp;|&nbsp; {{ "%.1f"|format(f.size/1024) }} KB
                        </div>
                    </div>
                    <div class="file-actions">
                        <a href="/files/download/{{ f.type }}/{{ f.name }}" class="btn">下载</a>
                        <a href="/files/view/{{ f.type }}/{{ f.name }}" class="btn btn-secondary">预览</a>
                    </div>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <div class="empty">
                <p>暂无Excel文件</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''


@app.route('/files')
def list_files():
    """文件列表页面"""
    files = get_all_excel_files()
    return render_template_string(FILES_HTML_TEMPLATE, files=files)


@app.route('/files/download/<file_type>/<filename>')
def download_file(file_type, filename):
    """下载文件"""
    try:
        if file_type == 'workspace':
            directory = WORKSPACE_DIR
        elif file_type == 'temp':
            directory = TEMP_DIR
        else:
            return '无效的文件类型', 400
        
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return '文件不存在', 404
        
        return send_from_directory(
            directory,
            filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return str(e), 500


@app.route('/files/view/<file_type>/<filename>')
def view_file(file_type, filename):
    """预览Excel文件内容（文本形式）"""
    try:
        import openpyxl
        
        if file_type == 'workspace':
            directory = WORKSPACE_DIR
        elif file_type == 'temp':
            directory = TEMP_DIR
        else:
            return '无效的文件类型', 400
        
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return '文件不存在', 404
        
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        
        # 读取所有数据
        rows = []
        for row in ws.iter_rows(values_only=True):
            rows.append([str(c) if c is not None else '' for c in row])
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>预览: ''' + filename + '''</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f7fa; }
                .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
                h1 { color: #2d3748; font-size: 20px; margin-bottom: 10px; }
                .meta { color: #718096; font-size: 13px; margin-bottom: 20px; }
                table { width: 100%; border-collapse: collapse; font-size: 13px; }
                th { background: #409DAD; color: white; padding: 10px; text-align: left; }
                td { padding: 10px; border-bottom: 1px solid #e2e8f0; color: #4a5568; }
                tr:hover { background: #f8fafc; }
                .back { display: inline-block; margin-bottom: 20px; color: #409DAD; text-decoration: none; }
                .back:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/files" class="back">← 返回文件列表</a>
                <h1>预览: ''' + filename + '''</h1>
                <div class="meta">共 ''' + str(len(rows)) + ''' 行数据</div>
                <div style="overflow-x:auto;">
                <table>
        '''
        
        for i, row in enumerate(rows):
            if i == 0:
                html += '<tr>' + ''.join(f'<th>{c}</th>' for c in row) + '</tr>'
            else:
                html += '<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>'
        
        html += '''
                </table>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        return f'预览失败: {str(e)}', 500


if __name__ == '__main__':
    print('启动不良资产估值工具 Web 版...')
    print('访问地址: http://localhost:5000')
    print('文件列表: http://localhost:5000/files')
    print('按 Ctrl+C 停止服务')
    app.run(host='0.0.0.0', port=5001, debug=False)
