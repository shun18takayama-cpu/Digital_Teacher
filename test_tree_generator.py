from sympy import Symbol
from src.core.parser.expression_parser import safe_parse
from src.core.generator_v2.dispatcher import generate_next_states

def build_milestone_tree(initial_expr_str):
    x = Symbol('x')
    initial_state = safe_parse(initial_expr_str)
    
    # 探索用キュー (ステップ数, 状態)
    queue = [(0, initial_state)]
    visited = set()
    milestones = {}

    print(f"=== 🌳 マイルストーン・ツリー自動生成 ===")
    print(f"問題: {initial_expr_str}\n")

    while queue:
        step_depth, current_state = queue.pop(0)
        state_str = str(current_state)
        
        if state_str in visited:
            continue
        visited.add(state_str)

        # マイルストーンの記録
        if step_depth not in milestones:
            milestones[step_depth] = []
        milestones[step_depth].append(current_state)

        print(f"[Step {step_depth}] {state_str}")

        # 次の可能な状態（並行世界）をすべて取得
        next_states = generate_next_states(current_state, x)
        
        if not next_states:
            print(f"   └─▶ (このルートは計算完了)")
        
        for ns in next_states:
            queue.append((step_depth + 1, ns))
            
    return milestones

if __name__ == "__main__":
    # HW03-01の式を入れてテスト
    build_milestone_tree("Derivative(exp(x)*log(x), x)")