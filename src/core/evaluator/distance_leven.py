import sys
import os

# パス解決
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

def calculate_levenshtein(str1: str, str2: str) -> int:
    """
    純粋な文字列（トークン）ベースのレーベンシュタイン距離を計算する。
    パース（AST変換）に失敗した致命的な数式に対する「最終防衛線」として機能する。
    """
    # Noneが来た場合の安全対策
    if str1 is None: str1 = ""
    if str2 is None: str2 = ""
    
    # 比較のために空白を詰める（最低限の正規化）
    s1 = str(str1).replace(" ", "")
    s2 = str(str2).replace(" ", "")

    n, m = len(s1), len(s2)
    if n == 0: return m
    if m == 0: return n

    # 動的計画法（DP）による距離計算
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # 削除
                dp[i][j - 1] + 1,      # 挿入
                dp[i - 1][j - 1] + cost # 置換
            )

    return dp[n][m]