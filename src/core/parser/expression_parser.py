import re
from sympy import Basic, Pow, E, exp, log, Integer, sin, cos, tan, sqrt, Symbol
from sympy.parsing.sympy_parser import (
    parse_expr, 
    standard_transformations, 
    implicit_multiplication_application
)

# 評価用のパース設定（ここでローカル関数を定義）
LOCAL_FUNCS = {"sin": sin, "cos": cos, "tan": tan, "exp": exp, "log": log, "ln": log, "sqrt": sqrt,"e": E}
TRANSFORMS = (standard_transformations + (implicit_multiplication_application,))

def canonicalize_ast(expr):
    """
    ASTを評価（evaluate）せずに、表記だけを強制統一（正準化）する。
    [ルール]
    1. e**x (Pow(E, x)) -> exp(x)
    2. log(e) -> 1
    """
    if not isinstance(expr, Basic) or not expr.args:
        # e という定数をそのまま扱うための保護
        if str(expr) == "E":
            return E
        return expr

    # 1. 子供のノードをボトムアップで再帰的に正準化
    new_args = [canonicalize_ast(arg) for arg in expr.args]

    # 2. e**x を exp(x) に強制統一
    if isinstance(expr, Pow) and expr.args[0] == E:
        base = new_args[0]
        if base == E or str(base) == "e":  # さらに安全に E と認識できるように
            return exp(new_args[1], evaluate=False)

    # 3. log(e) のようなゴミを 1 に強制変換（SymPyの自動計算漏れ対策）
    if isinstance(expr, log) and len(new_args) > 0 and new_args[0] == E:
        return Integer(1)

    # 新しい引数でノードを再構築
    return expr.func(*new_args, evaluate=False)

def safe_parse(expr_str):
    """
    文字列を安全にパースし、正準化済みのASTを返す。
    外部からはこの関数だけを呼び出す。
    """
    try:
        if not isinstance(expr_str, str):
            return None
        
        # 強固な前処理
        p_str = expr_str.strip().replace('^', '**')
        # 全角を半角に変換
        p_str = p_str.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

        # パース (evaluate=False を絶対維持)
        parsed = parse_expr(p_str, local_dict=LOCAL_FUNCS, transformations=TRANSFORMS, evaluate=False)
        
        # 最後に必ず正準化（表記統一）を通す
        return canonicalize_ast(parsed)
    except Exception as e:
        # print(f"[safe_parse Error] '{expr_str}' -> {type(e).__name__}: {e}")
        return None