# pythonコード
# 誤答者の全解答を抽出し、CSVファイルとして保存するコード (アウトプットディレクトリ変更版)

import pandas as pd
import re
import numpy as np
import os
import glob
import csv

# -------------------------------------------------------------
# 継続時間を日本語表記から秒数に変換する関数
# 「X分Y秒」形式に対応
# -------------------------------------------------------------
def convert_japanese_duration_to_seconds(duration_str):
    """
    'X分Y秒' 形式（例: '3分6秒', '10分0秒', '0分15秒'）の継続時間文字列を秒数に変換します。
    「X分」または「Y秒」のどちらか片方のみの表記にも対応します。
    無効な形式やNaNの場合は np.nan を返します。
    """
    if pd.isna(duration_str): # NaNの場合
        return np.nan
    
    s = str(duration_str).strip() # 前後の空白を除去

    minutes = 0
    seconds = 0

    # 「X分Y秒」または「Y秒」のみ
    match_sec = re.search(r'(\d+)秒', s)
    if match_sec:
        seconds = int(match_sec.group(1))

    # 「X分」または「X分Y秒」
    match_min = re.search(r'(\d+)分', s)
    if match_min:
        minutes = int(match_min.group(1))
    
    # どちらにもマッチしない、または数字以外の文字が多いなど、無効な形式の場合
    if not match_min and not match_sec:
        return np.nan

    try:
        total_seconds = minutes * 60 + seconds
        return total_seconds
    except ValueError:
        return np.nan


# --- 設定部分 ---
# 処理したいCSVファイルが格納されているディレクトリのパス (変更なし)
input_data_dir = './微分積分学データ/'

# 入力CSVファイルのエンコーディング
encoding_type = 'utf_8_sig'

# ★変更: 出力ディレクトリ名
output_dir = 'processed_analysis_results' # 例: 新しいアウトプットディレクトリ名

# '解答 1'列から抽出するための正規表現パターン
pattern_for_ans_cor_extraction = r'ans1:\s*=?\s*(.*?)\s*\[score\]'

target_column_for_ans = '解答 1'
target_column_for_cor = '正解 1'

target_column_for_score = '評点/10.00'
incorrect_score_thresholds = [0]

output_columns_to_save = [
    '姓', '開始日時', '受験完了', '継続時間_秒',
    '評点/10.00',
    'extracted_ans1',
    'extracted_cor1',
   


# --- メイン処理 ---
os.makedirs(output_dir, exist_ok=True)

full_input_file_paths = glob.glob(os.path.join(input_data_dir, '*.csv'))

if not full_input_file_paths:
    print(f"エラー: '{input_data_dir}' ディレクトリ内にCSVファイルが見つかりませんでした。パスを確認してください。")
    exit()

for current_input_file_path in full_input_file_paths:
    print(f"\n======== {os.path.basename(current_input_file_path)} の処理を開始します ========")

    try:
        final_output_cols_ordered = []

        df = pd.read_csv(current_input_file_path, encoding=encoding_type)
        df.columns = df.columns.str.strip()

        initial_required_cols = ['姓','開始日時', '評点/10.00', target_column_for_ans, target_column_for_cor, '継続時間']
        for col in initial_required_cols:
            if col not in df.columns:
                raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に必須の列 '{col}' が見つかりません。読み込んだ列名: {df.columns.tolist()}")

        df['継続時間_秒'] = df['継続時間'].apply(convert_japanese_duration_to_seconds)
        print(f"情報: '{os.path.basename(current_input_file_path)}': '継続時間' (日本語表記) を秒数に変換し、'継続時間_秒' 列を作成しました。")


        df['extracted_ans1'] = df[target_column_for_ans].astype(str).str.extract(pattern_for_ans_cor_extraction, expand=False)
        df['extracted_cor1'] = df[target_column_for_cor].astype(str).str.extract(pattern_for_ans_cor_extraction, expand=False)

        df_processed = df.copy()

        if target_column_for_score in df_processed.columns and pd.api.types.is_object_dtype(df_processed[target_column_for_score]):
            print(f"警告: '{os.path.basename(current_input_file_path)}': '{target_column_for_score}' 列が文字列型です。数値に変換を試みます。")
            df_processed[target_column_for_score] = pd.to_numeric(
                df_processed[target_column_for_score], errors='coerce'
            )

        incorrect_condition_on_score = df_processed[target_column_for_score].isin(incorrect_score_thresholds) & df_processed[target_column_for_score].notna()
        df_processed['_is_incorrect_flag'] = incorrect_condition_on_score

        df_processed['temp_student_id'] = df_processed['姓'].astype(str) + '_' + \
                                          df_processed['名'].astype(str) + '_' + \
                                          df_processed['メールアドレス'].astype(str)

        incorrect_student_identifiers = df_processed[df_processed['_is_incorrect_flag'] == True]['temp_student_id'].unique()

        incorrect_performers_all_answers_df = df_processed[df_processed['temp_student_id'].isin(incorrect_student_identifiers)].copy()
        
        incorrect_performers_all_answers_df = incorrect_performers_all_answers_df.drop(columns=['_is_incorrect_flag', 'temp_student_id'])

        sort_by_cols = []
        if '姓' in incorrect_performers_all_answers_df.columns:
            sort_by_cols.append('姓')
        if '開始日時' in incorrect_performers_all_answers_df.columns:
            sort_by_cols.append('開始日時')

        if sort_by_cols:
            final_output_df = incorrect_performers_all_answers_df.sort_values(by=sort_by_cols, ascending=[True] * len(sort_by_cols))
            print(f"情報: '{os.path.basename(current_input_file_path)}': 出力データを '{', '.join(sort_by_cols)}' でソートしました。")
        else:
            final_output_df = incorrect_performers_all_answers_df
            print(f"警告: '{os.path.basename(current_input_file_path)}': ソート基準列が見つからないためソートされません。")


        columns_to_check_for_excel = ['extracted_ans1', 'extracted_cor1']
        for col_name in columns_to_check_for_excel:
            if col_name in final_output_df.columns:
                is_string_col = pd.api.types.is_string_dtype(final_output_df[col_name])
                if is_string_col:
                    final_output_df[col_name] = final_output_df[col_name].astype(str).apply(
                        lambda x: "'" + x if pd.notna(x) and x.strip().startswith('=') else x
                    )
                    final_output_df[col_name] = final_output_df[col_name].replace("'nan", np.nan)
                else:
                    print(f"情報: 列 '{col_name}' は文字列型ではないため、#NAME?対策は適用されません。")


        output_cols_base_current = df.columns.tolist() 
        for col in output_columns_to_save:
            if col in final_output_df.columns:
                final_output_cols_ordered.append(col)
        
        if not final_output_cols_ordered:
            raise ValueError(f"CSVファイル '{os.path.basename(current_input_file_path)}': 出力対象となる列が一つもありません。output_columns_to_saveを確認してください。")

        final_output_df = final_output_df[final_output_cols_ordered]


        print(f"\n--- {os.path.basename(current_input_file_path)} の誤答者の全解答一覧（表示）：---")
        if final_output_df.empty:
            print("誤答を行った回答者が見つかりませんでした。")
        else:
            print(final_output_df.head())
            print(f"合計 {len(final_output_df)} 行のデータが抽出されました。")
        print("---")

        if not final_output_df.empty:
            base_filename = os.path.splitext(os.path.basename(current_input_file_path))[0]
            output_csv_filename_for_this_file = f"{base_filename}_誤答者全解答.csv"
            full_output_path = os.path.join(output_dir, output_csv_filename_for_this_file)

            final_output_df.to_csv(full_output_path, index=False, encoding='utf_8_sig', quoting=csv.QUOTE_MINIMAL)
            print(f"\n誤答者の全解答リストを '{full_output_path}' に保存しました。")
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