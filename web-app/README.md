# 不良资产估值参考案例搜索工具

基于淘宝司法拍卖数据的专业Web应用，为金融机构和评估机构提供抵押物估值参考。

## ✨ 功能特性

- **智能搜索**：输入抵押物地址和类型，一键搜索同类资产案例
- **标准格式**：V1格式8列报告（参照物位置、土地面积、建筑面积、市场价值、建筑单价、数据来源、备注、价格类型）
- **历史记录**：自动补充一拍/二拍/变卖历史记录
- **Excel导出**：一键导出搜索结果为Excel文件
- **数据缓存**：24小时缓存机制，提升搜索效率

## 🛠️ 技术栈

- **前端**：Next.js 14 (App Router) + TypeScript + Tailwind CSS 3
- **后端**：Next.js API Routes
- **数据库**：SQLite (node-sqlite3)
- **图标**：Lucide React
- **Excel导出**：xlsx

## 📁 项目结构

```
web-app/
├── app/
│   ├── page.tsx              # 搜索页面
│   ├── results/
│   │   └── page.tsx          # 结果页面
│   ├── api/
│   │   ├── search/
│   │   │   └── route.ts      # 搜索API
│   │   └── export/
│   │       └── route.ts      # 导出API
│   └── layout.tsx            # 根布局
├── lib/
│   ├── db.ts                 # 数据库操作
│   ├── searchService.ts      # 搜索服务
│   └── exportService.ts      # 导出服务
├── components/
│   ├── SearchForm.tsx        # 搜索表单组件
│   ├── ResultTable.tsx       # 结果表格组件
│   └── LoadingSpinner.tsx    # 加载动画组件
├── styles/
│   └── globals.css           # 全局样式
├── public/
│   └── favicon.ico           # 网站图标
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── vercel.json               # Vercel部署配置
├── .env.local                # 环境变量
└── .env.local.example        # 环境变量模板
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd web-app
npm install
```

### 2. 配置环境变量

复制 `.env.local.example` 文件并配置：

```bash
cp .env.local.example .env.local
```

编辑 `.env.local`：

```env
PYTHON_API_URL=http://localhost:8000/api/search  # Python后端API地址（可选）
DATABASE_PATH=./data/example.sqlite               # SQLite数据库路径
CACHE_TTL=86400                                   # 缓存过期时间（秒）
```

### 3. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 构建生产版本

```bash
npm run build
npm run start
```

## 📡 API接口

### POST /api/search

搜索抵押物参考案例

**请求参数**：

```json
{
    "address": "赤峰市红山区西屯办事处昭乌达路北段路西1号楼",
    "propertyType": "commercial",
    "area": 12916.69
}
```

**响应结构**：

```json
{
    "success": true,
    "message": "搜索成功",
    "data": [
        {
            "id": "1",
            "referenceLocation": "1、商业用房-...",
            "landArea": "不适用",
            "buildingArea": 306.62,
            "marketValue": 91.99,
            "unitPrice": 3000.13,
            "source": "https://sf-item.taobao.com/sf_item/xxx.htm",
            "remark": "一拍：...\n二拍：...",
            "priceType": "普通司法拍卖",
            "auctionRecords": [...]
        }
    ],
    "total": 4,
    "cacheHit": false
}
```

### POST /api/export

导出Excel文件

**请求参数**：

```json
{
    "cases": [...],
    "filename": "抵押物估值案例"
}
```

**响应**：Excel文件二进制流

## 🚀 Vercel部署

### 一键部署

点击下方按钮一键部署到Vercel：

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-repo/asset-valuation-web&project-name=asset-valuation-web)

### 手动部署步骤

1. **Fork项目**到你的GitHub仓库

2. **连接Vercel**：
   - 访问 https://vercel.com
   - 点击 "New Project"
   - 选择你的GitHub仓库
   - 点击 "Import"

3. **配置环境变量**：
   - 在Vercel项目设置中，添加环境变量：
     - `PYTHON_API_URL`: Python后端API地址（可选，不配置则使用Mock数据）
     - `DATABASE_PATH`: `/tmp/example.sqlite`（Vercel临时目录）
     - `CACHE_TTL`: `86400`

4. **部署**：
   - 点击 "Deploy"
   - 等待部署完成

### Vercel配置说明

- **Framework**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Node.js Version**: 18.x
- **Database**: SQLite（使用Vercel `/tmp` 临时目录存储）

> ⚠️ **注意**：Vercel Serverless Functions 使用临时文件系统，数据库数据在部署后会重置。如需持久化存储，建议使用外部数据库服务（如 Supabase、PlanetScale 等）。

## 📊 数据模型

### 搜索历史表 (search_history)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| address | TEXT | 搜索地址 |
| property_type | TEXT | 物业类型 |
| area | REAL | 抵押物面积 |
| total_cases | INTEGER | 案例数量 |
| created_at | TEXT | 创建时间 |

### 案例缓存表 (case_cache)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| address_key | TEXT | 地址关键词 |
| reference_location | TEXT | 参照物位置 |
| building_area | REAL | 建筑面积 |
| market_value | REAL | 市场价值 |
| unit_price | REAL | 建筑单价 |
| source_url | TEXT | 来源链接 |
| remark | TEXT | 备注 |
| price_type | TEXT | 价格类型 |
| auction_records | TEXT | 拍卖记录(JSON) |
| data_json | TEXT | 完整数据(JSON) |
| expires_at | INTEGER | 过期时间戳 |

### 用户配置表 (user_config)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| key | TEXT | 配置键名 |
| value | TEXT | 配置值 |
| updated_at | TEXT | 更新时间 |

## 📝 注意事项

1. **Python后端**：当前使用Mock数据演示，如需真实搜索功能，请部署Python搜索服务并配置 `PYTHON_API_URL`
2. **数据缓存**：搜索结果默认缓存24小时，可通过 `CACHE_TTL` 配置
3. **数据来源**：数据来源于淘宝司法拍卖，仅供估值参考
4. **隐私保护**：不存储用户敏感信息，搜索历史仅用于展示
5. **Vercel限制**：Vercel Serverless Functions 有执行时间限制（最大10秒），且使用临时文件系统

## 📄 许可证

MIT License