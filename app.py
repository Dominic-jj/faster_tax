"""
发票图片自动识别转电子发票 - Streamlit 主应用

使用方法：streamlit run app.py
"""

import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image

# 项目根目录 & 核心模块路径
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'core'))

from parser import Item, parse_text_line, parse_text_lines  # noqa: E402
from tax_matcher import TaxMatcher  # noqa: E402
from xlsx_writer import generate_to_bytes  # noqa: E402

# ─── 页面配置 ────────────────────────────────────────────
st.set_page_config(
    page_title='发票识别转换',
    page_icon='📄',
    layout='wide',
    initial_sidebar_state='collapsed',
)

# ─── 主题：两侧深色 + 中间浅色卡片 ──────────────────────────
st.markdown("""
<style>
/* 两侧深色 */
.stApp { background: #0f1117; }

/* 中间主体浅色卡片 */
.block-container {
    background: #ffffff;
    border-radius: 16px;
    padding: 2rem 2.5rem !important;
    max-width: 1200px;
    margin: 1.5rem auto;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}

/* 标题 */
h1 { color: #1e1e2e !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2, h3, h4 { color: #2d2d44 !important; }
p { color: #5c5c7a; }

/* ── Primary 按钮（紫色高饱和） ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: #ffffff !important; border: none !important; border-radius: 10px !important;
    padding: 12px 32px !important; font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span {
    color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 24px rgba(99,102,241,0.45) !important; transform: translateY(-1px);
}
.stButton > button[kind="primary"]:disabled {
    opacity: 0.5 !important; box-shadow: none !important;
}
.stButton > button[kind="primary"]:disabled p,
.stButton > button[kind="primary"]:disabled span {
    color: #ffffff !important;
}

/* ── 次要按钮 ── */
.stButton > button:not([kind="primary"]):not([kind="header"]) {
    background: #f1f1f6 !important; color: #4a4a68 !important;
    border: 1px solid #dddee8 !important; border-radius: 10px !important;
    padding: 10px 24px !important; font-weight: 500 !important;
    min-height: 44px !important; font-size: 0.9rem !important;
    transition: all 0.2s !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #e8e8f0 !important; border-color: #6366f1 !important; color: #3b3b5c !important;
}

/* ── Download 按钮（绿色高饱和） ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: #fff !important; border: none !important; border-radius: 10px !important;
    padding: 12px 32px !important; font-weight: 600 !important;
    box-shadow: 0 4px 16px rgba(16,185,129,0.3) !important;
}

/* ── 输入框 ── */
.stTextArea textarea, .stTextInput input {
    background: #f7f7fb !important; color: #2d2d44 !important;
    border: 1px solid #dddee8 !important; border-radius: 10px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #6366f1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.12);
}
.stTextArea textarea::placeholder { color: #a0a0b8 !important; }

/* ── 表格 ── */
.stDataEditor { border-radius: 12px !important; border: 1px solid #e4e4ee !important; overflow: hidden; }
.stDataEditor table { background: #fff !important; }
.stDataEditor th {
    background: #f4f4fa !important; color: #5c5c7a !important;
    border-bottom: 2px solid #6366f1 !important; font-weight: 600 !important;
    text-transform: uppercase; font-size: 0.78rem; letter-spacing: 0.5px;
}
.stDataEditor td { color: #2d2d44 !important; border-bottom: 1px solid #f0f0f6 !important; }
.stDataEditor tr:hover td { background: rgba(99,102,241,0.04) !important; }

/* ── 文件上传 ── */
.stFileUploader {
    border: 2px dashed #c8c8dc !important; border-radius: 14px !important;
    background: #f9f9fd !important; padding: 1.5rem !important;
}
.stFileUploader:hover { border-color: #6366f1 !important; }

hr { border-color: #e8e8f0 !important; }
.streamlit-expanderHeader { background: #f7f7fb !important; border-radius: 10px !important; color: #4a4a68 !important; border: 1px solid #e4e4ee; }
.stSuccess { background: rgba(16,185,129,0.08) !important; color: #065f46 !important; border-radius: 10px !important; border-left: 4px solid #10b981 !important; }
.stWarning { background: rgba(245,158,11,0.08) !important; color: #92400e !important; border-radius: 10px !important; border-left: 4px solid #f59e0b !important; }
.stError   { background: rgba(239,68,68,0.08) !important; color: #991b1b !important; border-radius: 10px !important; border-left: 4px solid #ef4444 !important; }
.stSpinner > div { border-color: #6366f1 transparent #6366f1 transparent !important; }

/* ── 徽标 ── */
.badge { display:inline-block; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600; margin:0 4px; }
.badge-purple { background:rgba(99,102,241,0.1); color:#6366f1; }
.badge-green  { background:rgba(16,185,129,0.1); color:#059669; }
.badge-amber  { background:rgba(245,158,11,0.1); color:#d97706; }
.badge-red    { background:rgba(239,68,68,0.1); color:#dc2626; }
.badge-slate  { background:#f1f1f6; color:#64748b; }

/* ── 统计卡片 ── */
.stat-card { background:#f7f7fb; border-radius:12px; padding:1rem 1.25rem; border:1px solid #e4e4ee; text-align:center; }
.stat-value { font-size:1.6rem; font-weight:700; color:#4f46e5; }
.stat-label { font-size:0.8rem; color:#8888a0; margin-top:2px; }

.section-header { display:flex; align-items:center; gap:10px; margin-bottom:0.8rem; }
.section-header .icon { font-size:1.2rem; }
.section-header .label { font-size:1.05rem; font-weight:600; color:#2d2d44; }
</style>
""", unsafe_allow_html=True)

# ─── 初始化 ──────────────────────────────────────────────
@st.cache_resource
def get_tax_matcher():
    return TaxMatcher()


# ─── Session State ──────────────────────────────────────
# NOTE: key name 'invoice_items' avoids conflict with st.session_state.items() method
def init_state():
    defaults = {
        'invoice_items': [],
        'ocr_texts': [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:0.3rem;">
    <h1 style="margin:0">📄 发票识别转换</h1>
</div>
<p style="color:#8888a0;margin-top:0;font-size:0.92rem;">
    上传图片 → OCR 识别 → 匹配税收分类 → 编辑确认 → 生成 xlsx
</p>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  IMAGE UPLOAD + OCR
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span class="icon">📷</span><span class="label">图片上传识别</span></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    '拖拽或点击上传发票图片',
    type=['jpg', 'jpeg', 'png'],
    key='file_uploader',
)

if uploaded_file is not None:
    col_img, col_res = st.columns([2, 3])

    with col_img:
        st.markdown('<div class="section-header"><span class="icon">🖼️</span><span class="label">原始图片</span></div>', unsafe_allow_html=True)
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, use_container_width=True)

    with col_res:
        st.markdown('<div class="section-header"><span class="icon">🔍</span><span class="label">OCR 识别结果</span></div>', unsafe_allow_html=True)

        with st.spinner('正在使用 Chandra 识别中...（首次运行需下载模型，请耐心等待）'):
            from ocr_service import recognize_texts
            raw_texts = recognize_texts(image)

        if raw_texts:
            with st.expander(f'📝 原始文本（{len(raw_texts)} 行）', expanded=True):
                for i, text in enumerate(raw_texts):
                    st.text(f'[{i}] {text}')

            parsed = parse_text_lines(raw_texts)
            if parsed:
                st.session_state.invoice_items = parsed
                st.success(f'识别成功，共 {len(parsed)} 个物品')
            else:
                st.warning('未能从 OCR 结果中解析出物品信息。请尝试「手动输入」。')
        else:
            st.error('OCR 未能识别出任何文字。')

st.divider()

# ═══════════════════════════════════════════════════════════
#  MANUAL INPUT
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="section-header"><span class="icon">✏️</span><span class="label">手动输入物品信息</span></div>', unsafe_allow_html=True)
st.markdown(
    '<span class="badge badge-slate">格式</span> 每行一个物品，空格分隔：<code style="color:#6366f1">规格 物品名 单位 数量 单价</code>'
    '&nbsp;&nbsp;<span class="badge badge-amber">提示</span> 总价自动计算 · 无规格填 <code style="color:#d97706">-</code>',
    unsafe_allow_html=True,
)

manual_text = st.text_area(
    '物品列表',
    value='',
    height=180,
    placeholder=(
        '示例（规格 物品名 单位 数量 单价）：\n'
        '16A 插座 个 4 15\n'
        '- 公牛有线 14座 组 4 38\n'
        '2P 空气开关 个 3 30\n'
        '30X60 平板灯 个 2 50\n'
        '- 热水器 台 1 37\n'
        '- 时控开关 个 1 55\n'
        '- 电线 米 10 5'
    ),
    key='manual_input',
    label_visibility='collapsed',
)

col_parse, _ = st.columns([1, 5])
if col_parse.button('✅ 解析文本', use_container_width=True):
    if manual_text.strip():
        import re as _re
        _known_units = {'个', '只', '把', '条', '件', '台', '套', '组', '米', '箱',
                        '盒', '包', '瓶', '罐', '块', '片', '张', '副', '对', '根',
                        '支', '卷', '袋', '桶', '升', '吨', '公斤', '千克', '克', '批',
                        '扎'}
        lines = [l.strip() for l in manual_text.strip().split('\n') if l.strip()]
        manual_items = []
        for line in lines:
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            spec_raw = parts[0]
            spec = '' if spec_raw == '-' else spec_raw
            rest = parts[1]

            # 从 rest 中解析：物品名 单位 数量 单价
            numbers = _re.findall(r'\d+\.?\d*', rest)
            if len(numbers) < 2:
                continue
            qty = float(numbers[-2])
            price = float(numbers[-1])

            # 从末尾去掉最后两个数字
            text = rest
            for n in [numbers[-1], numbers[-2]]:
                text = _re.sub(r'\s*' + _re.escape(n) + r'\s*$', '', text, count=1)
            text = text.strip()

            # 提取单位：末尾的已知单位词
            unit = '个'
            name = text
            # 先尝试双字单位
            if len(text) >= 2 and text[-2:] in _known_units:
                unit = text[-2:]
                name = text[:-2].strip()
            elif text and text[-1] in _known_units:
                unit = text[-1]
                name = text[:-1].strip()

            if not name:
                continue

            manual_items.append(Item(
                name=name, spec=spec, unit=unit,
                quantity=qty, unit_price=price, amount=qty * price,
            ))

        if manual_items:
            st.session_state.invoice_items = manual_items
            st.success(f'解析成功，共 {len(manual_items)} 个物品')
        else:
            st.error('无法解析输入内容，请检查格式。')
    else:
        st.warning('请先输入物品列表。')

# ═══════════════════════════════════════════════════════════
#  EDITOR SECTION
# ═══════════════════════════════════════════════════════════
current_items = st.session_state.invoice_items

if current_items:
    # 税收匹配（仅首次加载时自动匹配，避免覆盖手动选择）
    matcher = get_tax_matcher()
    if not any(item.tax_code for item in current_items):
        matcher.match_items(current_items)

    st.divider()

    # ── 统计卡片 ──
    total_amount = sum(item.amount for item in current_items)
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.markdown(f'<div class="stat-card"><div class="stat-value">{len(current_items)}</div><div class="stat-label">物品数量</div></div>', unsafe_allow_html=True)
    col_s2.markdown(f'<div class="stat-card"><div class="stat-value">{total_amount:.2f}</div><div class="stat-label">合计金额</div></div>', unsafe_allow_html=True)
    col_s3.markdown(f'<div class="stat-card"><div class="stat-value">1%</div><div class="stat-label">税率</div></div>', unsafe_allow_html=True)

    # ── 构建税收分类下拉选项（优先叶子节点编码） ──
    tax_names = []
    _seen = set()
    name_to_code: dict[str, str] = {}
    # 先收集所有，叶子节点覆盖父节点的编码
    for e in matcher.entries:
        n = e['name']
        if e.get('is_leaf', True) or n not in name_to_code:
            name_to_code[n] = e['code']
        if n not in _seen:
            _seen.add(n)
            tax_names.append(n)

    # ── 工具栏 ──
    st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header"><span class="icon">📋</span><span class="label">物品明细（可编辑修正）</span></div>', unsafe_allow_html=True)

    col_a, col_b, _ = st.columns([1, 1, 4])
    if col_a.button('🔄 重新匹配税收分类', use_container_width=True):
        for item in st.session_state.invoice_items:
            item.tax_code = ''
            item.tax_name = ''
        st.session_state.pop('tax_selections', None)
        if 'items_editor' in st.session_state:
            del st.session_state['items_editor']
        st.rerun()
    if col_b.button('🗑️ 清空所有物品', use_container_width=True):
        st.session_state.invoice_items = []
        st.session_state.pop('tax_selections', None)
        st.rerun()

    # ── 可编辑 DataFrame（不含税收分类列） ──
    df_data = []
    for item in current_items:
        df_data.append({
            '物品名称': item.name,
            '规格型号': item.spec,
            '单位': item.unit,
            '数量': item.quantity,
            '单价': item.unit_price,
            '总价': item.amount,
        })

    edited_df = st.data_editor(
        pd.DataFrame(df_data),
        use_container_width=True,
        num_rows='dynamic',
        key='items_editor',
    )

    # ── 税收分类选择（独立 selectbox，不受 data_editor rerun 影响） ──
    st.markdown('<div class="section-header"><span class="icon">🏷️</span><span class="label">税收分类选择</span></div>', unsafe_allow_html=True)

    # 初始化选择状态（仅首次或重新匹配时）
    if 'tax_selections' not in st.session_state or len(st.session_state.tax_selections) != len(edited_df):
        st.session_state.tax_selections = {}
        for idx, item in enumerate(current_items):
            if idx < len(edited_df):
                st.session_state.tax_selections[idx] = item.tax_name

    tax_selections = st.session_state.tax_selections

    for idx in range(len(edited_df)):
        row_name = str(edited_df.iloc[idx]['物品名称']).strip() if idx < len(edited_df) else ''
        if not row_name:
            continue

        _col_name, _col_sel = st.columns([1, 3])
        _col_name.markdown(f'**{idx+1}. {row_name}**')

        # 当前选择值
        current_sel = tax_selections.get(idx, '')

        # 构建选项列表：当前选中值 + 全量列表
        _opts = ['']
        if current_sel and current_sel not in tax_names:
            _opts.append(current_sel)
        _opts.extend(tax_names)

        _sel_idx = _opts.index(current_sel) if current_sel in _opts else 0

        selected = _col_sel.selectbox(
            f'tax_{idx}',
            options=_opts,
            index=_sel_idx,
            format_func=lambda x: '🔍 输入关键词搜索...' if not x else x,
            key=f'_tax_sel_{idx}',
            label_visibility='collapsed',
        )

        if selected:
            tax_selections[idx] = selected
            # 同步编码到 items
            if selected in name_to_code:
                current_items[idx].tax_code = name_to_code[selected]
                current_items[idx].tax_name = selected

    # ── 校验 ──
    validation_ok = True
    for idx, row in edited_df.iterrows():
        name_val = str(row.get('物品名称', '')).strip()
        qty_val = row.get('数量', 0)
        price_val = row.get('单价', 0)
        total_val = row.get('总价', 0)

        if not name_val:
            st.error(f'第 {idx+1} 行：物品名称不能为空')
            validation_ok = False
        if qty_val and price_val and total_val:
            expected = float(qty_val) * float(price_val)
            if abs(expected - float(total_val)) > max(expected * 0.01, 0.01):
                st.warning(f'第 {idx+1} 行：数量×单价={expected:.2f} ≠ 总价={total_val}')

    # ═══════════════════════════════════════════════════════
    #  GENERATE（即时生成，无需点按钮刷新）
    # ═══════════════════════════════════════════════════════
    st.divider()

    col_gen, col_preview = st.columns([1, 2])

    with col_gen:
        st.markdown('<div class="section-header"><span class="icon">📦</span><span class="label">生成文件</span></div>', unsafe_allow_html=True)

        # 即时从当前表格数据 + 税收选择生成 xlsx
        if validation_ok:
            try:
                tax_selections = st.session_state.get('tax_selections', {})
                final_items = []
                for idx, (_, row) in enumerate(edited_df.iterrows()):
                    name = str(row['物品名称'])
                    tax_name = tax_selections.get(idx, '').strip()
                    tax_code = ''

                    # 从手动选择反查编码
                    if tax_name and tax_name in name_to_code:
                        tax_code = name_to_code[tax_name]
                    # 没有手动选择则自动匹配
                    if not tax_code:
                        tax_code, tax_name = matcher.match(name)

                    final_items.append(Item(
                        name=name,
                        spec=str(row.get('规格型号', '')),
                        unit=str(row.get('单位', '个')),
                        quantity=float(row['数量']),
                        unit_price=float(row['单价']),
                        amount=float(row['总价']),
                        tax_code=tax_code,
                        tax_name=tax_name,
                    ))

                xlsx_bytes = generate_to_bytes(final_items)
                st.download_button(
                    label='⬇️ 下载电子发票 xlsx',
                    data=xlsx_bytes,
                    file_name=f'发票明细_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True,
                    type='primary',
                )
            except Exception as e:
                st.error(f'生成失败: {e}')
        else:
            st.info('请修正表格中的问题后下载')

    with col_preview:
        with st.expander('🔍 预览生成内容', expanded=True):
            tax_selections = st.session_state.get('tax_selections', {})
            for idx, (_, row) in enumerate(edited_df.iterrows()):
                spec_str = f'规格:{row["规格型号"]} | ' if row.get('规格型号') else ''
                tax_display = tax_selections.get(idx, '') or '未匹配'
                st.markdown(
                    f'<div style="padding:6px 0;border-bottom:1px solid #f0f0f6;color:#5c5c7a;">'
                    f'<b style="color:#1e1e2e">{row["物品名称"]}</b> '
                    f'<span class="badge badge-purple">{tax_display}</span><br>'
                    f'<span style="color:#8888a0;font-size:0.85rem">'
                    f'{spec_str}{row["数量"]}{row["单位"]} x {row["单价"]} = '
                    f'<b style="color:#059669">{row["总价"]}</b> | 税率:0.01</span></div>',
                    unsafe_allow_html=True,
                )

# ─── 使用说明 ──────────────────────────────────────────
st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
with st.expander('📖 使用说明'):
    st.markdown("""
    <div style="color:#5c5c7a;font-size:0.9rem;line-height:1.8">
    <b style="color:#2d2d44">操作流程</b><br>
    <span class="badge badge-purple">1</span> 上传发票图片或手动输入物品信息<br>
    <span class="badge badge-purple">2</span> 在表格中编辑、修正识别结果<br>
    <span class="badge badge-purple">3</span> 点击「生成电子发票 xlsx」<br>
    <span class="badge badge-purple">4</span> 点击「下载」保存文件<br><br>
    <b style="color:#2d2d44">输入格式</b><br>
    每行一个物品：<code style="color:#6366f1">物品名 数量 单价 总价</code><br>
    规格型号自动从物品名前缀提取<br><br>
    <span class="badge badge-amber">提示</span> 税率固定 0.01（1%） · 表格支持编辑/增删行 · 点击「重新匹配」刷新税收分类
    </div>
    """, unsafe_allow_html=True)
