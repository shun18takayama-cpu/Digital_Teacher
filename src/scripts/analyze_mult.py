import pandas as pd
import re
import os
import glob
from sympy import symbols, diff, log, sin, exp, simplify, sympify, E, Function, Symbol

# ==========================================
# 設定
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_DIR = os.path.join(BASE_DIR, "results", "JSISE")

TARGET_HW_IDS = ['HW01-05', 'HW03-01', 'HW03-05']
TARGET_SCORE_MAX = 0.1 

x = symbols('x')
PROBLEM_COMPONENTS = {
    'HW01-05': {'type': '2_term', 'u': x, 'v': log(x)},
    'HW03-01': {'type': '2_term', 'u': exp(x), 'v': log(x)},
    'HW03-05': {'type': '3_term', 'u': x, 'v': log(x), 'w': sin(x)}
}

def generate_naive_models(hw_id):
    if hw_id not in PROBLEM_COMPONENTS: return {}
    comp = PROBLEM_COMPONENTS[hw_id]
    models = {}
    
    if comp['type'] == '2_term':
        u, v = comp['u'], comp['v']
        # 1. 線形化誤認: (uv)' = u'v'
        models['Naive_Linearity'] = diff(u, x) * diff(v, x)
        
        # 2. 商の微分混同 (パターン拡充)
        # パターンA: u'v - uv' (本来の分子)
        models['Quotient_Minus_1'] = diff(u, x)*v - u*diff(v, x)
        # パターンB: uv' - u'v (順序逆転)
        models['Quotient_Minus_2'] = u*diff(v, x) - diff(u, x)*v
        
    elif comp['type'] == '3_term':
        u, v, w = comp['u'], comp['v'], comp['w']
        # 線形化誤認: (uvw)' = u'v'w'
        models['Naive_Linearity'] = diff(u, x) * diff(v, x) * diff(w, x)
        
    return models

def classify_hybrid(row):
    ans_str = str(row['student_expr']).replace(' ', '').lower()
    ast_str = str(row['student_ast'])
    hw_id = str(row['HW_ID'])

    # --- Level 0: 構文フィルター (Syntax Check) ---
    if ans_str in ["", "nan"]: return "無効回答"

    # ★修正1: セミコロン除去 (HW03-05対策)
    ans_str = ans_str.replace(';', '')

    # ★修正2: d/dx は構文エラーとして明確に弾く
    if 'd/dx' in ans_str: return "構文エラー：未定義記法 (d/dx)"
    if re.search(r'(?<![a-z])in\(', ans_str) or ans_str == 'in': return "構文エラー：in表記"
    if 'logx' in ans_str: return "構文エラー：括弧省略"

    # --- Level 1: 計算準備 ---
    has_diff = "diff" in ast_str or "derivative" in ast_str.lower() or "diff" in ans_str
    
    try:
        local_dict = {'e': E}
        parse_target = ans_str.replace('^', '**').replace('ln', 'log')
        parse_target = re.sub(r'(\d)([a-z\(])', r'\1*\2', parse_target)
        parse_target = re.sub(r'(\))([a-z\d\(])', r'\1*\2', parse_target)
        
        student_raw = sympify(parse_target, locals=local_dict)
        student_eval = student_raw.doit() 
    except Exception:
        return "構文エラー：数式解析不能"

    # --- Level 2: 数値的な照合 (Value Comparison) ---
    if hw_id in PROBLEM_COMPONENTS:
        # 正解との照合
        comp = PROBLEM_COMPONENTS[hw_id]
        if comp['type'] == '2_term':
            correct_expr = diff(comp['u']*comp['v'], x)
        else:
            correct_expr = diff(comp['u']*comp['v']*comp['w'], x)

        diff_val = simplify(student_eval - correct_expr)

        # A. 正解と一致
        if diff_val == 0:
            if has_diff: return "正答プロセス：演算未完 (立式は正解)"
            else: return "正答プロセス：正解 (なぜか0点)"
        
        # ★修正3: 判定順序の変更 (誤概念チェックを先に！)
        # これにより log(x)-1 が「定数のズレ」ではなく「商の混同」になる
        models = generate_naive_models(hw_id)
        for m_name, m_expr in models.items():
            if simplify(student_eval - m_expr) == 0:
                suffix = " (演算未完)" if has_diff else ""
                if m_name == 'Naive_Linearity': return f"誤概念：線形化誤認{suffix}"
                if 'Quotient' in m_name: return f"誤概念：商の微分混同{suffix}"

        # B. 定数のズレ (モデル不一致の後にチェック)
        if diff_val.is_number:
            return "計算ミス：定数・係数のズレ"

    # --- Level 3: 構造による判定 (Shape Analysis) ---
    top_node = ast_str.split('(')[0] if '(' in ast_str else ""
    
    if has_diff: 
        return "演算未完：立式誤り (モデル不一致)"

    if hw_id in PROBLEM_COMPONENTS:
        if top_node != 'Add':
            if top_node in ['Mul', 'Pow']: return "誤概念：線形化誤認 (構造判定)"
            elif top_node in ['Symbol', 'Integer', 'Float']: return "識別不能：単一項"
        else:
            # ★修正4: ラベル名をより事実に即したものに
            return "未分類：和の構造あり (数値不一致)"

    return "識別不能"

# ==========================================
# メイン実行部
# ==========================================
def run_analysis():
    print(f"--- JSISE向け分析フェーズ (v4出力版) ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    files = glob.glob(os.path.join(INPUT_DIR, "*_processed.csv"))
    if not files:
        print(f"エラー: データなし")
        return

    all_results = []

    for f in files:
        filename = os.path.basename(f)
        hw_id = filename.split('_')[0]
        if hw_id not in TARGET_HW_IDS: continue
            
        try:
            df = pd.read_csv(f)
            df['HW_ID'] = hw_id
            
            # カラム名統一 (元のロジックを維持)
            rename_map = {}
            for col in df.columns:
                if '評点' in col or 'Grade' in col or 'Score' in col: rename_map[col] = '評点'
                elif '所要時間' in col or 'Time' in col or '継続時間' in col: rename_map[col] = '経過時間'
            df = df.rename(columns=rename_map)

            if '評点' in df.columns:
                df['評点'] = pd.to_numeric(df['評点'], errors='coerce').fillna(0)
                df_filtered = df[df['評点'] < TARGET_SCORE_MAX].copy()
                
                print(f"分析中: {hw_id} (0点抽出: {len(df_filtered)}件)")
                
                if len(df_filtered) > 0:
                    df_filtered['Error_Category'] = df_filtered.apply(classify_hybrid, axis=1)
                    all_results.append(df_filtered)

        except Exception as e:
            print(f"エラー {filename}: {e}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        
        # ★元の出力順序ロジックを維持 (メタデータ保持)
        target_order = ['HW_ID', '姓', '評点', '経過時間', 'student_expr', 'student_comment', 'Error_Category', 'correct_expr', 'student_ast']
        cols = [c for c in target_order if c in final_df.columns] + [c for c in final_df.columns if c not in target_order]
        final_df = final_df[cols]
        
        # v4として出力
        output_csv = os.path.join(OUTPUT_DIR, "JSISE_final_analysis_v4.csv")
        final_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        
        # 集計表の出力
        summary = final_df.groupby(['HW_ID', 'Error_Category']).size().reset_index(name='Count')
        pivot = summary.pivot(index='Error_Category', columns='HW_ID', values='Count').fillna(0).astype(int)
        pivot.to_csv(os.path.join(OUTPUT_DIR, "JSISE_summary_count_v4.csv"), encoding='utf-8-sig')
        
        # パーセント表
        pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100
        pivot_pct.to_csv(os.path.join(OUTPUT_DIR, "JSISE_summary_percent_v4.csv"), encoding='utf-8-sig')

        print(f"\n--- 完了 ---")
        print(f"詳細データ: {output_csv}")
        print(f"集計(件数): JSISE_summary_count_v4.csv")
        print(f"集計(割合): JSISE_summary_percent_v4.csv")
    else:
        print("警告: データなし")

if __name__ == "__main__":
    run_analysis()