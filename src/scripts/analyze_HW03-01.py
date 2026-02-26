import pandas as pd
import re
import os
import sys
from sympy import symbols, parse_expr, Add, Mul, Pow, exp, log, E, simplify
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application

# -----------------------------------------------------------------------------
# 1. データの読み込み設定
# -----------------------------------------------------------------------------
# プロジェクトのルートディレクトリを特定 (src/scripts/../../ -> C:/Digital_Teacher)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../"))

# 入力データのパス (data/raw/ フォルダにある前提)
input_csv_path = os.path.join(project_root, "data", "raw", "微分積分学Ⅰ 2024（SUI）-HW03-01-解答.csv")
# 出力データのパス (results/analysis/ フォルダに出力)
output_dir = os.path.join(project_root, "results", "analysis")
os.makedirs(output_dir, exist_ok=True)
output_csv_path = os.path.join(output_dir, "analysis_HW03-01_result.csv")

print(f"読み込みファイル: {input_csv_path}")

try:
    df = pd.read_csv(input_csv_path, encoding='utf-8')
except UnicodeDecodeError:
    df = pd.read_csv(input_csv_path, encoding='cp932')
except FileNotFoundError:
    print("エラー: CSVファイルが見つかりません。パスを確認してください。")
    sys.exit()

# -----------------------------------------------------------------------------
# 2. データクリーニング関数
# -----------------------------------------------------------------------------
def clean_and_parse(text):
    if not isinstance(text, str):
        return None
    
    # 数式部分の抽出
    match = re.search(r'ans1:\s*(.*?)\s*(?:\[score\]|;)', text)
    if not match:
        return None
    formula_str = match.group(1).strip()
    
    # 強力な前処理 (翻訳)
    formula_str = re.sub(r'/\*.*?\*/', '', formula_str) # コメント削除
    if "diff" in formula_str or "d/dx" in formula_str:
        return None 

    # 数学記号の正規化
    formula_str = formula_str.replace('^', '**')
    formula_str = formula_str.replace('ln', 'log')
    formula_str = formula_str.replace('%e', 'E')
    formula_str = formula_str.replace('e**', 'E**')
    
    # SymPyでパース
    try:
        x = symbols('x')
        transformations = (standard_transformations + (implicit_multiplication_application,))
        expr = parse_expr(formula_str, transformations=transformations)
        return expr
    except:
        return None

print("データクリーニングとパースを実行中...")
df['解析用数式'] = df['解答 1'].apply(clean_and_parse)

# -----------------------------------------------------------------------------
# 3. 診断ロジック (差分による成分検証法)
# -----------------------------------------------------------------------------
x = symbols('x')

# 問題設定: f(x) = e^x * log(x)
target_A = exp(x) * log(x)  # (e^x)' * log(x)
target_B = exp(x) / x       # e^x * (log(x))'
target_total = target_A + target_B

def diagnose_structure(student_expr):
    if student_expr is None:
        return "解析不可 (Parse Error)"

    # 1. 最終的な正解との一致確認 (数学的等価性)
    is_correct_value = False
    try:
        if simplify(student_expr - target_total) == 0:
            is_correct_value = True
    except:
        pass

    # 2. 構造・成分分析
    has_part_A = False
    has_part_B = False
    
    try:
        # Aを含んでいるか？
        if student_expr.has(target_A) or simplify(student_expr - target_A).has(target_B):
             has_part_A = True
        
        # Bを含んでいるか？
        if student_expr.has(target_B) or simplify(student_expr - target_B).has(target_A):
             has_part_B = True
             
        # 項ごとの厳密チェック (展開形対応)
        expanded = student_expr.expand()
        terms = expanded.args if isinstance(expanded, Add) else [expanded]
        
        for term in terms:
            if simplify(term - target_A) == 0:
                has_part_A = True
            elif simplify(term - target_B) == 0:
                has_part_B = True
            
    except:
        pass

    # 3. 判定ロジック
    if is_correct_value:
        if has_part_A and has_part_B:
            return "◎ 完璧 (構造も値も正解)"
        else:
            return "〇 正解 (値は合うが構造特定できず/展開済み)"
            
    if has_part_A and not has_part_B:
        return "△ 部分点 (e^xの微分はできている)"
    if not has_part_A and has_part_B:
        return "△ 部分点 (log(x)の微分はできている)"
    
    return "× 不正解"

print("誤答診断を実行中...")
df['診断結果'] = df['解析用数式'].apply(diagnose_structure)

# 結果の保存
df.to_csv(output_csv_path, encoding='utf-8-sig', index=False)
print(f"分析完了！ 結果を保存しました: {output_csv_path}")

# 結果の一部を表示 (確認用)
print("\n--- 結果プレビュー ---")
print(df[['解答 1', '診断結果']].head(10))