# pythonコード
# 指定ディレクトリのすべてのCSVファイルを処理するコード

import pandas as pd
import re
import numpy as np
import os
import glob # globモジュールをインポート

# --- 設定部分 ---
# 処理したいCSVファイルが格納されているディレクトリのパス
# 例: スクリプトと同じディレクトリにある '微分積分学データ' フォルダ
input_data_dir = './微分積分学データ/'

# 入力CSVファイルのエンコーディング
# もしファイルによってエンコーディングが異なる可能姓がある場合は、
# 個別に指定するか、推測するロジックが必要です。ここでは一律に指定します。
encoding_type = 'utf_8_sig' # または 'cp932', 'shift_jis' など、前回成功したエンコーディング

# 出力ディレクトリ名
output_dir = 'output_results' # スクリプト実行場所からの相対パス

# ans1抽出元の列名
target_column_for_ans = '解答 1'

# 評点などの数値評価が格納されている列の名前
target_column_for_score = '評点/10.00'

# 不正解と判断する評点のしきい値（この値以下が不正解）
incorrect_score_threshold = 0

# 出力したい列のリスト
# すべてのCSVファイルにこれらの列が存在することを確認してください
output_columns_to_save = ['姓', '開始日時', '受験完了', '継続時間', 'extracted_ans1']

# --- メイン処理 ---
# 出力ディレクトリが存在しない場合は作成
os.makedirs(output_dir, exist_ok=True)

# -------------------------------------------------------------
# 指定ディレクトリ内のすべてのCSVファイルのパスを取得
# -------------------------------------------------------------
# os.path.join() でディレクトリとワイルドカードを結合し、glob.glob() で検索
# これにより、full_input_file_paths にすべてのCSVファイルのフルパスがリストとして格納されます。
full_input_file_paths = glob.glob(os.path.join(input_data_dir, '*.csv'))

# 処理するファイルが見つからなかった場合のメッセージ
if not full_input_file_paths:
    print(f"エラー: '{input_data_dir}' ディレクトリ内にCSVファイルが見つかりませんでした。パスを確認してください。")
    exit() # 処理を終了

# -------------------------------------------------------------
# 取得したCSVファイルごとにループを回す
# -------------------------------------------------------------
for current_input_file_path in full_input_file_paths:
    # 各ファイルの処理開始メッセージ
    print(f"\n======== {os.path.basename(current_input_file_path)} の処理を開始します ========")

    try:
        # CSVファイルの読み込み
        df = pd.read_csv(current_input_file_path, encoding=encoding_type)

        # 必須列の確認
        # output_columns_to_save の列も存在するかここで確認すると良い
        all_required_cols_for_processing = ['姓', target_column_for_ans, target_column_for_score] + [col for col in output_columns_to_save if col not in ['姓', 'extracted_ans1']]
        for col in all_required_cols_for_processing:
            if col not in df.columns:
                raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に必須の列 '{col}' が見つかりません。")

        # 'ans1'形式の文字列を抽出する正規表現
        pattern = r'ans1:\s*=?\s*(.*?)\s*\[score\]'
        df['extracted_ans1'] = df[target_column_for_ans].str.extract(pattern)

        # NaN（抽出できなかった行）を削除
        df_cleaned = df.dropna(subset=['extracted_ans1'])

        # extracted_ans1でソート
        sorted_df_cleaned = df_cleaned.sort_values(by='extracted_ans1', ascending=True)

        # '評点/10.00' の数値変換の試行
        if target_column_for_score in sorted_df_cleaned.columns and pd.api.types.is_object_dtype(sorted_df_cleaned[target_column_for_score]):
            print(f"警告: '{os.path.basename(current_input_file_path)}': '{target_column_for_score}' 列が文字列型です。数値に変換を試みます。")
            sorted_df_cleaned[target_column_for_score] = pd.to_numeric(
                sorted_df_cleaned[target_column_for_score], errors='coerce'
            )
            sorted_df_cleaned = sorted_df_cleaned.dropna(subset=[target_column_for_score])

        # 不正解の条件でフィルタリング
        incorrect_answers_df = sorted_df_cleaned[sorted_df_cleaned[target_column_for_score] == incorrect_score_threshold]

        # 出力する列を選択
        # output_columns_to_save の全ての列がincorrect_answers_dfに存在するかチェック
        final_output_cols = [col for col in output_columns_to_save if col in incorrect_answers_df.columns]
        if 'extracted_ans1' not in final_output_cols: # extracted_ans1は必ず含める
            final_output_cols.append('extracted_ans1')
        if '姓' not in final_output_cols: # 姓も必ず含める
            final_output_cols.insert(0, '姓') # 先頭に追加

        output_df = incorrect_answers_df[final_output_cols]


        print(f"\n--- {os.path.basename(current_input_file_path)} の不正解解答一覧（表示）：---")
        if output_df.empty:
            print("不正解の解答は見つかりませんでした。")
        else:
            print(output_df)
        print("---")

        # 結果をCSVファイルとして保存
        if not output_df.empty:
            base_filename = os.path.splitext(os.path.basename(current_input_file_path))[0]
            output_csv_filename_for_this_file = f"{base_filename}_不正解者リスト.csv" # 各ファイル用に出力ファイル名を生成
            full_output_path = os.path.join(output_dir, output_csv_filename_for_this_file)

            output_df.to_csv(full_output_path, index=False, encoding='utf_8_sig')
            print(f"\n結果を '{full_output_path}' に保存しました。")
        else:
            print(f"\n'{os.path.basename(current_input_file_path)}' に保存するデータがないため、ファイルは作成されませんでした。")

    except FileNotFoundError:
        print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}' が見つかりませんでした。パスを確認してください。")
    except UnicodeDecodeError:
        print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}': エンコーディング '{encoding_type}' でのデコードに失敗しました。別のエンコーディングを試してください。")
    except KeyError as e:
        print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}': 列 '{e}' がデータフレームに見つかりませんでした。CSVファイルの列名を確認してください。")
        if 'df' in locals():
            print("読み込んだデータフレームの列名:", df.columns.tolist())
        else:
            print("データフレームの読み込みに失敗したため、列名を表示できません。")
    except Exception as e:
        import traceback
        print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}' の処理中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()

    print(f"======== {os.path.basename(current_input_file_path)} の処理が完了しました ========\n")

print("\n--- 全てのCSVファイルの処理が完了しました ---")