import pandas as pd
import re
from sympy import sympify, srepr

# ==========================================
# 設定項目
# ==========================================
INPUT_FILE = "problem_master.csv"
OUTPUT_FILE = "problem_master_with_ast.csv"

def get_ast_structure(expr_str):
    """数式をクレンジングしてAST内部構造を文字列で返す"""
    if pd.isna(expr_str):
        return "Empty"
    
    try:
        # 1. 小文字化・ln置換・べき乗記号置換
        processed = str(expr_str).lower().replace('ln', 'log').replace('^', '**')
        
        # 2. 暗黙の掛け算の補完 (18x -> 18*x)
        processed = re.sub(r'(\d)([a-z\(])', r'\1*\2', processed)
        
        # 3. パースして構造をsrepr形式で取得
        return srepr(sympify(processed))
    except Exception as e:
        return f"Error: {str(e)}"

def run_save():
    try:
        # CSVの読み込み (BOM付きUTF-8対応)
        df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
        
        print("AST解析を開始します...")
        
        # 新しい列としてAST構造を追加
        df['問題_AST'] = df['問題 (f(x))'].apply(get_ast_structure)
        df['正答_AST'] = df['サンプル正答 (f\'(x))'].apply(get_ast_structure)
        
        # 結果をCSVに保存 (Excelでの文字化け防止のため utf-8-sig)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print(f"完了しました！保存先: {OUTPUT_FILE}")
        
    except FileNotFoundError:
        print(f"エラー: {INPUT_FILE} が見つかりません。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    run_save()