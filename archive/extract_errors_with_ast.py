import pandas as pd
import re
import os
from sympy import sympify, srepr

# ==========================================
# 設定項目
# ==========================================
# 抽出対象の宿題ID（ご指定の4題）
TARGET_IDS = ['HW01-03', 'HW01-05', 'HW03-01', 'HW03-05']

# 入力ファイルのディレクトリ（実行場所と同じなら "."）
INPUT_DIR = "./data/processed"

# 出力ファイル名（積の微分の誤答を抜き出したことが分かる名前）
OUTPUT_FILE = "product_rule_errors_extracted.csv"

# ==========================================
# 関数定義
# ==========================================

def get_ast_structure(expr_str):
    """数式文字列をクレンジングしてAST構造(srepr)を返す"""
    if pd.isna(expr_str) or str(expr_str).strip() == "":
        return "Empty"
    
    try:
        # 1. 前処理: 小文字化 (SIN -> sin)
        processed = str(expr_str).lower()
        # 2. 前処理: ln -> log
        processed = processed.replace('ln', 'log')
        # 3. 前処理: べき乗記号の置換 (^ -> **)
        processed = processed.replace('^', '**')
        # 4. 前処理: 暗黙の掛け算の補完 (例: 18x -> 18*x)
        processed = re.sub(r'(\d)([a-z\(])', r'\1*\2', processed)
        
        # 5. パースの実行 (eを定数として扱いたい場合は別途辞書が必要だが、まずは構造取得を優先)
        parsed_expr = sympify(processed)
        
        # 6. AST構造を文字列で返す
        return srepr(parsed_expr)
    except Exception as e:
        return f"Error: {str(e)}"

def extract_target_errors():
    print(f"--- 誤答抽出処理を開始します（対象: {TARGET_IDS}） ---")
    
    all_errors = []
    total_count = 0
    
    for hw_id in TARGET_IDS:
        # ファイル名を構築
        filename = f"{hw_id}_processed.csv"
        filepath = os.path.join(INPUT_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"スキップ: ファイルが見つかりません -> {filename}")
            continue
            
        try:
            # CSV読み込み
            df = pd.read_csv(filepath)
            
            # スコア列の特定
            score_cols = [c for c in df.columns if "評点" in c or "Score" in c]
            if not score_cols:
                print(f"警告: {filename} にスコア列が見つかりません。")
                continue
            score_col = score_cols[0]
            
            # 誤答（10点未満）をフィルタリング
            # 数値変換できないものは0点（誤答）扱いとする
            df[score_col] = pd.to_numeric(df[score_col], errors='coerce').fillna(0)
            error_rows = df[df[score_col] < 10.0].copy()
            
            if len(error_rows) > 0:
                print(f"抽出: {filename} から {len(error_rows)} 件の誤答")
                
                # 必要な情報の追加
                error_rows['HW_ID'] = hw_id
                
                # AST構造の生成と追加
                print(f"  -> AST構造を生成中...")
                error_rows['Student_AST'] = error_rows['解答 1'].apply(get_ast_structure)
                
                all_errors.append(error_rows)
                total_count += len(error_rows)
            else:
                print(f"情報: {filename} に誤答はありませんでした。")
                
        except Exception as e:
            print(f"エラー: {filename} の処理中に問題が発生しました: {e}")

    # 結果の保存
    if all_errors:
        final_df = pd.concat(all_errors, ignore_index=True)
        
        # カラムの整理（見やすい順序に）
        # 存在しないカラムがある場合のエラーを防ぐため、intersectionをとる
        base_cols = ['HW_ID', 'Student_AST', '解答 1', '正解 1']
        existing_cols = [c for c in base_cols if c in final_df.columns]
        other_cols = [c for c in final_df.columns if c not in base_cols]
        final_cols = existing_cols + other_cols
        
        final_df = final_df[final_cols]
        
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print("-" * 30)
        print(f"完了！ 合計 {total_count} 件の誤答データを保存しました。")
        print(f"保存先: {OUTPUT_FILE}")
    else:
        print("指定された条件の誤答データは見つかりませんでした。")

if __name__ == "__main__":
    extract_target_errors()