# src/core/parser/experimental_parser.py
from sympy import Basic, Pow, E, exp, log, Integer, sin, cos, tan, sqrt, Add, Mul, default_sort_key
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

LOCAL_FUNCS = {"sin": sin, "cos": cos, "tan": tan, "exp": exp, "log": log, "ln": log, "sqrt": sqrt, "e": E}
TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))

def canonicalize_ast(expr):
    if not isinstance(expr, Basic) or not expr.args:
        if str(expr) == "E": return E
        return expr

    new_args = [canonicalize_ast(arg) for arg in expr.args]

    # 正準化: e**x -> exp(x)
    if isinstance(expr, Pow):
        base = new_args[0]
        if base == E or str(base) == 'e':
            return exp(new_args[1], evaluate=False)

    # 正準化: log(e) -> 1
    if isinstance(expr, log) and len(new_args) > 0 and new_args[0] == E:
        return Integer(1)

    # =========================================================================
    # 【実験的機能】強制ソート（Add, Mulの項を数学的な標準順に並び替え）
    # =========================================================================
    if isinstance(expr, (Add, Mul)):
        new_args = sorted(new_args, key=default_sort_key)

    return expr.func(*new_args, evaluate=False)

def safe_parse(expr_str):
    try:
        if not isinstance(expr_str, str): return None
        p_str = expr_str.strip().replace('^', '**').translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
        parsed = parse_expr(p_str, local_dict=LOCAL_FUNCS, transformations=TRANSFORMS, evaluate=False)
        return canonicalize_ast(parsed)
    except:
        return None