# Changelog

本文件记录项目的所有重要变更。

## [0.4.0] - 2026-04-08

### Added
- 新增单位「扎」识别（`app.py`、`core/parser.py`）
- 新增 OCR 训练标注数据

### Fixed
- 修复 18-19 位税收编码在 Excel 中显示为科学计数法的问题
  - `core/tax_matcher.py` — 读取税收表时将 float 编码转为整数字符串
  - `core/xlsx_writer.py` — 编码列设为文本格式 (`number_format = '@'`)，防止 Excel 自动转换

### Changed
- 更新税收分类编码表 (`data/tax_list.xlsx`、`data/tax_list_new.xlsx`)

## [0.3.0] - 2026-04-03

### Added
- 税收分类编码自动选择优化
- 商品名称记忆功能，支持记住常用商品对应税收编码
- OCR 训练标注数据 (`data/train_data/_ground_truth.json`)

### Changed
- 移除旧的 `CLAUDE.md` 配置

## [0.2.0] - 2026-04-02

### Added
- 手动录入识别功能 — 支持不通过 OCR 直接手动输入发票信息
- `core/` 模块化重构，将核心功能拆分为独立模块
  - `core/ocr_service.py` — OCR 识别服务
  - `core/parser.py` — 发票数据解析
  - `core/tax_matcher.py` — 税收编码匹配
  - `core/xlsx_writer.py` — Excel 文件生成
- `app.py` 主应用大幅更新（交互流程优化）
- `README.md` 项目说明文档
- `requirements.txt` 依赖更新
- 启动脚本 `start.bat` (Windows) 和 `start.sh` (Linux/Mac)
- `.gitignore` 忽略规则
- 新版税收编码表 `data/tax_list.xlsx`、`data/tax_list_new.xlsx`
- 示例输出文件

### Changed
- `parser.py` → `core/parser.py`
- `tax_matcher.py` → `core/tax_matcher.py`
- `xlsx_writer.py` → `core/xlsx_writer.py`
- 删除独立 `ocr_service.py`（合并至 `core/`）

### Removed
- 根目录下 `ocr_service.py`
- 旧版 `tax_list.xlsx`、`test.jpg`

## [0.1.0] - 2026-03-29

### Added
- 初始化项目仓库
- 基础发票 OCR 识别功能
- 税收编码匹配 (`tax_matcher.py`)
- Excel 发票明细生成 (`xlsx_writer.py`)
- 税收编码数据表 (`tax_list.xlsx`)
- 基础依赖配置
