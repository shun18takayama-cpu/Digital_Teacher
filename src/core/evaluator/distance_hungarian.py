import sys
import os
import numpy as np
from scipy.optimize import linear_sum_assignment

# パス解決
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

def get_tree_size(expr):
    """ノードの総数を計算（削除・挿入コスト算出用）"""
    if not hasattr(expr, 'args') or not expr.args: 
        return 1
    return 1 + sum(get_tree_size(arg) for arg in expr.args)

def calculate_hungarian_ted(expr_a, expr_b):
    """ハンガリアン法を用いた順序無視の木編集距離（Hungarian TED）"""
    # 1. 葉ノードの比較
    if not hasattr(expr_a, 'args') or not hasattr(expr_b, 'args'):
        return 0 if str(expr_a) == str(expr_b) else 1

    # 2. ルート（関数名）のコスト
    root_cost = 0 if expr_a.func == expr_b.func else 1

    # 3. 子ノード同士のマッチング
    args_a, args_b = expr_a.args, expr_b.args
    n, m = len(args_a), len(args_b)
    
    if n == 0 or m == 0:
        return root_cost + abs(get_tree_size(expr_a) - get_tree_size(expr_b))

    # コスト行列の作成（再帰）
    cost_matrix = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            cost_matrix[i, j] = calculate_hungarian_ted(args_a[i], args_b[j])

    # ハンガリアン法による最適割り当て
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    matching_cost = cost_matrix[row_ind, col_ind].sum()

    # あぶれたノードのコスト加算
    unmatched_a_cost = sum(get_tree_size(args_a[i]) for i in range(n) if i not in row_ind)
    unmatched_b_cost = sum(get_tree_size(args_b[j]) for j in range(m) if j not in col_ind)

    return root_cost + matching_cost + unmatched_a_cost + unmatched_b_cost