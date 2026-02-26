# pythonコード
# data_analyzer.py （extracted_ans1の棒グラフ作成機能を追加）

import pandas as pd
import re
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_and_save_incorrect_answers(
    input_file_path: str,
    output_dir: str,
    encoding_type: str = 'cp932',
    output_filename: str = 'incorrect_answers_report.csv',
    target_column_for_ans: str = '解答 1',
    target_column_for_score: str = '評点/10.00',
    incorrect_score_threshold: int = 0,
    create_histograms: bool = True,
    histogram_column: str = '得点',
    create_extracted_ans_bar_chart: bool = True # 抽出された解答の棒グラフを作成するかどうかの引数を追加
):
    """
    指定されたCSVファイルを読み込み、不正解の解答を抽出し、指定ディレクトリにCSVとして保存します。
    オプションでヒストグラムとextracted_ans1の棒グラフも作成し、保存します。

    Args:
        input_file_path (str): 入力CSVファイルのパス。
        output_dir (str): 出力ファイルを保存するディレクトリのパス。
        encoding_type (str): 入力CSVファイルのエンコーディング。
        output_filename (str): 出力CSVファイルのファイル名。
        target_column_for_ans (str): ans1形式の文字列が格納されている列の名前。
        target_column_for_score (str): 評点などの数値評価が格納されている列の名前。
        incorrect_score_threshold (int): 不正解と判断する評点のしきい値。
        create_histograms (bool): 得点などのヒストグラムを作成し保存するかどうか。
        histogram_column (str): ヒストグラムを作成する対象の数値列名。
        create_extracted_ans_bar_chart (bool): extracted_ans1の棒グラフを作成し保存するかどうか。
    """
    try:
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)

        df = pd.read_csv(input_file_path, encoding=encoding_type)

        # 列名の確認
        required_columns = ['姓', target_column_for_ans, target_column_for_score, histogram_column]
        for col in required_columns:
            if col not in df.columns:
                raise KeyError(f"CSVファイルに必須の列 '{col}' が見つかりません。")

        # 'ans1'形式の文字列を抽出
        pattern = r'ans1:\s*(.*?)\s*\[score\]'
        df['extracted_ans1'] = df[target_column_for_ans].str.extract(pattern)

        # NaN（抽出できなかった行）を削除
        df_cleaned = df.dropna(subset=['extracted_ans1'])

        # extracted_ans1でソート
        sorted_df_cleaned = df_cleaned.sort_values(by='extracted_ans1', ascending=True)

        # '評点/10.00' の数値変換の試行
        if df[target_column_for_score].dtype == 'object':
            print(f"警告: '{target_column_for_score}' 列が文字列型です。数値に変換を試みます。")
            sorted_df_cleaned[target_column_for_score] = pd.to_numeric(
                sorted_df_cleaned[target_column_for_score], errors='coerce'
            )
            sorted_df_cleaned = sorted_df_cleaned.dropna(subset=[target_column_for_score])


        incorrect_answers_df = sorted_df_cleaned[sorted_df_cleaned[target_column_for_score] == incorrect_score_threshold]

        # 出力する列を選択
        output_df = incorrect_answers_df[['姓', 'extracted_ans1', target_column_for_score]]

        print(f"\n--- {output_filename} ---")
        print("不正解の解答一覧（表示）：")
        if output_df.empty:
            print("不正解の解答は見つかりませんでした。")
        else:
            print(output_df)
        print("---")

        # 結果をCSVファイルとして保存
        if not output_df.empty:
            full_output_path = os.path.join(output_dir, output_filename)
            output_df.to_csv(full_output_path, index=False, encoding='utf_8_sig')
            print(f"結果を '{full_output_path}' に保存しました。")
        else:
            print("保存するデータがないため、ファイルは作成されませんでした。")

        # -------------------------------------------------------------
        # ヒストグラム作成のコード（前回追加した部分）
        # -------------------------------------------------------------
        base_input_filename = os.path.splitext(os.path.basename(input_file_path))[0]
        if create_histograms:
            if pd.api.types.is_numeric_dtype(sorted_df_cleaned[histogram_column]):
                print(f"\n--- '{histogram_column}' のヒストグラムを作成します ---")
                hist_output_filename_all = f"{base_input_filename}_全体_{histogram_column}_hist.png"
                plt.figure(figsize=(10, 6))
                sns.histplot(sorted_df_cleaned[histogram_column], bins=10, kde=True)
                plt.title(f'全体の{histogram_column}の分布 - {base_input_filename}')
                plt.xlabel(histogram_column)
                plt.ylabel('頻度')
                plt.grid(axis='y', alpha=0.75)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, hist_output_filename_all))
                plt.close()

                if not incorrect_answers_df.empty and pd.api.types.is_numeric_dtype(incorrect_answers_df[histogram_column]):
                    hist_output_filename_incorrect = f"{base_input_filename}_不正解者_{histogram_column}_hist.png"
                    plt.figure(figsize=(10, 6))
                    sns.histplot(incorrect_answers_df[histogram_column], bins=10, kde=True, color='red')
                    plt.title(f'不正解者の{histogram_column}の分布 - {base_input_filename}')
                    plt.xlabel(histogram_column)
                    plt.ylabel('頻度')
                    plt.grid(axis='y', alpha=0.75)
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, hist_output_filename_incorrect))
                    plt.close()
                else:
                    print(f"不正解者のデータがないか、'{histogram_column}'列が数値型でないため、不正解者のヒストグラムは作成できませんでした。")
            else:
                print(f"警告: ヒストグラム作成対象の列 '{histogram_column}' が数値型ではありません。ヒストグラムは作成されませんでした。")

        # -------------------------------------------------------------
        # extracted_ans1の棒グラフ作成のコードを追加
        # -------------------------------------------------------------
        if create_extracted_ans_bar_chart:
            print(f"\n--- 'extracted_ans1' の棒グラフを作成します ---")
            bar_chart_output_filename = f"{base_input_filename}_extracted_ans1_bar.png"

            # 各解答の出現回数をカウント
            # 全体と不正解者の両方で作成することを想定
            ans_counts_all = sorted_df_cleaned['extracted_ans1'].value_counts()
            ans_counts_incorrect = incorrect_answers_df['extracted_ans1'].value_counts()

            # 全体の解答の棒グラフ
            if not ans_counts_all.empty:
                plt.figure(figsize=(12, 7)) # グラフサイズを調整
                sns.barplot(x=ans_counts_all.index, y=ans_counts_all.values, palette='viridis')
                plt.title(f'抽出された解答の出現回数（全体） - {base_input_filename}')
                plt.xlabel('解答')
                plt.ylabel('出現回数')
                plt.xticks(rotation=45, ha='right') # ラベルが重ならないように回転
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, hist_output_filename_all.replace('_hist.png', '_extracted_ans_all_bar.png')))
                plt.close()
            else:
                print("全体データに抽出された解答がないため、棒グラフは作成されませんでした。")

            # 不正解者の解答の棒グラフ
            if not ans_counts_incorrect.empty:
                plt.figure(figsize=(12, 7))
                sns.barplot(x=ans_counts_incorrect.index, y=ans_counts_incorrect.values, palette='magma')
                plt.title(f'不正解者の抽出された解答の出現回数 - {base_input_filename}')
                plt.xlabel('解答')
                plt.ylabel('出現回数')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, bar_chart_output_filename))
                plt.close()
            else:
                print("不正解者の抽出された解答がないため、棒グラフは作成されませんでした。")
        # -------------------------------------------------------------

    except FileNotFoundError:
        print(f"エラー: 指定されたファイル '{input_file_path}' が見つかりませんでした。パスを確認してください。")
    except UnicodeDecodeError:
        print(f"エンコーディング '{encoding_type}' でのデコードに失敗しました。別のエンコーディングを試してください。")
    except KeyError as e:
        print(f"エラー: 列 '{e}' がデータフレームに見つかりませんでした。CSVファイルの列名を確認してください。")
        try:
            print("読み込んだデータフレームの列名:", df.columns.tolist())
        except NameError:
            print("データフレームの読み込みに失敗したため、列名を表示できません。")
    except Exception as e:
        import traceback
        print(f"処理中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc()