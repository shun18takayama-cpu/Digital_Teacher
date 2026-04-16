import sympy

class ASTNode:
    def __init__(self,value:str):
        self.value = value
        self.left = None
        self.right = None
        self.id = None

current_id = 1

node_root = ASTNode("+")
node_root.left = ASTNode("x")
node_root.right = ASTNode("y")

memo_table = {}

#帰りかけ順
def print_post_order(node:ASTNode) -> str:
    global current_id

    if node is None:
        return
    
    print_post_order(node.left)
    
    print_post_order(node.right)

    node.id = current_id
    current_id += 1
    '''
    print(node.value)
    print(node.id)
    '''
#print(print_post_order(node_root))

def check_node_diff(node_a :ASTNode, node_b :ASTNode):
    global memo_table

    if node_a.value == node_b.value :
        return 0
    else :
        return 1

    

def compare_trees(node_a :ASTNode,node_b:ASTNode) ->int:

    if node_a is None and node_b is None:
        return 0

    if node_a is None or node_b is None:
        return 1
    
    pair_id = (node_a.id,node_b.id)
    
    if pair_id in memo_table:
        return memo_table[pair_id]

    base_cost = check_node_diff(node_a,node_b)

    straight_cost = compare_trees(node_a.left,node_b.left) + compare_trees(node_a.right,node_b.right)
    print(f"straight {straight_cost}")

    cross_cost = compare_trees(node_a.left,node_b.right) + compare_trees(node_a.right,node_b.left)
    print(f"cross_cost {cross_cost}")
    total_cost = base_cost + min(straight_cost,cross_cost)

    if total_cost > 0 :
        str_a = ast_to_string(node_a)
        str_b = ast_to_string(node_b)

        try :
            diff_expr = sympy.simplify(f"{str_a} - {str_b}")

            if diff_expr ==0:
                print(f"{str_a}と{str_b}は数学的に等値です")

                total_cost = 0
        
        except Exception as e:
            print("error")


    memo_table[pair_id] = total_cost

    return total_cost

#多分だけれどこれは外部ライブラリからインポートすればいいんじゃない？
def ast_to_string(node:ASTNode):
    if node is None:
        return ""
    
    if node.left is None and node.right is None:
        return node.value

    left_str = ast_to_string(node.left)
    right_str = ast_to_string(node.right)

    result_str = "(" + left_str + node.value + right_str +")"

    return result_str

tree_a = ASTNode("+")
tree_a.left = ASTNode("+")
tree_a.left.left = ASTNode("a")
tree_a.left.right = ASTNode("b")
tree_a.right = ASTNode("c")

# 誤答の木 B: a + (b + c)
tree_b = ASTNode("+")
tree_b.left = ASTNode("a")
tree_b.right = ASTNode("+")
tree_b.right.left = ASTNode("b")
tree_b.right.right = ASTNode("c")

# IDの割り振り（※あなたの関数名 print_post_order をそのまま使用）
print_post_order(tree_a)
print_post_order(tree_b)

# ==========================================
# おすすめの確認手順2：比較前に「配管（文字列化）」をテストする
# （SymPyに渡される文字列が正しいか、人間の目で事前に確認する）
# ==========================================
print("--- 1. 文字列化の確認 ---")
str_a = ast_to_string(tree_a)
str_b = ast_to_string(tree_b)
print(f"tree_a: {str_a}")  
print(f"tree_b: {str_b}")  

# ==========================================
# 本番の比較実行
# ==========================================
print("\n--- 2. 結合法則の比較テスト開始 ---")
final_cost = compare_trees(tree_a, tree_b)

print(f"\n最終的な比較コスト: {final_cost}")