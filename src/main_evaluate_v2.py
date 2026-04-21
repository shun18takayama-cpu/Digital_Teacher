import re
from typing import Tuple, List
from sympy import Basic, E, cos, exp, log, sin, srepr, Derivative
from sympy.abc import x
from sympy.parsing.sympy_parser import implicit_multiplication_application, parse_expr, standard_transformations

class RawDataProcessor:
    """
    学生の生データを正規化し、コメントを分離し、evaluate=False で純粋なAST文字列を生成する前処理クラス。
    木距離の計算は行わない。
    """
    def __init__(self):
        self.local_dict = {
            "x": x, "E": E, "e": E, "exp": exp, 
            "sin": sin, "cos": cos, "log": log, "ln": log,
            "Derivative": Derivative
        }
        self.transformations = standard_transformations + (implicit_multiplication_application,)

    def extract_comment(self, s: str) -> Tuple[str, str]:
        """数式から /* ... */ のコメントを抽出し、数式とコメントに分離する"""
        comment = ""
        # /* から */ までの最短マッチを検索
        match = re.search(r'(/\*.*?\*/)', s)
        if match:
            comment = match.group(1)
            # 数式からはコメント部分を削除
            s = s.replace(comment, "").strip()
        return s, comment

    def normalize_input(self, s: str) -> Tuple[str, List[str], str]:
        """
        文字列の正規化と前処理
        Returns: (正規化後の式, ログのリスト, 抽出したコメント)
        """
        logs = []
        s = str(s).strip()
        
        # ① コメントアウトの分離
        s, comment = self.extract_comment(s)

        # ② 全角記号を半角に変換
        half_s = s.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
        if s != half_s:
            logs.append("全角記号の半角化")
            s = half_s

        # ※方程式（=）の除去は廃止（ありのままをパースさせるため）

        # ③ 演算子の置換とタイポ修正
        replacements = {"^": "**", "*+": "+", "* +": "+"}
        for old, new in replacements.items():
            if old in s:
                s = s.replace(old, new)
                logs.append(f"演算子の置換: '{old}' -> '{new}'")

        # ④ 関数と変数の「くっつき事故」の防止
        for func in ["sin", "cos", "tan", "log", "ln"]:
            pattern = rf"\b{func}x\b"
            if re.search(pattern, s, flags=re.IGNORECASE):
                s = re.sub(pattern, f"{func}(x)", s, flags=re.IGNORECASE)
                logs.append(f"関数括弧の補完: {func}x -> {func}(x)")

        # ⑤ 微分記号の未評価クラス(Derivative)への統一
        if "diff(" in s:
            s_new = s.replace("diff(", "Derivative(")
            if s != s_new:
                logs.append("微分関数の未評価化: 'diff' -> 'Derivative'")
                s = s_new
        
        ddx_pattern = r"d/dx\(([^)]+)\)"
        if re.search(ddx_pattern, s):
            s = re.sub(ddx_pattern, r"Derivative(\1, x)", s)
            logs.append("微分表記の正規化: 'd/dx(A)' -> 'Derivative(A, x)'")
            
        # 連続するセミコロンなどのゴミ掃除
        s = s.replace(";", "").strip()

        return s, logs, comment

    def process_raw_data(self, raw_expr: str) -> dict:
        """生の入力を受け取り、前処理結果とAST文字列を返す"""
        norm_expr, norm_logs, comment = self.normalize_input(raw_expr)
        
        result = {
            "student_expr": str(raw_expr),
            "normalized_expr": norm_expr,
            "student_comment": comment,
            "normalization_logs": norm_logs,
            "student_ast": ""
        }
        
        if not norm_expr:
            return result

        try:
            # evaluate=False でパース
            expr = parse_expr(norm_expr, local_dict=self.local_dict, transformations=self.transformations, evaluate=False)
            result["student_ast"] = srepr(expr)
        except Exception as e:
            # 目標データ通り、エラー文字列をそのまま保存する
            result["student_ast"] = f"ParseError: {type(e).__name__}: {str(e)}"
            
        return result