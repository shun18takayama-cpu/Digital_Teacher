# 🐍 src/scripts/summarize_rule_metrics.py
# (これは新しく作成するファイルです)

import pandas as pd
import sys
import os

# -----------------------------------------------------------------------------
# 1. モジュールのインポート設定
# -----------------------------------------------------------------------------
# (config.py を読み込むために、プロジェクトのルートをパスに追加)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # src/config.py から「すべてのルール名リスト」をインポート
    from src import config
except ImportError as e:
    print(f"!!! エラー: 'src/config.py' が見つかりません。: {e}")
    sys.exit()

# (import文などは、この関数の上にある想定です)

# -----------------------------------------------------------------------------
# 2. 公式ごとの集計
# -----------------------------------------------------------------------------
def main():
    print("--- 公式ごとの精度 集計スクリプト ---")
    
    # 1. 読み込む「精度レポート」の場所を定義
    # (run_accuracy_test.py が出力したファイル)
    # ★ 注意: 'v2.csv' か 'v5.csv' か、正しいファイル名を指定してください
    report_path = os.path.join(project_root, "results", "accuracy", "accuracy_report_v8.csv")
    
    # 2. 精度レポートを読み込む
    try:
        df_report = pd.read_csv(report_path, encoding='utf-8-sig') 
    except FileNotFoundError:
        print(f"!!! エラー: レポートファイル '{report_path}' が見つかりません。")
        print("先に 'src/scripts/run_accuracy_test.py' を実行してください。")
        return
    except Exception as e:
        print(f"!!! エラー: レポートファイルの読み込みに失敗しました。: {e}")
        return
    
    print(f"'{report_path}' を読み込みました。")
    
    # 3. 公式ごとに TP, FP, FN を集計
    metrics_data = [] # 公式ごとの集計結果を格納するリスト
    
    # config.py から「すべてのルール名」リストを取得
    all_rules = config.ALL_RULE_NAMES 
    
    for rule in all_rules:
        # (文字列が空 'nan' でないことを確認)
        df_report = df_report.fillna('') 
        
        # ------------------------------------------------------------
        # ★★★ ここが修正点です ★★★
        # regex=False を追加し、"(x^n)" の括弧() を
        # 特殊文字ではなく、ただの文字列として検索するようにします。
        # ------------------------------------------------------------
        
        # True Positives (TP): 「TP_Rules」列にこのルール名が含まれる行の総数
        tp_count = df_report[df_report['TP_Rules (正しく検出)'].str.contains(rule, na=False, regex=False)].shape[0]
        
        # False Positives (FP): 「FP_Rules」列にこのルール名が含まれる行の総数
        fp_count = df_report[df_report['FP_Rules (検出過多)'].str.contains(rule, na=False, regex=False)].shape[0]
        
        # False Negatives (FN): 「FN_Rules」列にこのルール名が含まれる行の総数
        fn_count = df_report[df_report['FN_Rules (検出漏れ)'].str.contains(rule, na=False, regex=False)].shape[0]
        
        # ------------------------------------------------------------
        # ★★★ 修正点ここまで ★★★
        # ------------------------------------------------------------

        # 4. Precision, Recall, F1スコアを計算
        
        # Precision = TP / (TP + FP)
        if (tp_count + fp_count) == 0:
            precision = 1.0 if (tp_count + fn_count) == 0 else 0.0 # ゼロ除算防止
        else:
            precision = tp_count / (tp_count + fp_count)
            
        # Recall = TP / (TP + FN)
        if (tp_count + fn_count) == 0:
            recall = 1.0 if (tp_count + fp_count) == 0 else 0.0 # ゼロ除算防止
        else:
            recall = tp_count / (tp_count + fn_count)
            
        # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
        if (precision + recall) == 0:
            f1_score = 0.0 # ゼロ除算防止
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
            
        # 5. 結果をリストに追加
        metrics_data.append({
            "公式ルール名": rule,
            "Precision": precision,
            "Recall": recall,
            "F1_Score": f1_score,
            "TP (正しく検出)": tp_count,
            "FP (検出過多)": fp_count,
            "FN (検出漏れ)": fn_count
        })

    # 6. 最終的な集計結果をデータフレームに変換
    df_rule_metrics = pd.DataFrame(metrics_data)
    
    # 7. 集計レポートをCSVとして出力
    output_dir = os.path.join(project_root, "results", "accuracy")
    os.makedirs(output_dir, exist_ok=True) 
    output_path = os.path.join(output_dir, "rule_based_metrics_v8.csv") # v2 に更新
    
    df_rule_metrics.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n--- 処理完了 ---")
    print("【公式ごとの精度レポート (v2)】")
    # Precision, Recall, F1 を小数点以下3桁で表示
    print(df_rule_metrics.to_string(float_format="%.3f"))
    print(f"\n📋 集計レポートを '{output_path}' に保存しました。")


if __name__ == "__main__":
    main()
#
# (↑この2行は、summarize_rule_metrics.py の一番最後に
#  既に書かれているはずなので、main関数だけを置き換えてください)
# ---