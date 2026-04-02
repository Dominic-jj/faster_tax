# 发票图片自动识别转电子发票

上传手写/打印发票图片，自动 OCR 识别物品信息，匹配税收分类编码，生成标准电子发票明细 xlsx 文件。

## 快速开始

### Windows

双击 `start.bat`

### Linux / Mac

```bash
bash start.sh
```

### 手动启动

```bash
pip install -r requirements.txt
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

## 功能

- **图片识别** — 上传发票图片，OCR 自动提取物品、数量、单价、总价
- **手动输入** — 直接粘贴物品列表，格式：`物品名 数量 单价 总价`
- **规格型号** — 自动从物品名前缀提取（如 `2P 324空气开关` → 规格 `2P 324`）
- **税收分类** — 自动匹配 4200+ 条税收分类编码（参考 `data/tax_list.xlsx`）
- **可编辑表格** — 识别结果支持修改、增删行
- **一键生成 xlsx** — 基于 `data/invoice_template.xlsx` 模板输出，税率 0.01

## OCR 引擎

支持多引擎切换，在图片上传页顶部下拉选择：

| 引擎 | 安装方式 | 特点 |
|------|---------|------|
| **RapidOCR** (默认) | `pip install rapidocr_onnxruntime` | 轻量快速 (~20MB)，中文识别较好 |
| EasyOCR | `pip install easyocr` | 多语言支持，手写效果一般 |
| PaddleOCR | `pip install paddlepaddle paddleocr` | 中文最佳，但依赖较重 (~1GB) |

仅安装了部分引擎也可正常使用，应用会自动检测可用的引擎。

## 项目结构

```
├── app.py                  # Streamlit 主应用
├── start.bat               # Windows 一键启动
├── start.sh                # Linux/Mac 一键启动
├── requirements.txt        # Python 依赖
├── core/                   # 核心模块
│   ├── ocr_service.py      # OCR 多引擎支持
│   ├── parser.py           # 文本解析 → 结构化数据
│   ├── tax_matcher.py      # 税收分类匹配
│   └── xlsx_writer.py      # xlsx 生成
├── data/                   # 数据和模板
│   ├── invoice_template.xlsx
│   └── tax_list.xlsx
├── samples/                # 示例图片
│   └── test.jpg
└── output/                 # 生成的 xlsx 输出目录
```

## 输入格式

每行一个物品，空格分隔：

```
物品名 数量 单价 总价
```

示例：

```
16A 插座 4 15 60
公牛有线 14座 4 38 152
2P 324空气开关 3 30 90
30X 60平板灯 2 50 100
热水器 1 37 37
时控开关 1 55 55
```
