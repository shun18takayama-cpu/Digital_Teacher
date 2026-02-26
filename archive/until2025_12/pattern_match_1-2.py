import pandas as pd
import re
import numpy as np
import os
import csv

# --- 設定部分 ---
# 特定のファイルパスを直接指定 (ユーザーが以前アップロードしたファイルを使用)
input_file_path = './all_answer_analysis0/微分積分学Ⅰ 2024（SUI）-HW03-04-解答_誤答者全解答.csv'
encoding_type = 'utf_8_sig'

output_dir = 'all_pattern_match_optimal' # 出力ディレクトリ名

target_column_for_score = '評点/10.00'
incorrect_score_thresholds = [0] # 不正解者リストの作成

# ★ここから最適なパターンマッチング関連の設定を更新
# eの微分: -e^(-x) または -exp(-x) の形のみを残す
# ^の後に()の有無が関係ないように修正
pattern_optimal_exp_derivative = r'(?:-1\s*\*\s*|-)(?:exp\s*\(-x\)|e\s*\^\s*(?:\(-x\)|-x))'

# パターンとそれに対応する新しい列名 (日本語に簡潔化)
pattern_definitions = {
    'PM_eの微分': pattern_optimal_exp_derivative,
}

# 出力したい列のリストにパターンマッチング結果列を追加 (日本語に簡潔化)
output_columns_to_save = [
    '姓', '開始日時', '受験完了', '継続時間',
    '評点/10.00',
    'extracted_ans1', # 元の解答
    'processed_ans1', # 前処理後の解答 (新しく追加)
    'extracted_cor1',
] + list(pattern_definitions.keys()) + ['PM_その他正解', 'PM_その他誤答']
# ★ここまで最適なパターンマッチング関連の設定を更新


# --- メイン処理 ---
os.makedirs(output_dir, exist_ok=True)

current_input_file_path = input_file_path # 指定された単一ファイルを使用
print(f"\n======== {os.path.basename(current_input_file_path)} の処理を開始します ========")

try:
    # CSVファイルを直接読み込む
    df = pd.read_csv(current_input_file_path, encoding=encoding_type)
    df.columns = df.columns.str.strip()

    # -------------------------------------------------------------
    # 必須列の確認
    # 'extracted_ans1'と'extracted_cor1'は既にあるものとしてチェック
    # -------------------------------------------------------------
    initial_required_cols = ['姓', '開始日時', '評点/10.00', 'extracted_ans1', 'extracted_cor1']
    for col in initial_required_cols:
        if col not in df.columns:
            raise KeyError(f"CSVファイル '{os.path.basename(current_input_file_path)}' に必須の列 '{col}' が見つかりません。読み込んだ列名: {df.columns.tolist()}")

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
    df_processed['temp_student_id'] = df_processed['姓'].astype(str)

    incorrect_student_identifiers = df_processed[df_processed['_is_incorrect_flag'] == True]['temp_student_id'].unique()

    # --- extracted_ans1 の前処理: 先頭の '=' を除去し、processed_ans1 列に格納 ---
    df_processed['processed_ans1'] = df_processed['extracted_ans1'].astype(str).apply(
        lambda x: x.lstrip('=').strip() # 先頭の'='を除去し、その後に前後の空白も除去
    )

    # --- パターンマッチング処理を統合 ---
    # パターンマッチング結果を保存する新しい列を初期化
    for col_name in pattern_definitions.keys():
        df_processed[col_name] = ''
    df_processed['PM_その他正解'] = ''
    df_processed['PM_その他誤答'] = ''

    # カウント用の辞書を初期化
    counts = {col_name: 0 for col_name in pattern_definitions.keys()}
    counts['PM_その他正解'] = 0
    counts['PM_その他誤答'] = 0

    for idx, row_data in df_processed.iterrows():
        # パターンマッチングには 'processed_ans1' 列を使用
        response_to_check = str(row_data['processed_ans1'])
        score_to_check = row_data['評点/10.00']

        matched_any_defined_pattern_for_summary = False # 少なくとも1つの最適なパターンにマッチしたか

        # 各最適なパターンをチェックし、マッチした場合は「〇」を付ける
        for pm_col_name, pattern_regex in pattern_definitions.items():
            if pd.notna(response_to_check) and re.search(pattern_regex, response_to_check, re.IGNORECASE):
                df_processed.at[idx, pm_col_name] = '〇'
                # 正答の場合のみカウント対象
                if score_to_check == 10:
                    counts[pm_col_name] += 1
                matched_any_defined_pattern_for_summary = True # いずれかの最適パターンにマッチしたらTrue

        # 「PM_その他正解」のロジック
        if score_to_check == 10:
            if not matched_any_defined_pattern_for_summary:
                df_processed.at[idx, 'PM_その他正解'] = '〇'
                counts['PM_その他正解'] += 1
        # 「PM_その他誤答」のロジック (スコアが0の行かつ、どの最適パターンにもマッチしなかった場合)
        elif score_to_check == 0:
            if not matched_any_defined_pattern_for_summary:
                df_processed.at[idx, 'PM_その他誤答'] = '〇'
                counts['PM_その他誤答'] += 1
    # --- パターンマッチング処理ここまで ---

    # 誤答者の全解答を抽出（パターンマッチング後のdf_processedから）
    final_output_df = df_processed[df_processed['temp_student_id'].isin(incorrect_student_identifiers)].copy()
    final_output_df = final_output_df.drop(columns=['_is_incorrect_flag', 'temp_student_id'])


    # -------------------------------------------------------------
    # 出力データを「姓」と「開始日時」の順に並べ替え
    # -------------------------------------------------------------
    sort_by_cols = []
    if '姓' in final_output_df.columns:
        sort_by_cols.append('姓')
    if '開始日時' in final_output_df.columns:
        sort_by_cols.append('開始日時')

    if sort_by_cols:
        final_output_df = final_output_df.sort_values(by=sort_by_cols, ascending=[True] * len(sort_by_cols))
        print(f"情報: '{os.path.basename(current_input_file_path)}': 出力データを '{', '.join(sort_by_cols)}' でソートしました。")
    else:
        print(f"警告: '{os.path.basename(current_input_file_path)}': ソート基準列が見つからないためソートされません。")


    # -------------------------------------------------------------
    # Excelの #NAME? エラー対策: extracted_ans1 にのみアポストロフィを付加
    # -------------------------------------------------------------
    columns_for_apostrophe_fix = ['extracted_ans1'] # アポストロフィを付加する列を指定
    for col_name in columns_for_apostrophe_fix:
        if col_name in final_output_df.columns:
            is_string_col = pd.api.types.is_string_dtype(final_output_df[col_name])
            if is_string_col:
                final_output_df[col_name] = final_output_df[col_name].astype(str).apply(
                    lambda x: "'" + x if pd.notna(x) else x
                )
                # NaNが'nan'に変換された場合に'nan'の先頭にアポストロフィがついてしまうのを防ぐ
                final_output_df[col_name] = final_output_df[col_name].replace("'nan", np.nan)
            else:
                print(f"情報: 列 '{col_name}' は文字列型ではないため、アポストロフィ対策は適用されません。")


    # -------------------------------------------------------------
    # 出力する列の最終選択
    # -------------------------------------------------------------
    final_output_cols_ordered = []
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
        # 出力ファイル名を「01-02」と分かるように変更
        output_csv_filename_for_this_file = f"HW01-02_pattern_analysis_final_excel_fix_ans1_only_jp.csv" # ここを変更
        full_output_path = os.path.join(output_dir, output_csv_filename_for_this_file)

        final_output_df.to_csv(full_output_path, index=False, encoding='utf_8_sig', quoting=csv.QUOTE_MINIMAL)
        print(f"\n誤答者の全解答リストを '{full_output_path}' に保存しました。")
    else:
        print(f"\n'{os.path.basename(current_input_file_path)}' に保存するデータがないため、ファイルは作成されませんでした。")

    # パターンマッチングの回数を最後にまとめて出力
    print("\n--- サマリー: 最適なパターンマッチングのカウント ---")
    for category, count in counts.items():
        print(f'{category}: {count}')

except FileNotFoundError:
    print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}' が見つかりませんでした。パスを確認してください。")
except UnicodeDecodeError:
    print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}': エンコーディング '{encoding_type}' でのデコードに失敗しました。別のエンコーディングを試してください。")
except KeyError as e:
    print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}': 列 '{e}' がデータフレームに見つかりませんでした。CSVファイルの列名を確認してください。")
    if 'df' in locals():
        print("読み込んだデータフレームの列名:", df.columns.tolist())
except Exception as e:
    import traceback
    print(f"エラー: CSVファイル '{os.path.basename(current_input_file_path)}' の処理中に予期せぬエラーが発生しました: {e}")
    traceback.print_exc()

print(f"======== {os.path.basename(current_input_file_path)} の処理が完了しました ========\n")