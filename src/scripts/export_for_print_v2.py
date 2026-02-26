import pandas as pd
import os

# ==========================================
# 設定
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 最新の分析結果を読み込む
INPUT_FILE = os.path.join(BASE_DIR, "results", "JSISE", "JSISE_final_analysis.csv")
# 出力ファイル名（v2に変更してロック回避）
OUTPUT_FILE = os.path.join(BASE_DIR, "results", "JSISE", "For_Print_Checklist_v2.csv")

def create_print_sheet_v2():
    print("--- 印刷用チェックシート(v2)を作成します ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。analyze.pyを実行してください。")
        return

    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        print(f"エラー: ファイル読み込み失敗。Excelで開いていませんか？ ({e})")
        return
    
    # チェックに必要な列のみ抽出
    # HW_ID: 問題ID
    # student_expr: 学生の数式
    # Error_Category: AIの判定
    target_cols = ['HW_ID', 'student_expr', 'Error_Category']
    
    cols = [c for c in target_cols if c in df.columns]
    print_df = df[cols].copy()
    
    # 手書き記入用の空列を追加
    print_df['判定 (〇/×)'] = ''
    print_df['正解ラベル (訂正用)'] = ''
    print_df['メモ'] = ''
    
    # 問題IDとカテゴリでソートして、見やすくする
    if 'HW_ID' in print_df.columns and 'Error_Category' in print_df.columns:
        print_df = print_df.sort_values(['HW_ID', 'Error_Category'])
    
    # 保存 (Shift-JIS優先)
    try:
        print_df.to_csv(OUTPUT_FILE, index=False, encoding='cp932')
        print(f"作成完了(Shift-JIS): {OUTPUT_FILE}")
    except:
        print_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"作成完了(UTF-8): {OUTPUT_FILE}")
        
    print("-> Excelで開き、印刷してチェックを行ってください。")

if __name__ == "__main__":
    create_print_sheet_v2()