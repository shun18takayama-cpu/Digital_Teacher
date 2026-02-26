import pandas as pd
import glob
import re
import os
import warnings
from sympy import sympify, srepr, Function, Symbol
from sympy.utilities.exceptions import SymPyDeprecationWarning

# 警告を非表示
warnings.filterwarnings("ignore", category=SymPyDeprecationWarning)

# ==========================================
# 設定
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = os.path.join(BASE_DIR, "data", "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")

# ==========================================
# 関数定義
# ==========================================
def split_stack_content(text):
    """ 数式とコメントを分離 """
    if pd.isna(text): return "", None
    text = str(text)
    
    # ans1: ... [score] の形式から抽出
    match = re.search(r'ans\d+:\s*(.*?)\s*\[score\]', text)
    content = match.group(1).strip() if match else text
    
    # コメント抽出
    comments = re.findall(r'/\*.*?\*/', content, flags=re.DOTALL)
    extracted_comment = " ".join(comments) if comments else None
    
    # 数式クリーニング
    clean_expr = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    clean_expr = re.sub(r'seed:.*', '', clean_expr, flags=re.IGNORECASE)
    clean_expr = clean_expr.replace('%e', 'e').replace('%pi', 'pi').strip()
    
    # ★修正点: セミコロンを除去 (HW03-05対策)
    clean_expr = clean_expr.replace(';', '')
    
    return clean_expr, extracted_comment

def generate_student_ast(formula):
    """ AST生成 (diffは計算せず構造として保持) """
    if not formula or formula == "": return None
    try:
        # 表記統一
        processed = formula.lower().replace('ln', 'log').replace('^', '**')
        # 暗黙の掛け算を補完
        processed = re.sub(r'(\d)([a-z\(])', r'\1*\2', processed)
        processed = re.sub(r'(\))([a-z\d\(])', r'\1*\2', processed)
        
        # diffを関数として定義
        local_dict = {
            'diff': Function('diff'), 
            'derivative': Function('diff'), 
            'd/dx': Function('diff'),
            'x': Symbol('x'), 
            'e': Symbol('e')
        }
        # パース実行
        expr = sympify(processed, locals=local_dict, evaluate=False)
        return srepr(expr)
    except Exception as e:
        # パース失敗時はエラー内容を文字列で返す
        return f"ParseError: {e}"

# ==========================================
# メイン処理
# ==========================================
def run_cleaning_pipeline():
    print(f"--- データ前処理（セミコロン除去対応版）を開始します ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = glob.glob(os.path.join(INPUT_DIR, "*HW*.csv"))
    
    if not files:
        print(f"エラー: {INPUT_DIR} にCSVファイルがありません。")
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

            # 正解データ
            if '正解 1' in df.columns:
                results_correct = df['正解 1'].apply(split_stack_content)
                df['correct_expr'] = [res[0] for res in results_correct]
                df = df.drop(columns=['正解 1'])

            # 学生データ
            if '解答 1' in df.columns:
                results_stu = df['解答 1'].apply(split_stack_content)
                df['student_expr'] = [res[0] for res in results_stu]
                df['student_comment'] = [res[1] for res in results_stu]
                # ここでAST生成（セミコロン除去済みの student_expr を使う）
                df['student_ast'] = df['student_expr'].apply(generate_student_ast)
                df = df.drop(columns=['解答 1'])

            output_name = f"{hw_id}_processed.csv"
            df.to_csv(os.path.join(OUTPUT_DIR, output_name), index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"  -> エラー: {e}")

    print("--- 前処理完了: ASTが正常に再生成されました ---")

if __name__ == "__main__":
    run_cleaning_pipeline()