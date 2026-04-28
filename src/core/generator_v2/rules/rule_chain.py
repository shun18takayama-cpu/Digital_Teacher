from sympy import Mul, Derivative, Dummy
from sympy.core.function import Function
from src.core.parser.expression_parser import safe_parse

def step_chain_rule(expr, x):
    """
    合成関数の微分 f(g(x))' を f'(g(x)) * g'(x) に1段階だけ展開する。
    例: sin(exp(x)) -> cos(exp(x)) * Derivative(exp(x), x)
    """
    if not isinstance(expr, Function) or len(expr.args) != 1:
        return expr
        
    g_x = expr.args[0] # 内側の関数 (例: log(x))
    
    # -----------------------------------------------------------
    # 1. 外側の関数 f の微分 (ダミー変数 u を使って SymPy のパニックを回避)
    # -----------------------------------------------------------
    u = Dummy('u')                 # 誰とも被らない架空の文字 u を作る
    f_u = expr.func(u)             # 例: sin(log(x)) を sin(u) にする
    outer_diff_u = f_u.diff(u)     # 例: u で微分して cos(u) にする
    outer_diff = outer_diff_u.subs(u, g_x) # 例: u を log(x) に戻して cos(log(x)) にする!
    
    # 2. 内側の関数 g_x は未計算のまま Derivative に包む
    inner_deriv = Derivative(g_x, x)
    
    # 3. 掛け合わせる
    new_expr = Mul(outer_diff, inner_deriv, evaluate=False)
    
    return safe_parse(str(new_expr))