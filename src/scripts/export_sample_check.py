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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Full_Accuracy_Check_Fixed.csv")

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
        models['Naive_Linearity'] = diff(u, x) * diff(v, x)
        models['Quotient_Minus_1'] = diff(u, x)*v - u*diff(v, x)
        models['Quotient_Minus_2'] = u*diff(v, x) - diff(u, x)*v
        
    elif comp['type'] == '3_term':
        u, v, w = comp['u'], comp['v'], comp['w']
        models['Naive_Linearity'] = diff(u, x) * diff(v, x) * diff(w, x)
        
    return models

def classify_hybrid(row):
    ans_str = str(row['student_expr']).replace(' ', '').lower()
    ast_str = str(row['student_ast'])
    hw_id = str(row['HW_ID'])

    if ans_str in ["", "nan"]: return "無効回答"
    ans_str = ans_str.replace(';', '')

    if 'd/dx' in ans_str: return "構文エラー：未定義記法 (d/dx)"
    if re.search(r'(?<![a-z])in\(', ans_str) or ans_str == 'in': return "構文エラー：in表記"
    if 'logx' in ans_str: return "構文エラー：括弧省略"

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

    if hw_id in PROBLEM_COMPONENTS:
        comp = PROBLEM_COMPONENTS[hw_id]
        if comp['type'] == '2_term':
            correct_expr = diff(comp['u']*comp['v'], x)
        else:
            correct_expr = diff(comp['u']*comp['v']*comp['w'], x)

        diff_val = simplify(student_eval - correct_expr)

        if diff_val == 0:
            if has_diff: return "正答プロセス：演算未完 (立式は正解)"
            else: return "正答プロセス：正解 (なぜか0点)"
        
        models = generate_naive_models(hw_id)
        for m_name, m_expr in models.items():
            if simplify(student_eval - m_expr) == 0:
                suffix = " (演算未完)" if has_diff else ""
                if m_name == 'Naive_Linearity': return f"誤概念：線形化誤認{suffix}"
                if 'Quotient' in m_name: return f"誤概念：商の微分混同{suffix}"

        if diff_val.is_number:
            return "計算ミス：定数・係数のズレ"

    top_node = ast_str.split('(')[0] if '(' in ast_str else ""
    if has_diff: return "演算未完：立式誤り (モデル不一致)"

    if hw_id in PROBLEM_COMPONENTS:
        if top_node != 'Add':
            if top_node in ['Mul', 'Pow']: return "誤概念：線形化誤認 (構造判定)"
            elif top_node in ['Symbol', 'Integer', 'Float']: return "識別不能：単一項"
        else:
            return "未分類：和の構造あり (数値不一致)"

    return "識別不能"

def create_final_check_sheet():
    print("--- 最終チェックシート作成 (ラベル補完版) ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    files = glob.glob(os.path.join(INPUT_DIR, "*_processed.csv"))
    if not files:
        print("エラー: processedデータがありません。clean_data.pyを実行してください。")
        return

    all_data = []

    for f in files:
        filename = os.path.basename(f)
        hw_id = filename.split('_')[0]
        if hw_id not in TARGET_HW_IDS: continue
        
        try:
            df = pd.read_csv(f)
            df['HW_ID'] = hw_id
            
            # カラム名の正規化
            for col in df.columns:
                if '評点' in col or 'Grade' in col or 'Score' in col: 
                    df['評点'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                elif '姓' in col or 'Name' in col:
                    df['姓'] = df[col]

            # 0点抽出
            if '評点' in df.columns:
                df_filtered = df[df['評点'] < TARGET_SCORE_MAX].copy()
                
                if len(df_filtered) > 0:
                    # ここで分類を実行（確実にラベルを作る）
                    df_filtered['Error_Category'] = df_filtered.apply(classify_hybrid, axis=1)
                    all_data.append(df_filtered)
        except Exception as e:
            print(f"スキップ: {filename} ({e})")

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # 出力カラムの選定
        output_cols = [
            'HW_ID', 
            'Error_Category',  # これが最重要
            'student_expr', 
            '姓',
            'student_ast'
        ]
        
        # 必要な列だけ抽出（なければ空文字で埋める）
        for c in output_cols:
            if c not in final_df.columns: final_df[c] = ''
            
        final_df = final_df[output_cols]
        
        # チェック欄の追加
        final_df['判定は正しいか？(〇/×)'] = ''
        final_df['訂正ラベル（×の場合）'] = ''
        final_df['備考'] = ''
        
        # ソート
        final_df = final_df.sort_values(['HW_ID', 'Error_Category'])
        
        # 保存
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"作成完了: {OUTPUT_FILE}")
        print("このファイルには確実に 'Error_Category' が含まれています。")
    else:
        print("対象データが見つかりませんでした。")

if __name__ == "__main__":
    create_final_check_sheet()