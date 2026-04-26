import sys
import os
import zss
from sympy import srepr

# パス解決（常にプロジェクトルートを基準にする）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.core.parser.problem_analyzer import safe_parse

class SymPyNode:
    def __init__(self, label):
        self.label = label
        self.children = []

    @staticmethod
    def get_children(node): return node.children
    @staticmethod
    def get_label(node): return node.label

def sympy_to_zss(expr):
    """SymPyオブジェクトをzssが扱える木構造に変換"""
    label = str(expr.func.__name__)
    if not expr.args: label = str(expr)
    node = SymPyNode(label)
    for arg in expr.args:
        node.children.append(sympy_to_zss(arg))
    return node

def calculate_ted(expr1_obj, expr2_obj):
    """zssライブラリを使用した木編集距離の計算"""
    try:
        tree1 = sympy_to_zss(expr1_obj)
        tree2 = sympy_to_zss(expr2_obj)
        return zss.simple_distance(tree1, tree2, SymPyNode.get_children, SymPyNode.get_label)
    except Exception as e:
        print(f"TED計算中にエラー: {e}")
        return -1