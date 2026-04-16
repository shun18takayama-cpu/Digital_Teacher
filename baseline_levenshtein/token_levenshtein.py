"""
式文字列 → SymPy でパース → 比較

A) srepr を「塊」トークンに切ってレーベンシュタイン（線形シーケンス）
B) SymPy 式を有順序木とみなし、子の森に対する DP で距離（木ベース）

B の距離では「第1項の Mul に因数 x が1つ増えた」が
部分木1個の挿入として数えやすく、トークン列より直感に近いことが多い。
"""

from __future__ import annotations

import functools
import re
from typing import Dict, List, Tuple

from sympy import Basic, E, cos, exp, log, sin, srepr
from sympy.abc import x
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# ---------- 入力正規化・パース ----------

DEFAULT_TOKEN_SYNONYMS: Dict[str, str] = {}

_SREPR_TOKEN = re.compile(r"'[^']*'|[A-Za-z_][A-Za-z0-9_]*|\d+|[(),]")


def normalize_input(s: str) -> str:
    s = s.strip()
    s = s.replace("^", "**")
    s = s.replace("*+", "+")
    s = s.replace("* +", "+")
    s = re.sub(r"\bsinx\b", "sin(x)", s, flags=re.IGNORECASE)
    s = re.sub(r"\bcosx\b", "cos(x)", s, flags=re.IGNORECASE)
    s = s.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
    return s


def to_sympy(expr_str: str) -> Basic:
    processed = normalize_input(expr_str)
    local_dict = {
        "x": x,
        "E": E,
        "e": E,
        "exp": exp,
        "sin": sin,
        "cos": cos,
        "log": log,
        "ln": log,
    }
    t = standard_transformations + (implicit_multiplication_application,)
    return parse_expr(processed, local_dict=local_dict, transformations=t)


def ast_repr(expr) -> str:
    return srepr(expr)


# ---------- A) srepr トークン + レーベンシュタイン ----------


def tokenize_srepr(srepr_str: str, synonyms: Dict[str, str] | None = None) -> List[str]:
    if synonyms is None:
        synonyms = DEFAULT_TOKEN_SYNONYMS
    out: List[str] = []
    for m in _SREPR_TOKEN.finditer(srepr_str):
        t = m.group(0)
        out.append(synonyms.get(t, t))
    return out


def levenshtein_tokens(a: List[str], b: List[str]) -> tuple[int, list[list[int]]]:
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + c,
            )
    return dp[n][m], dp


# ---------- B) 有順序木スライド（根ラベル + 子の森の DP） ----------


def _root_label(n: Basic) -> Tuple[str, str]:
    """ノードのラベル（型 + その式の見た目）。葉も内部ノードも一意に比較できるようにする。"""
    fn = getattr(n.func, "__name__", type(n).__name__)
    return (type(n).__name__, fn)


@functools.lru_cache(maxsize=None)
def tree_edit_distance(a: Basic, b: Basic) -> int:
    """
    有順序木としての編集距離（実装は一般的な再帰 + 森DPの近似）。

    - 根のラベル（SymPy のクラス + func 名）が一致しない: まずコスト 1（置換扱い）
    - 子は左から順のリストとして、挿入・削除・対応づけにコスト 1、対応した子同士は再帰的に距離

    部分木ごとの「挿入・削除」を 1 としているので、
    Mul に因数 x が1つ増えるケースは距離が小さくなりやすい。
    """
    if a == b:
        return 0
    la, lb = _root_label(a), _root_label(b)
    root_cost = 0 if la == lb else 1

    ca, cb = a.args, b.args
    # 葉同士（args なし）はラベルだけで決める
    if len(ca) == 0 and len(cb) == 0:
        return root_cost if not a.equals(b) else 0

    # 片方だけ葉: もう片方の子リストを「森」として整列
    if len(ca) == 0:
        return root_cost + forest_edit_distance((), cb)
    if len(cb) == 0:
        return root_cost + forest_edit_distance(ca, ())

    return root_cost + forest_edit_distance(ca, cb)


@functools.lru_cache(maxsize=None)
def forest_edit_distance(
    children_a: Tuple[Basic, ...],
    children_b: Tuple[Basic, ...],
) -> int:
    """有順序の子リスト同士の編集距離（レーベンシュタインだがコストが部分木距離）。"""
    A, B = children_a, children_b
    n, m = len(A), len(B)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + 1  # 部分木1本削除
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + 1  # 部分木1本挿入
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + tree_edit_distance(A[i - 1], B[j - 1]),
            )
    return dp[n][m]


def compare_expressions(
    s1: str,
    s2: str,
    synonyms: Dict[str, str] | None = None,
) -> dict:
    e1 = to_sympy(s1)
    e2 = to_sympy(s2)
    r1 = ast_repr(e1)
    r2 = ast_repr(e2)
    toks1 = tokenize_srepr(r1, synonyms)
    toks2 = tokenize_srepr(r2, synonyms)
    d_tok, _ = levenshtein_tokens(toks1, toks2)
    d_tree = tree_edit_distance(e1, e2)
    return {
        "expr1": s1,
        "expr2": s2,
        "sympy1": str(e1),
        "sympy2": str(e2),
        "srepr1": r1,
        "srepr2": r2,
        "tokens1": toks1,
        "tokens2": toks2,
        "levenshtein_on_tokens": d_tok,
        "tree_edit_distance": d_tree,
    }


if __name__ == "__main__":
    user_a = "e^x*sinx*+ e^x*cosx"
    user_b = "x*e^x*sinx*+ e^x*cosx"

    for name, a, b in [
        ("ユーザー例（貼付どおり）", user_a, user_b),
        ("同じ式を括弧ありで書いた場合", "e^x*sin(x) + e^x*cos(x)", "x*e^x*sin(x) + e^x*cos(x)"),
    ]:
        print("==", name, "==")
        r = compare_expressions(a, b)
        print("式1:", r["expr1"])
        print("式2:", r["expr2"])
        print("SymPy:", r["sympy1"], "|", r["sympy2"])
        print("トークン距離(A):", r["levenshtein_on_tokens"])
        print("木距離(B):", r["tree_edit_distance"])
