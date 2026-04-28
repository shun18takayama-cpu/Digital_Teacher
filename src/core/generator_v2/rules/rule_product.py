from sympy import Mul, Add, Derivative
from src.core.parser.expression_parser import safe_parse

def step_product_rule(expr, x):
    """ (fg)' -> f'g + fg' の形に1段階だけ展開する """
    if not isinstance(expr, Mul) or len(expr.args) < 2:
        return expr
    f = expr.args[0]
    g = Mul(*expr.args[1:], evaluate=False)
    
    term1 = Mul(Derivative(f, x), g, evaluate=False)
    term2 = Mul(f, Derivative(g, x), evaluate=False)
    return safe_parse(str(Add(term1, term2, evaluate=False)))