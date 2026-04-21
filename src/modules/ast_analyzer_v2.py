import functools
import re
from typing import Dict, List, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment

# 【変更点】Derivative をインポートに追加
from sympy import Basic, E, cos, exp, log, sin, srepr, simplify, Derivative
from sympy.abc import x
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

class ASTAnalyzer:
    """
    数式のパース、AST化、および各種距離（レーベンシュタイン、ハンガリアンTED）の計算を一手に担うコアモジュール。
    【V2 仕様】
    - evaluate=False により SymPy の自動計算（flatten等）を無効化し、生の構造を保持する。
    - 正規化処理の履歴（ログ）を追跡可能にする。
    - 微分表記（diff, d/dx）を未評価クラス（Derivative）に変換し、プロセス評価を可能にする。
    """
    def __init__(self):
        self.synonyms: Dict[str, str] = {}
        # sreprの出力からトークンを抽出するための正規表現
        self.token_regex = re.compile(r"'[^']*'|[A-Za-z_][A-Za-z0-9_]*|\d+|[(),]")
        
        # 【変更点】SymPyでパースする際のローカル変数・関数の定義に Derivative を追加
        self.local_dict = {
            "x": x, "E": E, "e": E, "exp": exp, 
            "sin": sin, "cos": cos, "log": log, "ln": log,
            "Derivative": Derivative
        }
        # 暗黙の掛け算（例: 2x -> 2*x）を解釈するための変換ルール
        self.transformations = standard_transformations + (implicit_multiplication_application,)

    def normalize_input(self, s: str) -> Tuple[str, List[str]]:
        """
        文字列の正規化と前処理（タイポや方程式の除去）
        【変更点】文字列だけでなく、何を変更したかの履歴（ログリスト）を一緒に返す
        """
        logs = []
        original_s = str(s).strip()
        s = original_s

        # ① 全角記号を半角に変換
        half_s = s.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
        if s != half_s:
            logs.append("全角記号の半角化")
            s = half_s

        # ② 方程式の場合、右辺だけを抽出
        if "=" in s:
            s_new = s.split("=")[-1].strip()
            logs.append(f"方程式の除去: '{s}' -> '{s_new}'")
            s = s_new

        # ③ 演算子の置換とタイポ修正
        replacements = {"^": "**", "*+": "+", "* +": "+"}
        for old, new in replacements.items():
            if old in s:
                s = s.replace(old, new)
                logs.append(f"演算子の置換: '{old}' -> '{new}'")

        # ④ 関数と変数の「くっつき事故」の防止（対象を拡張）
        for func in ["sin", "cos", "tan", "log", "ln"]:
            pattern = rf"\b{func}x\b"
            if re.search(pattern, s, flags=re.IGNORECASE):
                s = re.sub(pattern, f"{func}(x)", s, flags=re.IGNORECASE)
                logs.append(f"関数括弧の補完: {func}x -> {func}(x)")

        # ⑤ 微分記号の「未評価クラス(Derivative)」への統一
        # パターンA: diff(A, x) -> Derivative(A, x)
        if "diff(" in s:
            s_new = s.replace("diff(", "Derivative(")
            if s != s_new:
                logs.append("微分関数の未評価化: 'diff' -> 'Derivative'")
                s = s_new
        
        # パターンB: d/dx(A) -> Derivative(A, x)
        ddx_pattern = r"d/dx\(([^)]+)\)"
        if re.search(ddx_pattern, s):
            s = re.sub(ddx_pattern, r"Derivative(\1, x)", s)
            logs.append("微分表記の正規化: 'd/dx(A)' -> 'Derivative(A, x)'")

        return s, logs

    def to_sympy(self, expr_str: str) -> Basic:
        """
        文字列をSymPyのAST（Basicオブジェクト）に変換
        【変更点】normalize_inputの返り値変更に対応 ＆ evaluate=False を追加
        """
        processed, _ = self.normalize_input(expr_str)
        return parse_expr(processed, local_dict=self.local_dict, transformations=self.transformations, evaluate=False)

    def ast_repr(self, expr: Basic) -> str:
        """ASTを文字列表現（srepr形式）に変換"""
        return srepr(expr)

    def tokenize_srepr(self, srepr_str: str) -> List[str]:
        """srepr文字列をトークンのリストに分割（レーベンシュタイン距離計算用）"""
        out: List[str] = []
        for m in self.token_regex.finditer(srepr_str):
            t = m.group(0)
            out.append(self.synonyms.get(t, t))
        return out

    def levenshtein_distance(self, a: List[str], b: List[str]) -> int:
        """トークンリスト間のレーベンシュタイン距離（編集距離）を動的計画法で計算"""
        n, m = len(a), len(b)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1): dp[i][0] = i
        for j in range(1, m + 1): dp[0][j] = j
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                c = 0 if a[i - 1] == b[j - 1] else 1
                dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + c)
        return dp[n][m]

    def _root_label(self, n: Basic) -> Tuple[str, str]:
        """TED計算用：ノードのラベル（クラス名と関数名）を抽出"""
        fn = getattr(n.func, "__name__", type(n).__name__)
        return (type(n).__name__, fn)

    @functools.lru_cache(maxsize=None)
    def tree_edit_distance(self, a: Basic, b: Basic) -> int:
        """【非順序木モード】ハンガリアン法を用いたTED"""
        if a == b: return 0
        la, lb = self._root_label(a), self._root_label(b)
        root_cost = 0 if la == lb else 1
        
        ca, cb = a.args, b.args
        if len(ca) == 0 and len(cb) == 0:
            return root_cost if not a.equals(b) else 0
            
        # どちらかに子供がいない場合は、従来の計算（一括削除/挿入）にフォールバック
        if len(ca) == 0 or len(cb) == 0:
            return root_cost + self.forest_edit_distance(ca, cb)
        
        # 両方に子供がいる場合、ハンガリアンマッチングを発動！
        return root_cost + self.hungarian_match_children(ca, cb)

    def hungarian_match_children(self, children_a: Tuple[Basic, ...], children_b: Tuple[Basic, ...]) -> int:
        """子ノードの集合を総当たりで比較し、最小コストの組み合わせを算出する"""
        n, m = len(children_a), len(children_b)
        
        # すべての子ノード同士の距離を計算して「コスト表（マトリックス）」を作る
        cost_matrix = np.zeros((n, m), dtype=int)
        for i in range(n):
            for j in range(m):
                # 再帰的に非順序木距離を計算（ここでお見合い相性チェック！）
                cost_matrix[i, j] = self.tree_edit_distance(children_a[i], children_b[j])
        
        # ハンガリアン法を実行して、最小コストになるペアを見つける
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # 選ばれたペアのコスト合計
        total_cost = cost_matrix[row_ind, col_ind].sum()
        
        # 子供の数が違う場合、ペアになれず余った子ノードの数だけペナルティ（削除/挿入）を追加
        unmatched_count = abs(n - m)
        total_cost += unmatched_count
        
        return int(total_cost)

    @functools.lru_cache(maxsize=None)
    def forest_edit_distance(self, children_a: Tuple[Basic, ...], children_b: Tuple[Basic, ...]) -> int:
        """子ノードのリスト（森）同士の編集距離を計算（フォールバック用）"""
        n, m = len(children_a), len(children_b)
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1): dp[i][0] = dp[i - 1][0] + 1
        for j in range(1, m + 1): dp[0][j] = dp[0][j - 1] + 1
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                dp[i][j] = min(
                    dp[i - 1][j] + 1,
                    dp[i][j - 1] + 1,
                    dp[i - 1][j - 1] + self.tree_edit_distance(children_a[i - 1], children_b[j - 1])
                )
        return dp[n][m]

    def process_expression(self, raw_expr: str) -> dict:
        """
        生の入力を受け取り、正規化・パース・トークン化・simplifyの全過程のデータを保持して返す。
        """
        result = {
            "raw_expr": str(raw_expr),
            "normalized_expr": "",
            "normalization_logs": [],  # 【追加】正規化のプロセスログ
            "sympy_expr": None,
            "simplified_expr": None,  # simplify用
            "ast_str": "",
            "tokens": [],
            "status": "Success"
        }
        
        # 【変更点】タプルで受け取り、ログも保持する
        norm_expr, norm_logs = self.normalize_input(raw_expr)
        result["normalized_expr"] = norm_expr
        result["normalization_logs"] = norm_logs
        
        try:
            # 【超重要変更点】 evaluate=False を追加 (V2の核となる機能)
            expr = parse_expr(norm_expr, local_dict=self.local_dict, transformations=self.transformations, evaluate=False)
            result["sympy_expr"] = expr
            
            # simplify（簡略化・展開など）されたAST
            result["simplified_expr"] = simplify(expr)
            
            ast_str = self.ast_repr(expr)
            result["ast_str"] = ast_str
            result["tokens"] = self.tokenize_srepr(ast_str)
            
        except Exception as e:
            result["status"] = "Error"
            result["ast_str"] = f"ParseError: {type(e).__name__}"
            
        return result