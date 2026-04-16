import streamlit as st
import pandas as pd
import os
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import re

# ==========================================
# ページ設定とパス設定
# ==========================================
st.set_page_config(page_title="AST 目視評価ツール", layout="wide")

DATA_FILE = "results/levenshtein/HW03-01_levenshtein.csv"

# ==========================================
# 補助関数群
# ==========================================
def load_data():
    if not os.path.exists(DATA_FILE):
        st.error(f"ファイルが見つかりません: {DATA_FILE}")
        st.stop()
    return pd.read_csv(DATA_FILE)

def save_data(df):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def normalize_expr(s: str) -> str:
    s = str(s).strip()
    s = s.replace("^", "**").replace("*+", "+").replace("* +", "+")
    s = re.sub(r"\bsinx\b", "sin(x)", s, flags=re.IGNORECASE)
    s = re.sub(r"\bcosx\b", "cos(x)", s, flags=re.IGNORECASE)
    if "=" in s:
        s = s.split("=")[-1].strip()
    return s

# ==========================================
# 【新機能】AST差分ハイライト用 カスタムDOTジェネレータ
# ==========================================
def generate_diff_graph(main_expr_str, compare_expr_str=None):
    """
    メインの数式をツリー化し、比較対象の数式と構造が違うノードを赤くハイライトする。
    """
    try:
        t = standard_transformations + (implicit_multiplication_application,)
        main_ast = parse_expr(normalize_expr(main_expr_str), transformations=t)
        
        comp_ast = None
        if compare_expr_str and str(compare_expr_str) != 'nan':
            try:
                comp_ast = parse_expr(normalize_expr(compare_expr_str), transformations=t)
            except:
                pass # 比較対象がパースエラーの場合はすべて赤色になるようにする

        # DOT言語（Graphviz）のヘッダー定義
        lines = [
            'digraph AST {',
            'graph [rankdir=TD, bgcolor=transparent];',
            'node [fontname="Helvetica", shape=box, style="rounded,filled", fillcolor="white"];',
            'edge [color="#666666"];'
        ]
        
        counter = [0]

        def traverse(n_main, n_comp):
            c_id = counter[0]
            counter[0] += 1
            
            # --- 差分（エラー）判定ロジック ---
            is_diff = False
            if n_comp is None:
                is_diff = True  # 比較対象にこのノードが存在しない
            elif type(n_main) != type(n_comp):
                is_diff = True  # ノードの種類（Add, Mul等）が違う
            elif not n_main.args and not n_comp.args:
                if n_main != n_comp:
                    is_diff = True  # 葉ノード（値）が違う
                    
            # --- ノードのラベル生成 ---
            if getattr(n_main, 'args', []):
                label = getattr(n_main.func, "__name__", type(n_main).__name__)
            else:
                label = str(n_main)
                
            label = label.replace('"', '\\"') # エスケープ処理
            
            # --- スタイル適用（違う場合は赤くする） ---
            if is_diff:
                style = 'fillcolor="#ffe6e6", color="#ff0000", penwidth=2, fontcolor="#cc0000"'
            else:
                style = 'fillcolor="#f8f9fa", color="#333333", penwidth=1'
                
            lines.append(f'  node_{c_id} [label="{label}", {style}];')
            
            # --- 子ノードの再帰処理 ---
            for i, arg_m in enumerate(n_main.args):
                # 比較対象の子ノードを同じインデックスで取得
                arg_c = n_comp.args[i] if n_comp and hasattr(n_comp, 'args') and i < len(n_comp.args) else None
                child_id = traverse(arg_m, arg_c)
                lines.append(f'  node_{c_id} -> node_{child_id};')
                
            return c_id

        traverse(main_ast, comp_ast)
        lines.append("}")
        return "\n".join(lines)
        
    except Exception as e:
        return None

# ==========================================
# メインアプリケーション
# ==========================================
def main():
    st.title("🌳 AST 誤答分析 - 目視評価ツール")

    df = load_data()
    
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0

    total_records = len(df)
    current_idx = st.session_state.current_index

    if total_records == 0:
        st.warning("評価するデータがありません。")
        st.stop()

    # 上部ナビゲーション
    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
    with col_nav1:
        if st.button("⬅️ 前のデータ") and current_idx > 0:
            st.session_state.current_index -= 1
            st.rerun()
    with col_nav2:
        st.markdown(f"<h3 style='text-align: center;'>データ {current_idx + 1} / {total_records} 件目</h3>", unsafe_allow_html=True)
        st.progress((current_idx + 1) / total_records)
    with col_nav3:
        if st.button("次のデータ ➡️") and current_idx < total_records - 1:
            st.session_state.current_index += 1
            st.rerun()

    row = df.iloc[current_idx]
    
    st.markdown("---")
    st.markdown(f"**学生ID**: {row.get('学生ID', '不明')} ｜ **ステータス**: `{row.get('ステータス', 'N/A')}`")
    
    col_metric1, col_metric2 = st.columns(2)
    col_metric1.metric("トークン距離 (Levenshtein)", row.get('トークン距離', 'N/A'))
    col_metric2.metric("木距離 (TED)", row.get('木距離(TED)', 'N/A'))
    st.markdown("---")

    # メインパネル：左右にASTツリーを表示（互いに差分をハイライト）
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("✅ 正答モデル")
        st.code(row['正答式'], language="python")
        # 正答をメインに、学生の解答と比較（学生が欠落させたノードが赤くなる）
        dot_corr = generate_diff_graph(row['正答式'], row['学生の解答'])
        if dot_corr:
            st.graphviz_chart(dot_corr, use_container_width=True)
        else:
            st.error("図の生成に失敗しました")

    with col_right:
        st.subheader("❌ 学生の解答")
        st.code(row['学生の解答'], language="python")
        # 学生をメインに、正答と比較（学生が余分に追加・間違えたノードが赤くなる）
        dot_stud = generate_diff_graph(row['学生の解答'], row['正答式'])
        if dot_stud:
            st.graphviz_chart(dot_stud, use_container_width=True)
        else:
            st.warning("構文エラーのため図が生成できません")

    st.markdown("---")

    # 下部パネル：入力フォーム
    st.subheader("📝 評価入力")
    
    # 初期値の安全な取得（空欄やNaNの場合は未評価として扱う）
    current_eval = str(row.get('目視判定', ''))
    try:
        default_score = int(float(current_eval))
    except ValueError:
        default_score = 0 # 評価なしのデフォルトは0など任意

    current_comment = str(row.get('コメント', ''))
    if current_comment == 'nan': current_comment = ''

    with st.form(key=f"eval_form_{current_idx}"):
        # 【変更点】最小値を -1 に変更し、ラベルもわかりやすく
        eval_score = st.slider(
            "目視による構造的距離スコア (-1: エラー/評価不能, 0: 完全一致 〜 10: 全く違う)", 
            min_value=-1, 
            max_value=10, 
            value=default_score
        )
        
        eval_comment = st.text_area("評価コメント（何が間違っているか等）", value=current_comment)
        submit_button = st.form_submit_button(label="💾 保存して次へ")

    # 途中終了ボタン
    st.markdown("<br>", unsafe_allow_html=True)
    col_end1, col_end2 = st.columns([3, 1])
    with col_end2:
        if st.button("🛑 途中保存して終了する", type="primary"):
            st.success("ターミナルで `Ctrl + C` を押してサーバーを停止してください。")
            st.stop()

    if submit_button:
        df.at[current_idx, '目視判定'] = eval_score
        df.at[current_idx, 'コメント'] = eval_comment
        
        save_data(df)
        st.success("保存しました！")
        
        if current_idx < total_records - 1:
            st.session_state.current_index += 1
            st.rerun()
        else:
            st.balloons()
            st.info("すべての評価が完了しました！")

if __name__ == "__main__":
    main()