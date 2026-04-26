import sys
import os
import zss # Tree Edit Distance計算ライブラリ
from sympy import srepr

# =============================================================================
# ★ パス解決（どこの部屋からでもルートを見つけられるようにする魔法）
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# 新しい部屋の住所を指定してインポート
from src.core.parser.problem_analyzer import safe_parse

# =============================================================================
# 核心ロジック: 木編集距離 (TED) の計算
# =============================================================================

class SymPyNode(object):
    """SymPyのASTをzssライブラリが扱える形式に変換するためのノードクラス"""
    def __init__(self, label):
        self.label = label
        self.children = list()

    @staticmethod
    def get_children(node):
        return node.children

    @staticmethod
    def get_label(node):
        return node.label

def sympy_to_zss(expr):
    """SymPyオブジェクトを再帰的にSymPyNode（木構造）に変換する"""
    label = str(expr.func.__name__)
    if not expr.args:
        label = str(expr)
    
    node = SymPyNode(label)
    for arg in expr.args:
        node.children.append(sympy_to_zss(arg))
    return node

def calculate_ted(expr1_obj, expr2_obj):
    """2つのSymPyオブジェクト間の木編集距離を計算する"""
    tree1 = sympy_to_zss(expr1_obj)
    tree2 = sympy_to_zss(expr2_obj)
    return zss.simple_distance(tree1, tree2, SymPyNode.get_children, SymPyNode.get_label)

# =============================================================================
# 動作テスト
# =============================================================================
def main():
    # テスト例: 生徒が少し整理をサボったケース
    correct_template = "2*x"
    student_answer = "x + x"
    
    print(f"--- 評価部門(TED) テスト開始 ---")
    
    # Parser部門(受付)の機能を呼び出す
    obj1 = safe_parse(correct_template)
    obj2 = safe_parse(student_answer)
    
    dist = calculate_ted(obj1, obj2)
    
    print(f"テンプレート: {correct_template}")
    print(f"生徒の解答  : {student_answer}")
    print(f"木距離(TED) : {dist}")
    
    if dist == 0:
        print("結果: 完全一致（構造も同じ）")
    else:
        print("結果: 数学的に正しくても、書き方（構造）が違います！")

if __name__ == "__main__":
    main()