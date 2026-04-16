import argparse
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.ast_analyzer import ASTAnalyzer

# 教授に見せる最大の武器：複数の正解テンプレートを定義
CORRECT_TEMPLATES = {
    "展開型": "e^x*log(x) + e^x/x",
    "因数分解型": "e^x*(log(x) + 1/x)",
    "通分型": "(x*e^x*log(x) + e^x) / x"
}

def main():
    parser = argparse.ArgumentParser(description="マルチテンプレート対応 AST評価ツール")
    parser.add_argument("--input", required=True, help="入力CSVファイルのパス")
    parser.add_argument("--output", required=True, help="出力CSVファイルのパス")
    parser.add_argument("--scores", type=str, default="0,10", help="評価対象のスコア")
    
    args = parser.parse_args()
    input_csv = args.input
    output_csv = args.output
    target_scores = [s.strip() for s in args.scores.split(",")]

    print(f"🚀 [マルチテンプレートAST評価] 処理を開始します...")
    
    if not os.path.exists(input_csv):
        print(f"❌ エラー: 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)

    df = pd.read_csv(input_csv)
    col_score = '評点/10.00'
    target_answers = df[df[col_score].astype(str).isin(target_scores)].copy()
    
    results = []
    analyzer = ASTAnalyzer()

    # あらかじめ正解テンプレートをすべてパースしておく（高速化のため）
    parsed_templates = {}
    for name, expr_str in CORRECT_TEMPLATES.items():
        parsed_templates[name] = analyzer.process_expression(expr_str)

    for index, row in target_answers.iterrows():
        student_id = row.get('姓', '不明')
        student_str = str(row.get('student_expr', ''))
        original_score = row[col_score]
        
        if student_str == 'nan' or not student_str.strip():
            continue
            
        stud_data = analyzer.process_expression(student_str)
        
        # 出力する1行分のデータ（辞書）のベースを作成
        row_dict = {
            '学生ID': student_id,
            '元のスコア': original_score,
            '学生_正規化': stud_data["normalized_expr"] if stud_data["status"] == "Success" else str(stud_data["raw_expr"]),
            'ステータス': stud_data["status"]
        }

        # エラー時の処理
        if stud_data["status"] == "Error":
            row_dict.update({
                '展開型': -1, '因数分解型': -1, '通分型': -1,
                '最小木距離': -1,
                '推測される意図': 'パース不能',
                '学生AST': 'Error',
                '目標AST': '',
                '評価値': '', 'コメント': ''
            })
            results.append(row_dict)
            continue

        min_dist = float('inf')
        best_match_name = ""

        # 🌟 各テンプレートとの距離を個別の列として保存
        for name, corr_data in parsed_templates.items():
            if corr_data["status"] == "Error": 
                row_dict[name] = -1
                continue
            
            # ハンガリアンTEDでの距離を計算
            dist = analyzer.tree_edit_distance(corr_data["sympy_expr"], stud_data["sympy_expr"])
            row_dict[name] = dist  # 列名に数値を直接入れる
            
            # 最小距離を更新
            if dist < min_dist:
                min_dist = dist
                best_match_name = name

        # 最も近かった目標モデルのASTを取得
        best_ast_str = parsed_templates[best_match_name]["ast_str"] if best_match_name else ""

        # 🌟 AST文字列と、手動アノテーション用の空欄を追加
        row_dict.update({
            '最小木距離': min_dist,
            '推測される意図': best_match_name,
            '学生AST': stud_data["ast_str"],
            '目標AST': best_ast_str,
            '評価値': '',  # 手動入力用
            'コメント': '' # 手動入力用
        })
        
        results.append(row_dict)

    # 🌟 Excel等で見たときに美しいカラム（列）の並び順を強制する
    columns_order = [
        '学生ID', '元のスコア', 'ステータス', '学生_正規化', 
        '展開型', '因数分解型', '通分型', 
        '最小木距離', '推測される意図', 
        '学生AST', '目標AST', 
        '評価値', 'コメント'
    ]
    
    res_df = pd.DataFrame(results)
    
    for col in columns_order:
        if col not in res_df.columns:
            res_df[col] = ''
    res_df = res_df[columns_order]
    
    # 🌟 ここでソートを実行！（元のスコアは降順[False]、学生IDは昇順[True]）
    res_df = res_df.sort_values(by=['元のスコア', '学生ID'], ascending=[False, True])
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    res_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"✅ 処理完了: 結果を {output_csv} に出力しました。")

if __name__ == "__main__":
    main()