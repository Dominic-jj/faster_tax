# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

发票图片自动识别转电子发票工具。上传/输入发票信息，自动匹配税收分类编码，生成标准 xlsx 电子发票明细文件。

## Project Structure

```
template/
├── app.py                # Streamlit 主应用（入口）
├── start.bat             # Windows 一键启动
├── start.sh              # Linux/Mac 一键启动
├── requirements.txt      # Python 依赖
├── core/                 # 核心模块
│   ├── __init__.py
│   ├── ocr_service.py    # OCR 识别（easyocr）
│   ├── parser.py         # 文本解析 → 结构化物品数据
│   ├── tax_matcher.py    # 税收分类匹配（基于 data/tax_list.xlsx）
│   └── xlsx_writer.py    # xlsx 生成（基于 data/invoice_template.xlsx）
├── data/                 # 数据和模板
│   ├── invoice_template.xlsx  # 发票明细模板
│   └── tax_list.xlsx          # 税收分类编码表（4200+ 条）
├── samples/              # 测试样本
│   └── test.jpg
└── output/               # 生成的 xlsx 输出目录
```

## Commands

```bash
# 启动应用
streamlit run app.py

# 或使用启动脚本
start.bat          # Windows
bash start.sh      # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

## Architecture

- **app.py**: Streamlit 前端，两种输入模式（图片上传 OCR / 手动输入），可编辑 DataFrame，一键下载 xlsx
- **core/ocr_service.py**: easyocr 封装，支持中文简体 + 英文
- **core/parser.py**: 从文本行中提取物品名、规格型号前缀、数量、单价、总价
- **core/tax_matcher.py**: 加载 tax_list.xlsx，通过关键词模糊匹配税收分类编码，优先机电设备分类（109xxx）
- **core/xlsx_writer.py**: 复制 invoice_template.xlsx 模板，从第4行开始填入数据

## Key Constraints

- 税率固定 0.01（1%）
- 默认模板路径 `data/invoice_template.xlsx`
- 默认税收表路径 `data/tax_list.xlsx`
- 两个默认路径在 xlsx_writer.py 和 tax_matcher.py 中通过 `_PROJECT_ROOT` 变量解析
