from sympy import Symbol
from test_matcher import build_educational_tree, print_visual_tree

if __name__ == "__main__":
    x = Symbol('x')
    
    # ラスボス級のテスト問題リスト
    test_problems = [
        # 1. 基本的な合成関数
        {"name": "合成関数の基本", "expr": "Derivative(exp(x**2), x)"},
        
        # 2. 商の微分
        {"name": "商の微分の基本", "expr": "Derivative(sin(x) / cos(x), x)"},
        
        # 3. 積と合成の複合（計算爆発チェック）
        {"name": "積 ＋ 合成関数の複合", "expr": "Derivative(exp(x) * sin(x**2), x)"},
        
        # 4. 前回のHW03-01の式（後退テスト）
        {"name": "HW03-01 (積の微分)", "expr": "Derivative(exp(x)*log(x), x)"}
    ]

    print("🚀 Digital Teacher - 次世代エンジン ストレステスト開始\n")

    for i, prob in enumerate(test_problems):
        print(f"==================================================")
        print(f"📝 テスト {i+1}: {prob['name']}")
        print(f"   問題式 : {prob['expr']}")
        print(f"==================================================")
        
        try:
            # ツリーの自動生成（クラッシュしないか、無限ループしないかテスト）
            milestones = build_educational_tree(prob['expr'], x)
            print(f"✅ 成功! {len(milestones)} 個の状態（ノード）を生成しました。")
            
            # ツリー構造の表示
            print_visual_tree(milestones)
            
        except Exception as e:
            print(f"❌ エラー発生: {e}")