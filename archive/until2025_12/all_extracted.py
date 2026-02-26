# pythonコード
# 解答1のみを正規表現で抽出し、新しいCSVファイルとして保存するコード (複数の不正解しきい値対応版)

import pandas as pd
import re
import numpy as np
import os
import glob

# --- 設定部分 ---
input_data_dir = './微分積分学データ/'
encoding_type = 'utf_8_sig'

output_dir = 'extracted_ans1_results'

pattern_to_extract = r'.*' # 全ての文字にマッチ (純粋な解答でも抽出できる)
target_column_to_extract = '解答 1'

# 評点などの数値評価が格納されている列の名前
target_column_for_score = '評点/10.00'

# -------------------------------------------------------------
# 修正: 不正解と判断する評点のしきい値（リストとして定義）
# このリストに含まれる値のいずれかに一致する場合を不正解とします。
# -------------------------------------------------------------
incorrect_score_thresholds = [0, 10] # 0 または 10 が不正解の場合


# --- メイン処理 ---
os.makedirs(output_dir, exist_ok=True)

full_input_file_paths = glob.glob(os.path.join(input_data_dir, '*.csv'))

if not full_input_file_paths:
    print(f"エラー: '{input_data_dir}' ディレクトリ内にCSVファイルが見つかりませんでした。パスを確認してください。")
    exit()

for current_input_file_path in full_input_file_paths:
    print(f"\n======== {os.path.basename(current_input_file_path)} の処理を開始します ========")

    try:
        df = pd.read_csv(current_input_file_path, encoding=encoding_type)

        if target_column_to_extract not in df.columns:
            raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に列 '{target_column_to_extract}' が見つかりません。")

        extracted_data_series = df[target_column_to_extract].astype(str).str.extract(pattern_to_extract, expand=False)
        output_df_single_column = pd.DataFrame({'extracted_ans1': extracted_data_series})


        print(f"\n--- {os.path.basename(current_input_file_path)} の抽出結果（表示）：---")
        if output_df_single_column.empty:
            print("抽出されたデータが見つかりませんでした。")
        else:
            print(output_df_single_column.head())
            print(f"合計 {len(output_df_single_column)} 行のデータが抽出されました。")
        print("---")

        if not output_df_single_column.empty:
            base_filename = os.path.splitext(os.path.basename(current_input_file_path))[0]
            output_csv_filename_for_this_file = f"{base_filename}_extracted_ans1.csv"
            full_output_path = os.path.join(output_dir, output_csv_filename_for_this_file)

            output_df_single_column.to_csv(full_output_path, index=False, encoding='utf_8_sig')
            print(f"\n抽出結果を '{full_output_path}' に保存しました。")
        else:
            print(f"\n'{os.path.basename(current_input_file_path)}' に保存するデータがないため、ファイルは作成されませんでした。")

    # -------------------------------------------------------------
    # ここからが前回のコードとは異なる「全解答リスト」作成部分です。
    # 抽出結果のみのCSV保存と、全解答リストのCSV保存を同時に行いたい場合、
    # この部分をループ内に別途記述する必要があります。
    # 現在のコードは「解答1をすべて正規表現したcsvファイルを作成して」という要件に特化しています。
    #
    # もし「全解答リスト」の機能も維持したい場合は、そのコードブロックをここに再挿入してください。
    # ただし、その場合はdf, sorted_df_final, incorrect_answers_df, correct_answers_df などの
    # データフレームが適切に定義されている必要があります。
    # -------------------------------------------------------------

    print(f"======== {os.path.basename(current_input_file_path)} の処理が完了しました ========\n")

print("\n--- 全てのCSVファイルの処理が完了しました ---")
