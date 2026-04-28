import pandas as pd
import os
import sys
from sympy import Symbol

# =============================================================================
# 新しい「正準化パーサー」をインポート（ここが全ての入り口！）
# =============================================================================
# --- 通常モード（生徒の生の思考を維持） ---
from src.core.parser.expression_parser import safe_parse

# --- 実験モード（強制ソートを適用してTEDのズレを消す） ---
# 実験したい時は上の行をコメントアウトし、下の行を有効にしてください
#from src.core.parser.experimental_parser import safe_parse

from src.core.generator.rules.product_rules import apply_product_rule
from src.core.evaluator.distance_ted import calculate_ted
from src.core.evaluator.distance_hungarian import calculate_hungarian_ted
from src.core.evaluator.distance_leven import calculate_levenshtein

INPUT_CSV = "data/answers/processed_2/HW03-01_processed.csv"
OUTPUT_DIR = "results"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "HW03-01_evaluation_report_v8_experimental.csv")

def run_evaluation_pipeline():
    print(f"--- Digital Teacher 評価パイプライン (Rev 3.0 正準化対応版) 起動 ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_CSV):
        print(f"エラー: 入力ファイルが見つかりません -> {INPUT_CSV}")
        return
    
    df = pd.read_csv(INPUT_CSV)
    x = Symbol('x')
    results = []

    # =========================================================================
    # ★ 先生（正解）側の準備
    # =========================================================================
    # CSVの correct_expr は「微分の結果」が入っているため、ここでは「元の問題（種）」を定義します。
    # (将来的な課題: 問題ごとにこの「種」を別ファイル管理する機構を作ります)
    problem_seed_str = "e**x * log(x)" 
    
    # 先生の式も、全く同じ safe_parse を通して「正準形（expなど）」に強制変換
    model_expr = safe_parse(problem_seed_str)
    
    # Generatorに渡し、複数の正準形パターンを生成
    templates = apply_product_rule(model_expr, x)

    print(f"【Generator生成パターン】")
    for name, expr in templates.items():
        print(f"  - {name}: {expr}")
    print("-" * 50)

    # =========================================================================
    # ★ 学生側の評価ループ
    # =========================================================================
    for index, row in df.iterrows():
        student_id = row.get('姓', f"ID_{index}")
        target_expr = str(row.get('normalized_expr', ""))
        
        result_row = row.to_dict()

        # 学生の式も safe_parse を通して「正準形」に強制変換
        student_ast = safe_parse(target_expr)
        
        best_ted_dist = 999
        best_ted_pattern_name = ""
        best_ted_pattern_expr = ""

        best_hun_dist = 999
        best_hun_pattern_name = ""

        if student_ast is not None:
            # 各パターンと総当たりで比較
            for t_name, t_expr in templates.items():
                # TED計算
                ted = calculate_ted(student_ast, t_expr)
                if 0 <= ted < best_ted_dist: 
                    best_ted_dist = ted
                    best_ted_pattern_name = t_name
                    best_ted_pattern_expr = str(t_expr)
                
                # ハンガリアン計算
                hun = calculate_hungarian_ted(student_ast, t_expr)
                if 0 <= hun < best_hun_dist: 
                    best_hun_dist = hun
                    best_hun_pattern_name = t_name

        else:
            best_ted_dist = -1
            best_hun_dist = -1

        # レーベンシュタイン距離
        # 比較対象の文字列として、最終展開形に近いものを使用
        best_lev_dist = calculate_levenshtein(target_expr, "e**x*log(x) + e**x/x")

        # 結果を格納
        result_row["パース成功"] = "OK" if student_ast else "NG"
        result_row["TED最小距離"] = best_ted_dist
        result_row["TEDマッチ先パターン"] = best_ted_pattern_name
        result_row["TEDマッチ先_数式"] = best_ted_pattern_expr
        result_row["ハンガリアン最小距離"] = best_hun_dist
        result_row["ハンガリアンマッチ先パターン"] = best_hun_pattern_name
        result_row["レーベンシュタイン距離"] = best_lev_dist

        results.append(result_row)

    report_df = pd.DataFrame(results)
    report_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\n--- 処理完了！ 超・高解像度レポート(v8_experimental)を作成しました ---")
    print(f"Path: {OUTPUT_CSV}")

if __name__ == "__main__":
    run_evaluation_pipeline()