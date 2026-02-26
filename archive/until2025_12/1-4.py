# pythonコード
# 指定ディレクトリのすべてのCSVファイルを処理するコード (正解1抽出追加版)

import pandas as pd
import re
import numpy as np
import os
import glob

# --- 設定部分 ---
input_data_dir = './微分積分学データ/'
encoding_type = 'utf_8_sig'

output_dir_all = 'output_results'

target_column_for_ans = '解答 1'
target_column_for_cor = '正解 1' # 新しく追加された設定

target_column_for_score = '評点/10.00'
incorrect_score_threshold = 0 and 10

# 出力したい列のリスト
# すべてのCSVファイルにこれらの列が存在することを確認してください
output_columns_to_save = ['姓', '開始日時', '受験完了', '継続時間', 'extracted_ans1', 'extracted_cor1'] # extracted_cor1 を追加

# --- メイン処理 ---
os.makedirs(output_dir_all, exist_ok=True)

full_input_file_paths = glob.glob(os.path.join(input_data_dir, '*.csv'))

if not full_input_file_paths:
    print(f"エラー: '{input_data_dir}' ディレクトリ内にCSVファイルが見つかりませんでした。パスを確認してください。")
    exit()

for current_input_file_path in full_input_file_paths:
    print(f"\n======== {os.path.basename(current_input_file_path)} の処理を開始します ========")

    try:
        df = pd.read_csv(current_input_file_path, encoding=encoding_type)

        # 必須列の確認
        # target_column_for_cor も必須列として追加
        all_required_cols_for_processing = ['姓', target_column_for_ans, target_column_for_cor, target_column_for_score] + [col for col in output_columns_to_save if col not in ['姓', 'extracted_ans1', 'extracted_cor1']]
        for col in all_required_cols_for_processing:
            if col not in df.columns:
                raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に必須の列 '{col}' が見つかりません。")

        # -------------------------------------------------------------
        # 'ans1'形式の文字列を抽出する正規表現
        # 'ans1: ' の後に '=' があればそれを取り除き、その後の任意の文字 (非貪欲マッチ .*?) をキャプチャ
        # その後に ' [score]' が続くパターン
        # -------------------------------------------------------------
        pattern = r'ans1:\s*=?\s*(.*?)\s*\[score\]'

        # 新しい列 'extracted_ans1' を作成し、正規表現で値を抽出
        df['extracted_ans1'] = df[target_column_for_ans].str.extract(pattern)

        # -------------------------------------------------------------
        # '正解 1'列から 'extracted_cor1' を抽出する部分を追加
        # 同じパターンを使用すると仮定
        # -------------------------------------------------------------
        df['extracted_cor1'] = df[target_column_for_cor].str.extract(pattern)


        # extracted_ans1またはextracted_cor1のNaNを含む行を削除
        # どちらかが欠損していれば削除するか、extracted_ans1のみにするか？
        # ここではextracted_ans1のみを基準にNaNを削除します。
        # もしextracted_cor1も存在しない行を削除したい場合は、subsetに 'extracted_cor1' も追加してください。
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
        final_output_cols = [col for col in output_columns_to_save if col in incorrect_answers_df.columns]
        if 'extracted_ans1' not in final_output_cols:
            final_output_cols.append('extracted_ans1')
        if 'extracted_cor1' not in final_output_cols: # extracted_cor1 も必ず含める
            final_output_cols.append('extracted_cor1') # extracted_ans1の後に追加
        if '姓' not in final_output_cols:
            final_output_cols.insert(0, '姓')

        # 出力列の順序を調整 (必要であれば)
        # 例えば、['姓', 'extracted_ans1', 'extracted_cor1', '開始日時', ...] のようにしたい場合
        # desired_order = ['姓', 'extracted_ans1', 'extracted_cor1'] + [col for col in final_output_cols if col not in ['姓', 'extracted_ans1', 'extracted_cor1']]
        # output_df = incorrect_answers_df[desired_order]
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
            output_csv_filename_for_this_file = f"{base_filename}_解答リスト.csv"
            full_output_path = os.path.join(output_dir_all, output_csv_filename_for_this_file)

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
