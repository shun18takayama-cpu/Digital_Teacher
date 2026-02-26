import pandas as pd
import re
import os

# ==========================================
# 設定項目
# ==========================================
INPUT_FILE = "product_rule_errors_extracted.csv"
OUTPUT_FILE = "product_rule_error_analysis_strict_v3.csv"

# ==========================================
# 誤答分類ロジック（正規表現による厳密化版）
# ==========================================
def classify_strict_v3(row):
    # 前処理：空白除去と小文字化
    ans_str = str(row['解答 1']).replace(' ', '')
    ans_lower = ans_str.lower()
    # ASTは文字列として取得（構造解析用）
    ast_str = str(row['Student_AST'])
    hw_id = row['HW_ID']
    
    # ---------------------------------------------------------
    # 【Step 1】文字列解析 (String Analysis)
    # 目的：AST変換以前の「入力・構文レベル」のミスを弾く
    # ---------------------------------------------------------
    
    # 1. 自然対数の誤入力 (in vs ln)
    # 正規表現: (?<![a-z])in\( は「直前にアルファベットがない in(」を探す
    # これにより sin, min, arcsin 等の中にある "in" は無視される
    if re.search(r'(?<![a-z])in\(', ans_lower) or ans_lower == 'in':
        return "構文エラー：自然対数の誤入力 (in表記)"
        
    # 2. 括弧の省略 (logx)
    if 'logx' in ans_lower and 'log(x)' not in ans_lower:
        return "構文エラー：関数の括弧省略 (logx)"
        
    # 3. システム情報の混入
    if 'seed:' in ans_lower:
        return "システムエラー：シード値の混入"
        
    # 4. 無効な入力
    if ans_lower in ['-', 'x', '0', '', 'nan']: 
        return "無効回答：未入力または無意味な文字"

    # 5. 演算プロセス未完 (文字列での簡易検知)
    if 'diff' in ans_lower or 'd/dx' in ans_lower:
        return "演算未完：微分命令の残存 (diff)"

    # ---------------------------------------------------------
    # 【Step 2】AST構造解析 (Abstract Syntax Tree Analysis)
    # 目的：数式の「構造」を見て、数学的な誤概念を特定する
    # ---------------------------------------------------------
    
    # 演算未完 (ASTレベルでの検知: Derivativeノード)
    if 'derivative' in ast_str.lower():
        return "演算未完：微分命令の残存 (diff)"

    # ASTのルートノード（一番外側の構造）を取得
    # 例: "Add(Mul(...), ...)" -> "Add"
    top_node = ast_str.split('(')[0] if '(' in ast_str else ast_str
    
    # 積の微分問題のリスト
    product_rule_problems = ['HW01-05', 'HW03-01', 'HW03-05', 'HW04-05', 'HW05-01', 'HW05-02']
    
    if hw_id in product_rule_problems:
        # --- 分類C：積の微分の線形化誤認 ---
        # 正解は (uv)' = u'v + uv' なので、ASTの頂点は必ず「和 (Add)」になるはず。
        # もし頂点が Mul(積) や Pow(べき乗) なら、公式の適用自体を間違えていると断定。
        if top_node != 'Add':
            return "誤概念：積の微分の線形化誤認 ((uv)'=u'v')"

    # --- 分類D：商の微分との混同 ---
    # e^x を含む問題で、符号ミス（マイナス）があるかチェック
    if hw_id in ['HW03-01', 'HW05-01']:
        if '-' in ans_str and top_node == 'Add':
             return "誤概念：商の微分との混同 (符号ミス)"

    # --- 分類E：多項式の展開ミス ---
    if hw_id == 'HW01-03':
        if top_node == 'Add':
            return "計算ミス：多項式の展開・係数誤り"
        if top_node == 'Mul':
            return "計算ミス：因数分解形式での提出"

    # ---------------------------------------------------------
    # 【Step 3】識別不能 (Unclassified)
    # ---------------------------------------------------------
    # 上記の網にかからなかった複雑な誤答
    return "識別不能：分類パターンに該当せず"

def run_analysis_strict_v3():
    print("--- 誤答パターンの詳細分析（正規表現厳密化版）を開始します ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。")
        return

    try:
        df = pd.read_csv(INPUT_FILE)
        
        print("厳密化されたアルゴリズムで判定中...")
        df['誤答パターン'] = df.apply(classify_strict_v3, axis=1)
        
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        
        print("\n" + "="*60)
        print("【問題別・誤答パターン集計結果 (v3)】")
        print("="*60)
        
        summary = df.groupby(['HW_ID', '誤答パターン']).size().reset_index(name='件数')
        
        for hw_id in summary['HW_ID'].unique():
            print(f"\n■ 問題 ID: {hw_id}")
            sub_df = summary[summary['HW_ID'] == hw_id].sort_values('件数', ascending=False)
            for _, row in sub_df.iterrows():
                label = row['誤答パターン']
                count = row['件数']
                total = sub_df['件数'].sum()
                percent = (count / total) * 100
                print(f"- {label:<35} : {count:>2} 件 ({percent:>5.1f}%)")
                
        print("\n" + "="*60)
        print(f"完了: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"予期せぬエラー: {e}")

if __name__ == "__main__":
    run_analysis_strict_v3()