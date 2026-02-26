# 🐍 src/scripts/run_accuracy_test.py (v2.0 - 評価指標 導入版)

import pandas as pd
import sys
import os

# -----------------------------------------------------------------------------
# 1. モジュールのインポート設定 (変更なし)
# -----------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.modules.problem_analyzer import analyze_expression_rules
except ImportError as e:
    print(f"!!! エラー: モジュールのインポートに失敗しました: {e}")
    sys.exit()
except Exception as e:
    print(f"!!! 予期せぬエラー: {e}")
    sys.exit()

# -----------------------------------------------------------------------------
# 2. ★★★ 新規追加 ★★★
# Precision, Recall を計算するためのヘルパー関数
# -----------------------------------------------------------------------------
def calculate_metrics(expected_set, detected_set):
    """
    2つのセット(set)を受け取り、TP, FP, FN, Precision, Recall を計算する関数
    """
    
    # 2-1. TP, FP, FN を計算
    # True Positives (両方に含まれる)
    tp_set = expected_set.intersection(detected_set)
    # False Positives (検出されたが、正解ではない = 検出過多)
    fp_set = detected_set.difference(expected_set)
    # False Negatives (正解だが、検出されなかった = 検出漏れ)
    fn_set = expected_set.difference(detected_set)
    
    # 2-2. それぞれの数をカウント
    tp_count = len(tp_set)
    fp_count = len(fp_set)
    fn_count = len(fn_set)
    
    # 2-3. Precision と Recall を計算
    # (ゼロ除算エラーを防ぐための処理を含む)
    
    # Precision = TP / (TP + FP)
    if (tp_count + fp_count) == 0:
        # プログラムが何も検出しなかった(TP=0, FP=0)場合。
        # 正解もなかった(FN=0)なら 1.0 (完璧)、正解があった(FN>0)なら 0.0 (不正解)。
        precision = 1.0 if (tp_count + fn_count) == 0 else 0.0 
    else:
        precision = tp_count / (tp_count + fp_count)

    # Recall = TP / (TP + FN)
    if (tp_count + fn_count) == 0:
        # 本来見つけるべきルールがなかった(TP=0, FN=0)場合。
        # 何も検出しなければ 1.0 (完璧)、何か検出していたら(FP>0) 0.0 (不正解)。
        recall = 1.0 if (tp_count + fp_count) == 0 else 0.0
    else:
        recall = tp_count / (tp_count + fn_count)

    return {
        "precision": precision,
        "recall": recall,
        "tp_rules": ";".join(sorted(list(tp_set))), # 文字列に戻す
        "fp_rules": ";".join(sorted(list(fp_set))), # 文字列に戻す
        "fn_rules": ";".join(sorted(list(fn_set)))  # 文字列に戻す
    }

# -----------------------------------------------------------------------------
# 3. 精度測定のメイン処理 (ここを修正)
# -----------------------------------------------------------------------------
def main():
    print("--- タスク1: 分類器 精度測定スクリプト (v2.0) ---")

    test_data_path = os.path.join("data", "raw", "test_problems_generated_added.csv")

    try:
        df_test = pd.read_csv(test_data_path, encoding='utf-8-sig')
    except FileNotFoundError:
        print(f"!!! エラー: テストデータ '{test_data_path}' が見つかりません。")
        return
    except UnicodeDecodeError:
        print(f"!!! エラー: '{test_data_path}' の文字コードが Shift_JIS (cp932) ではないようです。")
        return
    except Exception as e:
        print(f"!!! エラー: テストデータの読み込みに失敗しました。: {e}")
        return
        
    print(f"テストデータ {len(df_test)} 件を読み込みました。")
    
    results = [] # 結果を格納するリスト
    
    for index, row in df_test.iterrows():
        problem_id = row['problem_id']
        problem_formula = row['problem_formula']
        
        if pd.isna(row['expected_rules']):
            print(f"警告: {problem_id} の expected_rules が空です。スキップします。")
            continue
            
        expected_rules_set = set(str(row['expected_rules']).split(';'))
        
        try:
            detected_rules_list, problem_ast_str = analyze_expression_rules(problem_formula)
            detected_rules_set = set(detected_rules_list)
            
            # ★★★ 修正箇所1 ★★★
            # 従来の「完全一致」判定
            if detected_rules_set == expected_rules_set:
                is_correct = "◎"
            else:
                is_correct = "×"
                
            # ★★★ 修正箇所2 ★★★
            # 新しい評価指標を計算
            metrics = calculate_metrics(expected_rules_set, detected_rules_set)

            # ★★★ 修正箇所3 ★★★
            # 結果辞書に新しい指標を追加
            results.append({
                "problem_id": problem_id,
                "problem_formula": problem_formula,
                "is_correct (完全一致)": is_correct, # 列名を変更
                "precision (適合率)": metrics["precision"], # ★ 追加
                "recall (再現率)": metrics["recall"],       # ★ 追加
                "expected_rules (あなたの正解)": row['expected_rules'], 
                "detected_rules (プログラムの判定)": ";".join(sorted(list(detected_rules_set))),
                "TP_Rules (正しく検出)": metrics["tp_rules"], # ★ 追加
                "FP_Rules (検出過多)": metrics["fp_rules"], # ★ 追加
                "FN_Rules (検出漏れ)": metrics["fn_rules"], # ★ 追加
                "problem_ast (問題文のAST)": problem_ast_str
            })
            
        except Exception as e:
            # エラー時も列を合わせる
            results.append({
                "problem_id": problem_id,
                "problem_formula": problem_formula,
                "is_correct (完全一致)": "エラー",
                "precision (適合率)": 0.0,
                "recall (再現率)": 0.0,
                "expected_rules (あなたの正解)": row['expected_rules'],
                "detected_rules (プログラムの判定)": f"分析エラー: {type(e).__name__}",
                "TP_Rules (正しく検出)": "",
                "FP_Rules (検出過多)": "",
                "FN_Rules (検出漏れ)": "",
                "problem_ast (問題文のAST)": f"エラーのためAST取得不可: {type(e).__name__}"
            })

    # 5. 結果をデータフレームに変換
    df_report = pd.DataFrame(results)
    
    # ★★★ 修正箇所4 ★★★
    # 出力する列を定義し、新しい指標を含める
    output_columns = [
        "problem_id",
        "problem_formula",
        "is_correct (完全一致)",
        "precision (適合率)",
        "recall (再現率)",
        "expected_rules (あなたの正解)",
        "detected_rules (プログラムの判定)",
        "TP_Rules (正しく検出)",
        "FP_Rules (検出過多)",
        "FN_Rules (検出漏れ)",
        "problem_ast (問題文のAST)"
    ]
    df_report = df_report[output_columns]
    
    # 6. 精度レポートをCSVとして出力
    output_dir = os.path.join("results", "accuracy")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "accuracy_report_v8.csv") # バージョンを都度変更
    
    df_report.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n--- 処理完了 ---")
    print("【精度レポート】")
    print(df_report)
    print(f"\n📋 精度レポートを '{output_path}' に保存しました。")

if __name__ == "__main__":
    main()