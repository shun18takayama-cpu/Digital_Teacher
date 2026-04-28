# test_dispatcher.py
# 既存のシステムを一切壊さない、次世代アーキテクチャ(Rev 4.0)の完全独立実験用スクリプト

from sympy import Symbol, Basic, Derivative, Mul, Add
# 唯一、あなたが完成させた「完璧なパーサー」だけは再利用させてもらいます
from src.core.parser.expression_parser import safe_parse

# =============================================================================
# 【Layer 2】現場の職人たち（1ステップだけ展開する機能）
# =============================================================================
def step_product_rule(expr, x):
    """ 積の微分 (fg)' を f'g + fg' に1段階だけ展開する """
    if not isinstance(expr, Mul) or len(expr.args) < 2:
        return expr

    f = expr.args[0]
    g = Mul(*expr.args[1:], evaluate=False)

    term1 = Mul(Derivative(f, x), g, evaluate=False)
    term2 = Mul(f, Derivative(g, x), evaluate=False)
    
    return safe_parse(str(Add(term1, term2, evaluate=False)))

def step_basic_diff(expr, x):
    """ 基本関数の微分（SymPyの標準diffを使って一発で計算） """
    return safe_parse(str(expr.diff(x)))

# =============================================================================
# 【Layer 1】The Dispatcher（司令塔）
# =============================================================================
def find_first_derivative(expr):
    """ ASTを探索し、最初に見つかった未計算の Derivative ノードを返す """
    if isinstance(expr, Derivative):
        return expr
    for arg in expr.args:
        found = find_first_derivative(arg)
        if found:
            return found
    return None

def safe_replace(expr, old_node, new_node):
    """ SymPyのevaluateの暴発を防ぎながら、安全にノードをすげ替える """
    if expr == old_node:
        return new_node
    if not isinstance(expr, Basic) or not expr.args:
        return expr
    
    new_args = [safe_replace(arg, old_node, new_node) for arg in expr.args]
    return expr.func(*new_args, evaluate=False)

def dispatch_next_step(current_state, x):
    """ 司令塔: 次にやるべき微分を見つけ、適切な職人に投げ、結果をはめ込む """
    target_deriv = find_first_derivative(current_state)
    
    # 探しても Derivative が無い ＝ これ以上展開できない（微分完了）
    if target_deriv is None:
        return current_state, "COMPLETED"

    inner_expr = target_deriv.expr
    new_sub_expr = None
    applied_rule = ""

    # ルール判定と職人への振り分け
    if isinstance(inner_expr, Mul):
        new_sub_expr = step_product_rule(inner_expr, x)
        applied_rule = "積の微分 (Product Rule)"
    elif isinstance(inner_expr, Add):
        # 足し算の微分は分配するだけ (f + g)' -> f' + g'
        new_sub_expr = Add(*[Derivative(arg, x) for arg in inner_expr.args], evaluate=False)
        applied_rule = "和の微分分配 (Add Rule)"
    else:
        # その他（e^x や log(x) などの基本関数）
        new_sub_expr = step_basic_diff(inner_expr, x)
        applied_rule = f"基本関数の微分 ({inner_expr.func.__name__})"

    next_state = safe_replace(current_state, target_deriv, new_sub_expr)
    return next_state, applied_rule

# =============================================================================
# 🏃‍♂️ 実験の実行（シミュレーションループ）
# =============================================================================
if __name__ == "__main__":
    x = Symbol('x')
    
    print("=== 🚀 Digital Teacher 次世代エンジン(Rev 4.0) 稼働実験 ===")
    
    # ここに好きな問題（正しい正準形）を入れて実験できます
    # 例: "Derivative(exp(x)*log(x)*sin(x), x)" のように3つの積でも勝手に解きます
    initial_str = "Derivative(exp(x)*log(x), x)"
    current_state = safe_parse(initial_str)
    
    print(f"\n[Step 0] 初期状態\n  式: {current_state}")
    
    step_count = 1
    while True:
        next_state, rule_name = dispatch_next_step(current_state, x)
        
        if rule_name == "COMPLETED":
            print(f"\n✅ すべての微分が完了しました！")
            break
            
        print(f"\n[Step {step_count}] 適用ルール: {rule_name}")
        print(f"  式: {next_state}")
        
        current_state = next_state
        step_count += 1