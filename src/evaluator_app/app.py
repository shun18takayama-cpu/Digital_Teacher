import streamlit as st
import pandas as pd
import os
import sys

# SymPyからのツール
from sympy import latex, srepr
from sympy.printing.dot import dotprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.ast_analyzer import ASTAnalyzer

st.set_page_config(page_title="AST Annotation Tool", layout="wide")

# --- ユーティリティ：ASTをシンプルなテーブル形式にする ---
def flatten_ast_to_simple_list(expr):
    """ASTをスキャンして、階層をインデント文字列で表現したシンプルなリストを作る"""
    nodes = []
    def walk(node, depth=0):
        node_type = type(node).__name__
        label = getattr(node.func, "__name__", node_type) if hasattr(node, "func") else str(node)
        
        # 🌟 「階層を分ける」のではなく、一つの文字列としてインデントを表現
        indent_str = "　" * depth + "└─ " if depth > 0 else ""
        nodes.append({
            "ノード構造": f"{indent_str}{label}",
            "型": node_type
        })
        
        if hasattr(node, "args"):
            for arg in node.args:
                walk(arg, depth + 1)
    
    walk(expr)
    return pd.DataFrame(nodes)

# --- 初期準備 ---
@st.cache_resource
def get_analyzer():
    return ASTAnalyzer()

analyzer = get_analyzer()

@st.cache_resource
def get_template_asts():
    templates = {
        "展開型": "e^x*log(x) + e^x/x",
        "因数分解型": "e^x*(log(x) + 1/x)",
        "通分型": "(x*e^x*log(x) + e^x) / x"
    }
    parsed = {}
    for name, expr in templates.items():
        parsed[name] = analyzer.process_expression(expr)
    return templates, parsed

TEMPLATES_EXPR, TEMPLATES_DATA = get_template_asts()

# --- メイン処理 ---
st.title("🌳 AST アノテーション・ダッシュボード")

csv_path = os.path.join("results", "levenshtein", "HW03-01_eval_multitemplate.csv")

if not os.path.exists(csv_path):
    st.error(f"❌ ファイルが見つかりません: {csv_path}")
    st.stop()

if 'df' not in st.session_state:
    st.session_state.df = pd.read_csv(csv_path)
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

df = st.session_state.df
current_idx = st.session_state.current_idx

# --- 🔄 ナビゲーション ---
col_prev, col_count, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("⬅️ 前の解答", use_container_width=True, disabled=(current_idx == 0)):
        st.session_state.current_idx -= 1
        st.rerun()
with col_count:
    st.markdown(f"<h4 style='text-align: center;'>{current_idx + 1} / {len(df)} 件目</h4>", unsafe_allow_html=True)
with col_next:
    if st.button("次の解答 ➡️", use_container_width=True, disabled=(current_idx == len(df) - 1)):
        st.session_state.current_idx += 1
        st.rerun()

st.markdown("---")

row = df.iloc[current_idx]
status = row.get('ステータス', '')
score = row.get('元のスコア', -1)
icon = "🟢" if score == 10 else "🔴" if score == 0 else "⚪"

# --- 🎓 学生情報ヘッダー ---
st.subheader(f"{icon} 学生ID: {row.get('学生ID', '不明')} （システム評点: {score}点）")

if status == "Error":
    st.error("解析エラー")
    st.code(row.get('学生_正規化', ''), language="python")
else:
    # 🌟 木距離を大々的に表示
    best_match = row.get('推測される意図', '展開型')
    target_models = list(TEMPLATES_DATA.keys())
    default_index = target_models.index(best_match) if best_match in target_models else 0
    selected_model = st.radio("目標モデルを選択：", target_models, index=default_index, horizontal=True)
    
    dist = row.get(selected_model, -1)
    dist_color = "#28a745" if dist == 0 else "#dc3545" if dist > 3 else "#ffc107"
    
    st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <p style="margin: 0; color: #555;">選択モデルとの木距離</p>
            <h1 style="margin: 0; font-size: 5rem; color: {dist_color};">{int(dist)}</h1>
        </div>
    """, unsafe_allow_html=True)

    # --- 📐 数式比較セクション（TeX ＆ 生入力） ---
    st.markdown("### 📐 数式比較")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.info(f"**目標モデル ({selected_model})**")
        target_sympy = TEMPLATES_DATA[selected_model]["sympy_expr"]
        if target_sympy:
            st.latex(latex(target_sympy))
            st.caption("正規化された数式")
            st.code(TEMPLATES_EXPR[selected_model], language="python") # 🌟 目標の生入力も表示
    with l_col2:
        st.success("**学生の解答**")
        student_norm = str(row.get('学生_正規化', ''))
        stud_result = analyzer.process_expression(student_norm)
        student_sympy = stud_result.get("sympy_expr")
        if student_sympy:
            st.latex(latex(student_sympy))
            st.caption("正規化された数式（生徒入力）")
            st.code(student_norm, language="python") # 🌟 生徒の生入力も表示

    # --- 🌳 木構造比較セクション ---
    st.markdown("### 🌳 AST構造比較")
    # 🌟 デフォルトを「図解表示」に変更し、テーブルを後に配置
    tab1, tab2 = st.tabs(["図解表示 (Graphviz)", "📊 シンプルテーブル表示"])
    
    with tab1:
        gcol1, gcol2 = st.columns(2)
        with gcol1:
            st.graphviz_chart(dotprint(target_sympy))
        with gcol2:
            if student_sympy:
                st.graphviz_chart(dotprint(student_sympy))
            
    with tab2:
        # 🌟 文字列として階層を表現したシンプルなテーブル
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            st.markdown("**目標のノードリスト**")
            st.dataframe(flatten_ast_to_simple_list(target_sympy), use_container_width=True, hide_index=True)
        with tcol2:
            st.markdown("**学生のノードリスト**")
            if student_sympy:
                st.dataframe(flatten_ast_to_simple_list(student_sympy), use_container_width=True, hide_index=True)

# --- 📝 アノテーション ---
st.markdown("---")
st.markdown("### 📝 主観アノテーション")
curr_eval = row.get('評価値', -1)
if pd.isna(curr_eval) or str(curr_eval).strip() == "": curr_eval = -1
else: curr_eval = int(curr_eval)

new_eval = st.slider("評価値（-1:未評価, 0:完全一致）", -1, 15, curr_eval)
new_comment = st.text_area("分析・目視コメント", value=str(row.get('コメント', '') if not pd.isna(row.get('コメント', '')) else ""))

if st.button("💾 このデータを保存して次へ", type="primary", use_container_width=True):
    st.session_state.df.at[current_idx, '評価値'] = new_eval
    st.session_state.df.at[current_idx, 'コメント'] = new_comment
    st.session_state.df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    st.success("保存しました")