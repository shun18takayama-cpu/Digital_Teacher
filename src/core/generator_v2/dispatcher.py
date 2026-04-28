from sympy import Basic, Derivative, Mul, Add
from src.core.generator_v2.rules.rule_product import step_product_rule
from src.core.generator_v2.rules.rule_basic import step_basic_diff

def get_all_derivatives(expr):
    """ ASTを探索し、式の中に含まれる【すべて】の未計算 Derivative ノードをリストで返す """
    derivs = []
    if isinstance(expr, Derivative):
        derivs.append(expr)
    if hasattr(expr, 'args') and expr.args:
        for arg in expr.args:
            derivs.extend(get_all_derivatives(arg))
    return derivs

def safe_replace(expr, old_node, new_node):
    """ SymPyの暴発を防ぎながら、ノードを1箇所だけすげ替える """
    if expr == old_node:
        return new_node
    if not isinstance(expr, Basic) or not expr.args:
        return expr
    new_args = [safe_replace(arg, old_node, new_node) for arg in expr.args]
    return expr.func(*new_args, evaluate=False)

def generate_next_states(current_state, x):
    """
    現在の状態から、1ステップだけ進んだ「すべての可能な状態（並行世界）」を生成する。
    """
    target_derivs = get_all_derivatives(current_state)
    
    if not target_derivs:
        return [] # 微分する場所がもう無い（完了）

    next_states = []
    
    # 式の中にあるすべての微分箇所に対して、それぞれ独立して1ステップ展開を試みる
    for target in target_derivs:
        inner_expr = target.expr
        new_sub_expr = None
        
        # ルール判定と振り分け
        if isinstance(inner_expr, Mul):
            new_sub_expr = step_product_rule(inner_expr, x)
        elif isinstance(inner_expr, Add):
            new_sub_expr = Add(*[Derivative(arg, x) for arg in inner_expr.args], evaluate=False)
        else:
            new_sub_expr = step_basic_diff(inner_expr, x)

        # 展開した部分を元の式にはめ込み、新しい状態として登録
        new_state = safe_replace(current_state, target, new_sub_expr)

        new_state = safe_replace(str(new_state), "Derivative", "Derivative")  # 文字列置換で安全にDerivativeを維持
        
        # 重複を防ぐために文字列で比較して追加
        if not any(str(ns) == str(new_state) for ns in next_states):
            next_states.append(new_state)

    return next_states