from sympy import Symbol, Basic, Derivative, Mul, Add, Pow
from src.core.parser.expression_parser import safe_parse
from src.core.evaluator.distance_hungarian import calculate_hungarian_ted
from sympy.core.function import Function
from src.core.generator_v2.rules.rule_chain import step_chain_rule
from src.core.generator_v2.rules.rule_quotient import step_quotient_rule

def safe_replace(expr, old_node, new_node):
    if expr == old_node: return new_node
    if not isinstance(expr, Basic) or not expr.args: return expr
    return expr.func(*[safe_replace(arg, old_node, new_node) for arg in expr.args], evaluate=False)

def get_all_derivatives(expr):
    derivs = []
    if isinstance(expr, Derivative): derivs.append(expr)
    if hasattr(expr, 'args') and expr.args:
        for arg in expr.args: derivs.extend(get_all_derivatives(arg))
    return derivs

def generate_transitions(current_state, x):
    """
    現在の状態から、1ステップだけ進んだ「すべての可能な状態（並行世界）」と
    「適用したルール名」のセットを生成して返す。
    """
    target_derivs = get_all_derivatives(current_state)
    transitions = []
    
    for target in target_derivs:
        inner_expr = target.expr
        new_sub_expr = None
        action_name = ""
        
        if isinstance(inner_expr, Mul):
            # 分母（Pow(..., -1)）があるかどうかで積か商かを判定
            has_denominator = any(isinstance(arg, Pow) and arg.args[1] == -1 for arg in inner_expr.args)
            
            if has_denominator:
                # --- 商の微分 ---
                new_sub_expr = step_quotient_rule(inner_expr, x)
                action_name = "商の微分の公式適用"
            else:
                # --- 積の微分 ---
                f = inner_expr.args[0]
                g = Mul(*inner_expr.args[1:], evaluate=False)
                new_sub_expr = Add(Mul(Derivative(f, x), g, evaluate=False), Mul(f, Derivative(g, x), evaluate=False), evaluate=False)
                action_name = "積の微分の公式適用"
                
        elif isinstance(inner_expr, Add):
            # --- 和の微分 ---
            new_sub_expr = Add(*[Derivative(arg, x) for arg in inner_expr.args], evaluate=False)
            action_name = "和の微分の分配"
            
        elif isinstance(inner_expr, Function):
            # --- 基本関数 vs 合成関数 ---
            inner_arg = inner_expr.args[0]
            if inner_arg == x:
                # 中身がただの x なら基本関数 (例: sin(x))
                new_sub_expr = inner_expr.diff(x)
                action_name = f"{inner_expr.func.__name__} の微分実行"
            else:
                # 中身が x 以外なら合成関数 (例: sin(exp(x)))
                new_sub_expr = step_chain_rule(inner_expr, x)
                action_name = "合成関数の微分の公式適用"
                
        else:
            # --- その他 (x^2 など) ---
            new_sub_expr = inner_expr.diff(x)
            action_name = "基本微分の実行"

        # 展開した部分を元の式にはめ込み、もう一度パースして綺麗なASTにする
        new_state = safe_parse(str(safe_replace(current_state, target, new_sub_expr)))
        transitions.append((new_state, action_name))
        
    return transitions

def build_educational_tree(initial_expr_str, x):
    initial_state = safe_parse(initial_expr_str)
    queue = [(initial_state, 0, [])]
    visited = set()
    milestones = [] 

    while queue:
        current_state, step_depth, history = queue.pop(0)
        state_str = str(current_state)
        
        if state_str in visited: continue
        visited.add(state_str)

        transitions = generate_transitions(current_state, x)
        next_possible_actions = [action for _, action in transitions]
        
        milestones.append({
            "ast": current_state,
            "step": step_depth,
            "history": history,           
            "next_actions": next_possible_actions
        })

        for next_state, action_name in transitions:
            new_history = history + [action_name]
            queue.append((next_state, step_depth + 1, new_history))
            
    return milestones

# =============================================================================
# 🌳 ツリーの視覚的表示関数
# =============================================================================
def print_visual_tree(milestones):
    print("\n=== 🌳 正解マイルストーン・ツリー（数式展開図） ===")
    # ステップ順にソートして階層的に表示
    for ms in sorted(milestones, key=lambda x: x["step"]):
        indent = "    " * ms["step"]
        if ms["step"] == 0:
            print(f"🌟 [初期状態]\n   {ms['ast']}")
        else:
            last_action = ms["history"][-1]
            print(f"{indent}└─({last_action})─▶")
            print(f"{indent}    {ms['ast']}")
    print("===================================================\n")

def analyze_student(student_expr_str, milestones):
    student_ast = safe_parse(student_expr_str)
    best_ms = None
    best_dist = float('inf')

    for ms in milestones:
        dist = calculate_hungarian_ted(student_ast, ms["ast"])
        if dist < best_dist or (dist == best_dist and ms["step"] > (best_ms["step"] if best_ms else -1)):
            best_dist = dist
            best_ms = ms

    return best_ms, best_dist

if __name__ == "__main__":
    x = Symbol('x')
    
    # ★ テスト問題: sin(log(x)) の微分（合成関数）
    problem_str = "Derivative(sin(log(x)), x)"
    
    print("🌳 正解マイルストーン・ツリーを生成中...")
    milestones = build_educational_tree(problem_str, x)
    print_visual_tree(milestones)

    # 仮想の学生データ
    test_students = [
        "cos(log(x)) * (1/x)",                           # 完璧な学生
        "cos(log(x)) * Derivative(log(x), x)",           # 途中式（合成公式は合ってる）
        "cos(1/x)",                                      # ありがちな間違い: 外側と内側を同時に微分しちゃった
    ]

    print("=== 🎓 教育的・自動診断レポート ===")
    for i, ans in enumerate(test_students):
        ms, dist = analyze_student(ans, milestones)
        print(f"\n[学生 {chr(65+i)} の提出] : {ans}")
        
        # 1. 根本的なエラー（距離5.0以上）
        if dist >= 5.0:
            print(f"  👉 診断: 【根本的エラー】(ズレ: {dist})")
            print(f"  💡 先生へ: どの計算ステップとも一致しません。微分の公式を根本から勘違いしています。")
            continue

        # 2. 完璧 または 軽微な表記揺れ（距離1.0以下は許容！）
        if dist <= 1.0:
            if not ms["next_actions"]:
                print(f"  👉 診断: 【完全正解！】(表記揺れ補正込, ズレ: {dist})")
                print(f"  💡 先生へ: 完璧です。すべての微分計算を完了しています。")
            else:
                print(f"  👉 診断: 【途中式でストップ】(ズレ: {dist})")
                print(f"  ✅ 成功した操作: {' -> '.join(ms['history']) if ms['history'] else '立式のみ'}")
                print(f"  ❌ やり残し    : 次は 【{'】か【'.join(ms['next_actions'])}】 を行う必要があります。")
        
        # 3. 具体的な計算ミス（あるノードに向かおうとして失敗した）
        else:
            print(f"  👉 診断: 【計算ミス】(ズレ: {dist})")
            # 履歴の最後のアクションを「ミスした箇所」として抽出する
            success_hist = ms["history"][:-1] if ms["history"] else []
            error_action = ms["history"][-1] if ms["history"] else "初期の立式"
            
            print(f"  ✅ 成功した操作: {' -> '.join(success_hist) if success_hist else '立式のみ'}")
            print(f"  ❌ ミス発生箇所: 【{error_action}】の計算で間違えている可能性が高いです！")
            print(f"  🎯 本来の正解式: {ms['ast']}")