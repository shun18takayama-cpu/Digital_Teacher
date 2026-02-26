# pythonコード
# 誤答者の全解答を抽出し、CSVファイルとして保存するコード (最終版 - 姓のみで識別)

import pandas as pd
import re
import numpy as np
import os
import glob
import csv

# --- 設定部分 ---
input_data_dir = './微分積分学データ/'
encoding_type = 'utf_8_sig'

output_dir = 'all_answer_analysis0'

# ★重要: この正規表現は 'ans1: (-x-1)/(x-1)^3 [score]' のような形式用です。
# ★もしCSVの「解答 1」や「正解 1」列が '(-x-1)/(x-1)^3' のように純粋な解答形式なら、
#   ここを pattern_for_ans_cor_extraction = r'.*' に変更することを推奨します。
#   その場合、下の抽出部分で astype(str).str.extract(pattern, expand=False) はそのまま使用できます。
pattern_for_ans_cor_extraction = r'ans1:\s*=?\s*(.*?)\s*\[score\]'

target_column_for_ans = '解答 1'
target_column_for_cor = '正解 1'

target_column_for_score = '評点/10.00'
incorrect_score_thresholds = [0,10] # 不正解者リストの作成

# 出力したい列のリスト
output_columns_to_save = [
    '姓', '開始日時', '受験完了', '継続時間',
    '評点/10.00', 
    'extracted_ans1',
    'extracted_cor1',
    
]


# --- メイン処理 ---
os.makedirs(output_dir, exist_ok=True)

full_input_file_paths = glob.glob(os.path.join(input_data_dir, '*.csv'))

if not full_input_file_paths:
    print(f"エラー: '{input_data_dir}' ディレクトリ内にCSVファイルが見つかりませんでした。パスを確認してください。")
    exit()

for current_input_file_path in full_input_file_paths:
    print(f"\n======== {os.path.basename(current_input_file_path)} の処理を開始します ========")

    try:
        final_output_cols_ordered = [] # <-- ここで初期化されます

        df = pd.read_csv(current_input_file_path, encoding=encoding_type)
        df.columns = df.columns.str.strip()

        # -------------------------------------------------------------
        # 必須列の確認 ('名', 'メールアドレス'は必須ではなくなる)
        # -------------------------------------------------------------
        initial_required_cols = ['姓', '開始日時', '評点/10.00', target_column_for_ans, target_column_for_cor]
        for col in initial_required_cols:
            if col not in df.columns:
                raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に必須の列 '{col}' が見つかりません。読み込んだ列名: {df.columns.tolist()}")

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

        # -------------------------------------------------------------
        # 修正: 誤答を行った回答者の「一意な識別子」を「姓」のみにする
        # -------------------------------------------------------------
        # 姓を一時的な識別子として使用
        df_processed['temp_student_id'] = df_processed['姓'].astype(str)

        incorrect_student_identifiers = df_processed[df_processed['_is_incorrect_flag'] == True]['temp_student_id'].unique()

        incorrect_performers_all_answers_df = df_processed[df_processed['temp_student_id'].isin(incorrect_student_identifiers)].copy()
        
        incorrect_performers_all_answers_df = incorrect_performers_all_answers_df.drop(columns=['_is_incorrect_flag', 'temp_student_id'])


        # -------------------------------------------------------------
        # 出力データを「姓」と「開始日時」の順に並べ替え
        # -------------------------------------------------------------
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


        # -------------------------------------------------------------
        # Excelの #NAME? エラー対策: '=' で始まる文字列にアポストロフィを付加
        # -------------------------------------------------------------
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


        # -------------------------------------------------------------
        # 出力する列の最終選択
        # -------------------------------------------------------------
        output_cols_base_current = df.columns.tolist() 
        # final_output_cols_ordered はtryブロックの最初に初期化済み

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