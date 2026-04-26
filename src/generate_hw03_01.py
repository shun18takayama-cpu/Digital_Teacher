import sympy as sp
from sympy import Symbol, exp, log, Derivative, Mul, Add, srepr

def generate_hw03_01_templates():
    print("🚀 HW03-01 (e^x * log(x)) の正解展開パターンを自動生成します\n")
    
    # 1. 変数と関数の定義
    x = Symbol('x')
    f = exp(x)
    g = log(x)
    
    templates = {}

    # ----------------------------------------------------
    # Pattern 1: 積の微分公式を適用した直後 (未計算)
    # 構造: (f' * g) + (f * g')
    # ----------------------------------------------------
    # evaluate=False を入れることで、SymPyが勝手に計算するのを防ぎます
    term1_uncalc = Mul(Derivative(f, x), g, evaluate=False)
    term2_uncalc = Mul(f, Derivative(g, x), evaluate=False)
    pat1 = Add(term1_uncalc, term2_uncalc, evaluate=False)
    templates['Pattern_1_積の微分適用直後'] = pat1

    # ----------------------------------------------------
    # Pattern 2a: e^xの公式だけ適用 (log(x)は未計算)
    # これにより「e^xの微分はわかっているか」を判定できる
    # ----------------------------------------------------
    term1_calc = Mul(f.diff(x), g, evaluate=False) # e^x * log(x)
    pat2a = Add(term1_calc, term2_uncalc, evaluate=False)
    templates['Pattern_2a_expの公式のみ適用'] = pat2a

    # ----------------------------------------------------
    # Pattern 2b: log(x)の公式だけ適用 (e^xは未計算)
    # これにより「log(x)の微分はわかっているか」を判定できる
    # ----------------------------------------------------
    term2_calc = Mul(f, g.diff(x), evaluate=False) # e^x * (1/x)
    pat2b = Add(term1_uncalc, term2_calc, evaluate=False)
    templates['Pattern_2b_logの公式のみ適用'] = pat2b

    # ----------------------------------------------------
    # Pattern 3: 両方の微分を実行 (未整理)
    # 構造: e^x * log(x) + e^x * (1/x)
    # ----------------------------------------------------
    pat3 = Add(term1_calc, term2_calc, evaluate=False)
    templates['Pattern_3_両方の公式適用済_未整理'] = pat3

    # ----------------------------------------------------
    # Pattern 4: 最終形態 (簡略化・くくり出し)
    # ----------------------------------------------------
    pat4_factor = sp.factor(pat3) # e^x*(log(x) + 1/x)
    pat4_expand = sp.expand(pat3) # e^x*log(x) + e^x/x
    templates['Pattern_4_最終_くくり出し型'] = pat4_factor
    templates['Pattern_4_最終_展開型'] = pat4_expand

    # 結果の出力
    for name, expr in templates.items():
        print(f"■ {name}")
        print(f"  数式表示 : {expr}")
        print(f"  AST(内部): {srepr(expr)}\n")

if __name__ == "__main__":
    generate_hw03_01_templates()