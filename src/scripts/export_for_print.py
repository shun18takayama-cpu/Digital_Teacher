import pandas as pd
import os

# ==========================================
# 設定
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# さっき作った最終結果ファイルを読み込む
INPUT_FILE = os.path.join(BASE_DIR, "results", "JSISE", "JSISE_final_analysis.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "results", "JSISE", "For_Print_Checklist.csv")

def create_print_sheet():
    print("--- 印刷用チェックシートを作成します ---")
    
    if not os.path.exists(INPUT_FILE):
        print("エラー: 分析結果ファイルがありません。analyze.pyを実行してください。")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # 印刷に必要な列だけ選ぶ
    # HW_ID: 問題番号
    # student_expr: 学生の式
    # Error_Category: AIの判定
    target_cols = ['HW_ID', 'student_expr', 'Error_Category']
    
    # 存在確認
    cols = [c for c in target_cols if c in df.columns]
    print_df = df[cols].copy()
    
    # 手書き用の空欄列を作る
    print_df['判定 (〇/×)'] = ''  # ここにマルバツを書く
    print_df['正解ラベル (訂正用)'] = '' # ここに正しい答えを書く
    print_df['メモ'] = '' # 気づきを書く
    
    # 見やすいように少し並び替え（カテゴリごとにしておくとチェックが楽かも？お好みで）
    # print_df = print_df.sort_values(['HW_ID', 'Error_Category'])
    
    # Excelで開いたときに文字化けしないおまじない (cp932 = Shift-JIS)
    try:
        print_df.to_csv(OUTPUT_FILE, index=False, encoding='cp932')
    except:
        # 記号などでShift-JIS変換できない場合はutf-8-sigで
        print_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
    print(f"作成完了: {OUTPUT_FILE}")
    print("-> Excelで開き、「列の幅」を広げて、「罫線」をつけて印刷してください！")

if __name__ == "__main__":
    create_print_sheet()
    