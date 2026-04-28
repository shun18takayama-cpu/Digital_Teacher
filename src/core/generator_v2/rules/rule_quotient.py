from sympy import Mul, Add, Derivative, Pow
from src.core.parser.expression_parser import safe_parse

def step_quotient_rule(expr, x):
    """
    商の微分 (f/g)' を (f'g - fg') / g^2 に1段階だけ展開する。
    """
    if not isinstance(expr, Mul):
        return expr
        
    # SymPyでは f/g は f * g**(-1) としてパースされる。
    # g**(-1) の部分（分母）を探す。
    numer_args = []
    denom_base = None
    
    for arg in expr.args:
        if isinstance(arg, Pow) and arg.args[1] == -1:
            denom_base = arg.args[0]
        else:
            numer_args.append(arg)
            
    # 分母が存在しない場合は商の微分ではないのでそのまま返す
    if denom_base is None:
        return expr
        
    f = Mul(*numer_args, evaluate=False) if len(numer_args) > 1 else numer_args[0]
    g = denom_base
    
    # 公式: (f'g - fg') / g^2
    # f'g
    term1 = Mul(Derivative(f, x), g, evaluate=False)
    # -fg'
    term2 = Mul(-1, f, Derivative(g, x), evaluate=False)
    
    # 分子 = f'g - fg'
    numerator = Add(term1, term2, evaluate=False)
    
    # 分母 = g^2
    denominator = Pow(g, 2, evaluate=False)
    
    # (分子) * (分母)^(-1)
    new_expr = Mul(numerator, Pow(denominator, -1, evaluate=False), evaluate=False)
    
    return safe_parse(str(new_expr))