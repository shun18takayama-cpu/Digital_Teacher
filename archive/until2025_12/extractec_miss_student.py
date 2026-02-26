# pythonコード
# 誤答者の全解答を抽出し、CSVファイルとして保存するコード (「姓」列クリーニング版)

import pandas as pd
import re
import numpy as np
import os
import glob

# --- 設定部分 ---
input_data_dir = './微分積分学データ/'
encoding_type = 'utf_8_sig'

output_dir = 'incorrect_answer_analysis'

pattern_for_ans_cor_extraction = r'ans1:\s*=?\s*(.*?)\s*\[score\]'

target_column_for_ans = '解答 1'
target_column_for_cor = '正解 1'

target_column_for_score = '評点/10.00'
incorrect_score_thresholds = ['0', '10']


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

        # -------------------------------------------------------------
        # 修正: 列名をクリーニング（前後の空白除去など）
        # -------------------------------------------------------------
        df.columns = df.columns.str.strip() # 前後の空白を除去
        # もし列名に途中に空白がある場合は、replaceで変換も検討
        # df.columns = df.columns.str.replace(' ', '_')


        # -------------------------------------------------------------
        # 必須列の確認
        # -------------------------------------------------------------
        # 実際の列名が ['姓', '名', ...] であることを確認したので、'姓' を必須として指定
        initial_required_cols = ['姓', '開始日時', '継続時間', '評点/10.00', target_column_for_ans, target_column_for_cor]
        for col in initial_required_cols:
            if col not in df.columns:
                raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に必須の列 '{col}' が見つかりません。読み込んだ列名: {df.columns.tolist()}")

        # '解答 1' と '正解 1' から正規表現でデータを抽出
        df['extracted_ans1'] = df[target_column_for_ans].astype(str).str.extract(pattern_for_ans_cor_extraction, expand=False)
        df['extracted_cor1'] = df[target_column_for_cor].astype(str).str.extract(pattern_for_ans_cor_extraction, expand=False)

        df_processed = df.copy()

        # '評点/10.00' の数値変換の試行
        if target_column_for_score in df_processed.columns and pd.api.types.is_object_dtype(df_processed[target_column_for_score]):
            print(f"警告: '{os.path.basename(current_input_file_path)}': '{target_column_for_score}' 列が文字列型です。数値に変換を試みます。")
            df_processed[target_column_for_score] = pd.to_numeric(
                df_processed[target_column_for_score], errors='coerce'
            )

        # 不正解の条件でフィルタリングして、誤答者の姓を特定
        incorrect_condition_on_score = df_processed[target_column_for_score].isin(incorrect_score_thresholds) & df_processed[target_column_for_score].notna()
        df_processed['_is_incorrect_flag'] = incorrect_condition_on_score

        # 誤答を行った回答者の「姓」を取得
        incorrect_student_names_or_ids = df_processed[df_processed['_is_incorrect_flag'] == True]['姓'].unique()

        # 誤答を行った回答者全員の、全ての解答データ（正解も含む）を抽出
        incorrect_performers_all_answers_df = df_processed[df_processed['姓'].astype(str).isin(incorrect_student_names_or_ids.astype(str))].copy()
        
        # 不要になった一時的なフラグ列を削除
        incorrect_performers_all_answers_df = incorrect_performers_all_answers_df.drop(columns=['_is_incorrect_flag'])

        # 出力データを「姓」と「開始日時」の順に並べ替え
        sort_by_cols = []
        if '姓' in incorrect_performers_all_answers_df.columns:
            sort_by_cols.append('姓')
        if '開始日時' in incorrect_performers_all_answers_df.columns:
            sort_by_cols.append('開始日時')

        if sort_by_cols:
            final_output_df = incorrect_performers_all_answers_df.sort_values(by=sort_by_cols, ascending=[True] * len(sort_by_cols))
            print(f"情報: '{os.path.basename(current_input_file_path)}': 出力データを '{', '.join(sort_by_cols)}' でソートしました。")
        else:
            final_output_df = incorrect_performers_all_answers_df # ソートする列がなければそのまま
            print(f"警告: '{os.path.basename(current_input_file_path)}': ソート基準列が見つからないためソートされません。")

        # 出力する列の最終選択
        output_cols_base = df.columns.tolist() # df_processedではなくdfの元の列を使う
        final_output_cols_ordered = []
        
        for col in output_cols_base:
            if col in final_output_df.columns:
                final_output_cols_ordered.append(col)
        
        if 'extracted_ans1' in final_output_df.columns and 'extracted_ans1' not in final_output_cols_ordered:
             final_output_cols_ordered.append('extracted_ans1')
        if 'extracted_cor1' in final_output_df.columns and 'extracted_cor1' not in final_output_cols_ordered:
             final_output_cols_ordered.append('extracted_cor1')
        
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

            final_output_df.to_csv(full_output_path, index=False, encoding='utf_8_sig')
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