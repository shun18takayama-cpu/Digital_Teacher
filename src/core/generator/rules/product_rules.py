from sympy import Mul, Add, Derivative, factor
from src.core.parser.expression_parser import safe_parse

def apply_product_rule(expr, x):
    """
    積の微分ルール (fg)' = f'g + fg' に基づき、複数の展開パターンを生成する。
    【全方位拡張版】因数分解時の「順序違い」を徹底的に網羅。
    """
    templates = {}
    
    if not isinstance(expr, Mul) or len(expr.args) < 2:
        templates["Pattern_0_Base"] = expr
        return templates

    f = expr.args[0]
    g = Mul(*expr.args[1:], evaluate=False)

    df_unresolved = Derivative(f, x)
    dg_unresolved = Derivative(g, x)
    df_eval = f.diff(x)
    dg_eval = g.diff(x)

    # -------------------------------------------------------------------------
    # Pattern 1 & 1.5 & 2: 途中式パターン（変更なし）
    # -------------------------------------------------------------------------
    templates["Pattern_1_積の微分適用直後"] = safe_parse(str(Add(Mul(df_unresolved, g, evaluate=False), Mul(f, dg_unresolved, evaluate=False), evaluate=False)))
    templates["Pattern_1.5a_前項のみ微分完了"] = safe_parse(str(Add(Mul(df_eval, g, evaluate=False), Mul(f, dg_unresolved, evaluate=False), evaluate=False)))
    templates["Pattern_1.5b_後項のみ微分完了"] = safe_parse(str(Add(Mul(df_unresolved, g, evaluate=False), Mul(f, dg_eval, evaluate=False), evaluate=False)))
    templates["Pattern_2_両方の微分実行完了"] = safe_parse(str(Add(Mul(df_eval, g, evaluate=False), Mul(f, dg_eval, evaluate=False), evaluate=False)))

    # -------------------------------------------------------------------------
    # Pattern 3: SymPyによる完全自動整理
    # -------------------------------------------------------------------------
    pattern_3 = expr.diff(x)
    templates["Pattern_3_最終展開形"] = safe_parse(str(pattern_3))

    # -------------------------------------------------------------------------
    # Pattern 4: 共通因数でのくくり出し（バリエーション徹底網羅）
    # -------------------------------------------------------------------------
    pattern_4_base = factor(pattern_3)
    templates["Pattern_4a_因数分解_標準"] = safe_parse(str(pattern_4_base))

    # factorの結果が「A * (B + C)」のような形（Mulで要素が2つ）の場合、順序を入れ替える
    if isinstance(pattern_4_base, Mul) and len(pattern_4_base.args) == 2:
        arg1, arg2 = pattern_4_base.args
        
        # 4b: 因数を後ろに配置 -> (B + C) * A
        pattern_4b = Mul(arg2, arg1, evaluate=False)
        templates["Pattern_4b_因数分解_因数後置"] = safe_parse(str(pattern_4b))
        
        # カッコの中身が足し算（Addで要素が2つ）の場合、さらにその中身も入れ替える
        if isinstance(arg2, Add) and len(arg2.args) == 2:
            inner1, inner2 = arg2.args
            reversed_add = Add(inner2, inner1, evaluate=False)
            
            # 4c: カッコの中身を逆順 + 因数前置 -> A * (C + B)
            pattern_4c = Mul(arg1, reversed_add, evaluate=False)
            templates["Pattern_4c_因数分解_項逆順_前"] = safe_parse(str(pattern_4c))
            
            # 4d: カッコの中身を逆順 + 因数後置 -> (C + B) * A
            pattern_4d = Mul(reversed_add, arg1, evaluate=False)
            templates["Pattern_4d_因数分解_項逆順_後"] = safe_parse(str(pattern_4d))

    return templates