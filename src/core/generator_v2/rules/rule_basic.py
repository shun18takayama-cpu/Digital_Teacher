from src.core.parser.expression_parser import safe_parse

def step_basic_diff(expr, x):
    """ e^x や log(x) などの基本関数を1発で微分する """
    return safe_parse(str(expr.diff(x)))