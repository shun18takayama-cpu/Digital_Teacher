# pythonコード
# 1-4.py （棒グラフ作成機能を含むdata_analyzerを呼び出す）
from data_analyzer import analyze_and_save_incorrect_answers

input_csv_file_1 = r'./微分積分学データ/微分積分学Ⅰ 2024（SUI）-HW01-04-解答.csv'
output_directory_1 = 'output_results'
output_file_name_1 = '1-4_不正解者リスト.csv'
encoding_for_file_1 = 'utf_8_sig'

print(f"--- {input_csv_file_1} の処理を開始します ---")
analyze_and_save_incorrect_answers(
    input_file_path=input_csv_file_1,
    output_dir=output_directory_1,
    encoding_type=encoding_for_file_1,
    output_filename=output_file_name_1,
    target_column_for_ans='解答 1',
    target_column_for_score='評点/10.00',
    incorrect_score_threshold=0,
    create_histograms=True,
    histogram_column='得点',
    create_extracted_ans_bar_chart=True # この引数をTrueにする（デフォルト）
)
print(f"--- {input_csv_file_1} の処理が完了しました ---")
