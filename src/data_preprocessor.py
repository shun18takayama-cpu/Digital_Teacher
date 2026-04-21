import pandas as pd
import glob
import re
import os
import warnings
from sympy import E, cos, exp, log, sin, srepr, Derivative
from sympy.abc import x
from sympy.parsing.sympy_parser import implicit_multiplication_application, parse_expr, standard_transformations
from sympy.utilities.exceptions import SymPyDeprecationWarning

# 警告を非表示
warnings.filterwarnings("ignore", category=SymPyDeprecationWarning)

# ==========================================
# 設定
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed_2")

# ==========================================
# 関数定義
# ==========================================
def split_stack_content(text):
    """ Moodle形式からの数式抽出とコメントの分離 """
    if pd.isna(text): return "", None
    text = str(text)
    
    match = re.search(r'ans\d+:\s*(.*?)\s*\[score\]', text)
    content = match.group(1).strip() if match else text
    
    comments = re.findall(r'/\*.*?\*/', content, flags=re.DOTALL)
    extracted_comment = " ".join(comments) if comments else None
    
    clean_expr = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    clean_expr = re.sub(r'seed:.*', '', clean_expr, flags=re.IGNORECASE)
    clean_expr = clean_expr.replace('%e', 'e').replace('%pi', 'pi').strip()
    clean_expr = clean_expr.replace(';', '')
    
    return clean_expr, extracted_comment

def normalize_and_log(expr_str):
    """
    数式の正規化を行い、結果文字列と詳細なフラグ（True/False）をPandas Seriesで返す
    """
    # 初期フラグ（すべてFalse）
    flags = {
        "flag_half_width": False,    # 全角->半角
        "flag_equation": False,      # ★追加：方程式（=の右辺抽出）
        "flag_operator": False,      # 演算子置換 (^ -> **)
        "flag_parentheses": False,   # 括弧補完 (logx -> log(x))
        "flag_derivative": False     # 微分統一 (diff -> Derivative)
    }
    
    if pd.isna(expr_str) or expr_str == "":
        return pd.Series(["", ""] + list(flags.values()))
        
    logs = []
    s = str(expr_str).strip()
    
    # ① 全角記号を半角に変換
    half_s = s.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    if s != half_s:
        logs.append("全角記号の半角化")
        flags["flag_half_width"] = True
        s = half_s

    # ② 【復活】方程式の場合、右辺だけを抽出する
    if "=" in s:
        s_new = s.split("=")[-1].strip()
        logs.append(f"方程式の除去: '='の右辺のみ抽出")
        flags["flag_equation"] = True
        s = s_new

    # ③ 演算子の置換
    replacements = {"^": "**", "*+": "+", "* +": "+"}
    for old, new in replacements.items():
        if old in s:
            s = s.replace(old, new)
            logs.append(f"演算子の置換: '{old}' -> '{new}'")
            flags["flag_operator"] = True

    # ④ 関数と変数の「()忘れ」補完
    for func in ["sin", "cos", "tan", "log", "ln"]:
        pattern = rf"\b{func}x\b"
        if re.search(pattern, s, flags=re.IGNORECASE):
            s = re.sub(pattern, f"{func}(x)", s, flags=re.IGNORECASE)
            logs.append(f"関数括弧の補完: {func}x -> {func}(x)")
            flags["flag_parentheses"] = True

    # ⑤ 微分記号を未評価クラス（Derivative）へ統一
    if "diff(" in s:
        s_new = s.replace("diff(", "Derivative(")
        if s != s_new:
            logs.append("微分表記の統一: 'diff' -> 'Derivative'")
            flags["flag_derivative"] = True
            s = s_new
    
    ddx_pattern = r"d/dx\(([^)]+)\)"
    if re.search(ddx_pattern, s):
        s = re.sub(ddx_pattern, r"Derivative(\1, x)", s)
        logs.append("微分表記の統一: 'd/dx(A)' -> 'Derivative(A, x)'")
        flags["flag_derivative"] = True
        
    # [正規化された式, ログ文字列, フラグ1, フラグ2, ...] の形で返す
    return pd.Series([s, " | ".join(logs)] + list(flags.values()))

def generate_student_ast(norm_expr):
    """ AST生成 (evaluate=False でSymPyのお節介を封印) """
    if not norm_expr or norm_expr == "": return None
    try:
        local_dict = {
            "x": x, "E": E, "e": E, "exp": exp, 
            "sin": sin, "cos": cos, "log": log, "ln": log,
            "Derivative": Derivative
        }
        transformations = standard_transformations + (implicit_multiplication_application,)
        
        expr = parse_expr(norm_expr, local_dict=local_dict, transformations=transformations, evaluate=False)
        return srepr(expr)
    except Exception as e:
        return f"ParseError: {type(e).__name__}: {str(e)}"

# ==========================================
# メイン処理
# ==========================================
def run_cleaning_pipeline():
    print(f"--- データ前処理（方程式対応・フラグ展開機能付き）を開始します ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = glob.glob(os.path.join(INPUT_DIR, "*HW*.csv"))
    
    if not files:
        print(f"エラー: {INPUT_DIR} にCSVファイルが見つかりません。")
        return

    for f in files:
        filename = os.path.basename(f)
        match = re.search(r'(HW\d+-\d+)', filename)
        hw_id = match.group(1) if match else "unknown"
        print(f"処理中: {filename}")
        
        try:
            df = pd.read_csv(f)
            
            # メタデータ保持
            cols_to_drop = ['名', 'メールアドレス', '受験完了', 'ステータス', '開始日時']
            df = df.drop(columns=[c for c in cols_to_drop if c in df.columns], errors='ignore')

            # 正解データの処理
            if '正解 1' in df.columns:
                results_correct = df['正解 1'].apply(split_stack_content)
                df['correct_expr'] = [res[0] for res in results_correct]
                df = df.drop(columns=['正解 1'])

            # 学生データの処理
            if '解答 1' in df.columns:
                # Step 1: クレンジングとコメント分離
                results_stu = df['解答 1'].apply(split_stack_content)
                df['student_expr'] = [res[0] for res in results_stu]
                df['student_comment'] = [res[1] for res in results_stu]
                
                # Step 2: 正規化と【フラグ展開】 (★flag_equationを追加)
                res_cols = ['normalized_expr', 'normalization_logs', 
                            'flag_half_width', 'flag_equation', 'flag_operator', 'flag_parentheses', 'flag_derivative']
                df[res_cols] = df['student_expr'].apply(normalize_and_log)
                
                # Step 3: AST（srepr）の生成
                df['student_ast'] = df['normalized_expr'].apply(generate_student_ast)
                
                df = df.drop(columns=['解答 1'])

            output_name = f"{hw_id}_processed.csv"
            df.to_csv(os.path.join(OUTPUT_DIR, output_name), index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"  -> エラー: {e}")

    print("--- 前処理完了: ASTと各種フラグが正常に出力されました ---")

if __name__ == "__main__":
    run_cleaning_pipeline()