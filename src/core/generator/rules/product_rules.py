import sys
import os
import sympy as sp
from sympy import Symbol, Derivative, Mul, Add, srepr

# =============================================================================
# ★ パス解決（Import地獄の回避）
# =============================================================================
# 現在のファイル(product_rule.py)から見て、5階層上のディレクトリ(Digital_Teacher)
# をPythonの世界の中心（ルート）として強制認識させます。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# 新しいアーキテクチャのパスで、safe_parseを読み込む
from src.core.parser.problem_analyzer import safe_parse

# =============================================================================
# コアロジック: 積の微分エンジン
# =============================================================================
def apply_product_rule(expr, x):
    """
    Module 2a: 積の微分 (Mul) の展開パターンを自動生成するエンジン
    入力された expr (Mulオブジェクト) を解体してパターンを作る。
    """
    # 簡略化のため、今回は2つの項 (f * g) の掛け算のみに対応
    if len(expr.args) != 2:
        return {"Error": "現在は2つの項の積にのみ対応しています"}

    # expr.args から自動で中身を取り出す
    f, g = expr.args
    
    templates = {}

    # 1. 公式適用直後 (未計算) : f'*g + f*g'
    term1_uncalc = Mul(Derivative(f, x), g, evaluate=False)
    term2_uncalc = Mul(f, Derivative(g, x), evaluate=False)
    pat1 = Add(term1_uncalc, term2_uncalc, evaluate=False)
    templates['Pattern_1_積の微分適用直後'] = pat1

    # 2a. fのみ計算 : e^xの微分だけやった状態
    term1_calc = Mul(f.diff(x), g, evaluate=False) 
    pat2a = Add(term1_calc, term2_uncalc, evaluate=False)
    templates['Pattern_2a_左側のみ計算'] = pat2a

    # 2b. gのみ計算 : log(x)の微分だけやった状態
    term2_calc = Mul(f, g.diff(x), evaluate=False) 
    pat2b = Add(term1_uncalc, term2_calc, evaluate=False)
    templates['Pattern_2b_右側のみ計算'] = pat2b

    # 3. 両方計算 (未整理)
    pat3 = Add(term1_calc, term2_calc, evaluate=False)
    templates['Pattern_3_両方の微分完了_未整理'] = pat3

    # 4. 最終形態（簡略化）
    templates['Pattern_4_最終_展開型'] = sp.expand(pat3)
    
    return templates

# =============================================================================
# 動作テスト用メイン処理
# =============================================================================
def main():
    x = Symbol('x')
    
    # テストする数式（HW03-01）
    expr_str = "exp(x) * log(x)"
    print(f"--- 積の微分エンジン テスト開始 ---\n入力文字列: {expr_str}\n")
    
    # Module 1: パース
    parsed_expr = safe_parse(expr_str)
    
    if parsed_expr is None:
        print("パースに失敗しました。")
        return

    # Module 2: ルール判定と実行
    if parsed_expr.func == Mul:
        print("➡️ 一番外側の構造が『Mul (積)』であることを検知しました！\n➡️ 積の微分エンジン (apply_product_rule) を起動します。\n")
        
        patterns = apply_product_rule(parsed_expr, x)
        
        for name, expr_obj in patterns.items():
            print(f"■ {name}")
            print(f"  数式表示: {expr_obj}")
            print(f"  AST詳細 : {srepr(expr_obj)}\n")
    else:
        print(f"Mulではありません。（{parsed_expr.func}です）")

if __name__ == "__main__":
    main()