import pandas as pd
import os

# ==========================================
# 設定
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 分析済みの最終ファイルを読み込む
INPUT_FILE = os.path.join(BASE_DIR, "results", "JSISE", "JSISE_final_analysis.csv")
# 出力先
OUTPUT_FILE = os.path.join(BASE_DIR, "results", "JSISE", "Detailed_Judgment_Ledger.csv")

# ==========================================
# 参照用データ (ここが情報の肝です)
# ==========================================
# 各問題の「正解プロセス」と「誤答モデルの形」を定義
REFERENCE_INFO = {
    'HW01-05': {
        '問題式': 'y = x * log(x)',
        '正解プロセス': "(x)'log(x) + x(log(x))' \n= 1*log(x) + x*(1/x) \n= log(x) + 1",
        '誤答モデル(線形化)': "u'v' = 1/x",
        '誤答モデル(商混同)': "u'v - uv' = log(x) - 1"
    },
    'HW03-01': {
        '問題式': 'y = e^x * log(x)',
        '正解プロセス': "(e^x)'log(x) + e^x(log(x))' \n= e^x*log(x) + e^x*(1/x)",
        '誤答モデル(線形化)': "u'v' = e^x * (1/x)",
        '誤答モデル(商混同)': "u'v - uv' = e^x*log(x) - e^x*(1/x)"
    },
    'HW03-05': {
        '問題式': 'y = x * log(x) * sin(x)',
        '正解プロセス': "3項の積の法則:\n (x)'log(x)sin(x) + x(log(x))'sin(x) + xlog(x)(sin(x))'\n= log(x)sin(x) + sin(x) + xlog(x)cos(x)",
        '誤答モデル(線形化)': "u'v'w' = 1 * (1/x) * cos(x) \n= cos(x)/x",
        '誤答モデル(商混同)': "※パターン多岐 (符号ミス等)"
    }
}

def create_detailed_sheet():
    print("--- 詳細判断台帳を作成します ---")
    
    if not os.path.exists(INPUT_FILE):
        print("エラー: JSISE_final_analysis.csv がありません。analyze.pyを実行してください。")
        return

    df = pd.read_csv(INPUT_FILE)
    
    # 参照情報をデータフレームにマージするための準備
    # HW_IDをキーにして、REFERENCE_INFOの内容を各行に追加する
    
    # 追加する列のリスト
    ref_cols = ['問題式', '正解プロセス', '誤答モデル(線形化)', '誤答モデル(商混同)']
    
    # 辞書からデータを引いてくる関数
    def get_ref_data(hw_id, key):
        if hw_id in REFERENCE_INFO:
            return REFERENCE_INFO[hw_id].get(key, "")
        return ""

    # 列を追加
    for col in ref_cols:
        df[col] = df['HW_ID'].apply(lambda x: get_ref_data(x, col))

    # --- 出力する列の選定と並び替え ---
    # 判定に必要な情報を左側に集める
    output_cols = [
        'HW_ID',
        '問題式',               # 何を解いているか
        'student_expr',        # 学生の答え
        'Error_Category',      # AIの判定
        '正解プロセス',         # どう計算すべきだったか
        '誤答モデル(線形化)',    # 線形化誤認だとどうなるか
        '誤答モデル(商混同)',    # 商混同だとどうなるか
        'Human_Label',         # 【記入欄】あなたの判定
        'メモ'                  # 【記入欄】気づき
    ]
    
    # 存在しない列（Human_Labelなど）は空文字で埋める
    for c in output_cols:
        if c not in df.columns:
            df[c] = ''
            
    # 指定順序で抽出
    export_df = df[output_cols].copy()
    
    # Excelで見やすいようにShift-JISで出力
    try:
        export_df.to_csv(OUTPUT_FILE, index=False, encoding='cp932')
    except:
        export_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
    print(f"作成完了: {OUTPUT_FILE}")
    print("\n【Excelでの作業アドバイス】")
    print("1. 全体を選択して「折り返して全体を表示」をONにすると、計算過程の改行が見やすくなります。")
    print("2. 列幅を調整して印刷、またはPC上で入力してください。")

if __name__ == "__main__":
    create_detailed_sheet()