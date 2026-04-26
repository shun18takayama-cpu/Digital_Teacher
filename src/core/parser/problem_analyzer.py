# 🐍 src/modules/problem_analyzer.py (v5.0)

import csv
from sympy import symbols, parse_expr, Mul, sin, cos, exp, Pow, log, Add, Symbol, Integer, tan, srepr, sqrt, Basic
from sympy.parsing.sympy_parser import (
    standard_transformations, implicit_multiplication_application,
    parse_expr
)

# -----------------------------------------------------------------------------
# ★ config.py からルール定義をインポート
# -----------------------------------------------------------------------------
import src.config as config

# -----------------------------------------------------------------------------
# STEP 1: 数式分析の関数（analyze_recursive）
# -----------------------------------------------------------------------------
def analyze_recursive(expr, rules):
    """
    ASTを再帰的に探索し、微分のルールを判定する関数。
    【v2.0】TypeError を防ぐチェックを追加。
    【v3.0】ルール名を config.py から参照するように変更。
    【v4.0】一般指数関数 (a^x) の判定ロジックを追加。
    【v5.0】商の微分判定を強化 (Mulクラス内の負の指数を持つ項を検知)。
    """
    x = symbols('x')
    
    if not isinstance(expr, Basic):
        return

    # --- Powクラスの判定（対数微分、一般指数、商、べき乗、累乗根） ---
    if isinstance(expr, Pow):
        base, exponent = expr.args
        
        # 属性チェック用のフラグ
        base_has_x = hasattr(base, 'has') and base.has(x)
        exp_has_x = hasattr(exponent, 'has') and exponent.has(x)
        base_is_number = hasattr(base, 'is_Number') and base.is_Number
        exp_is_number = getattr(exponent, 'is_Number', False)
        exp_is_integer = getattr(exponent, 'is_Integer', False)
        exp_is_negative = getattr(exponent, 'is_negative', False)

        # 1. 対数微分法: 底も指数も x を含む (x^x)
        if base_has_x and exp_has_x:
            rules.add(config.RULE_LOGARITHMIC)

        # 2. 一般指数関数の微分: 底が定数、指数が x を含む (2^x)
        elif base_is_number and exp_has_x:
            rules.add(config.RULE_GENERAL_EXP)

        # 3. 商の微分（単項の場合）: 1/x -> x^-1
        elif base_has_x and exp_is_number and exp_is_negative:
            rules.add(config.RULE_QUOTIENT)
            # ※ x^-1 は「べき乗」でも解けるが、定義上「商」構造も持つため追加。
            # さらに「べき乗」判定へ進むため、ここではelifで止めないケースもありうるが、
            # 優先順位として一旦ここで判定。

        # 4. べき乗微分と累乗根: 底が x を含み、指数が定数
        elif base_has_x and exp_is_number:
            if exp_is_integer:
                if base == x: 
                    rules.add(config.RULE_POWER) # x^2
                # (底が x 以外なら合成関数へ)
            else: 
                # 指数が整数でない (x^(1/2)) -> 累乗根
                rules.add(config.RULE_ROOT) 

    # --- 積の微分 および 商の微分（Mul内） ---
    if isinstance(expr, Mul):
        numerator_parts = []
        has_quotient_structure = False # ★ v5.0 追加: 商の構造フラグ

        for arg in expr.args:
             # 指数が負の数かどうか判定（＝分母に来る項か？）
             is_negative_power = isinstance(arg, Pow) and \
                                 len(arg.args) > 1 and \
                                 getattr(arg.args[1], 'is_Number', False) and \
                                 arg.args[1].is_negative
             
             if is_negative_power:
                 # ★ v5.0 追加: 負の指数の項が x を含んでいれば「商の微分」
                 if hasattr(arg, 'has') and arg.has(x):
                     rules.add(config.RULE_QUOTIENT)
                     has_quotient_structure = True
             else:
                 # 負の指数でなければ、積の微分のカウント対象（分子）
                 numerator_parts.append(arg)
        
        # 積の微分判定: 分子となる項の中で、xを含むものが2つ以上あるか
        if sum(1 for part in numerator_parts if hasattr(part, 'has') and part.has(x)) >= 2:
            rules.add(config.RULE_PRODUCT)

    # --- 商の微分 (Pow判定は上で統合済みだが、Mul内判定は上記で行った) ---
    # (v5.0でロジックを整理したため、個別の商判定ブロックは不要となり削除)

    # --- 基本的な関数の微分 ---
    if hasattr(expr, 'func'):
        func = expr.func
        if func in [sin, cos, tan]: 
            rules.add(config.RULE_TRIG)
        if func is exp: 
            rules.add(config.RULE_EXP) # e^x
            if len(expr.args) > 0:
                arg = expr.args[0]
                if isinstance(arg, Basic) and hasattr(arg, 'has') and arg.has(x) and \
                   not isinstance(arg, Symbol): 
                    rules.add(config.RULE_CHAIN)
        if func is log: 
            rules.add(config.RULE_LOG)

    # --- 合成関数の微分 ---
    if hasattr(expr, 'func') and hasattr(expr, 'args') and \
       expr.func in [sin, cos, tan, log, Pow, sqrt]: # (expは上で処理済み)
        
        # 単純な x^n を除く (これは「べき乗微分」で処理済み)
        is_simple_power = isinstance(expr, Pow) and len(expr.args) > 0 and \
                          expr.args[0] == x and \
                          getattr(expr.args[1], 'is_Integer', False)

        if not is_simple_power:
            for arg in expr.args:
                if isinstance(arg, Basic) and hasattr(arg, 'has') and arg.has(x) and \
                   not isinstance(arg, Symbol): 
                    rules.add(config.RULE_CHAIN)
        # ★ v6.0 追加: 指数が -1 の Pow (つまり分数 1/g(x)) は、合成関数判定から除外する
        is_reciprocal = isinstance(expr, Pow) and \
                        len(expr.args) > 1 and \
                        getattr(expr.args[1], 'is_Integer', False) and \
                        expr.args[1] == -1

        # 条件に `not is_reciprocal` を追加
        if not is_simple_power and not is_reciprocal:
            for arg in expr.args:
                if isinstance(arg, Basic) and hasattr(arg, 'has') and arg.has(x) and \
                   not isinstance(arg, Symbol): # 中身が x そのものではない
                    rules.add(config.RULE_CHAIN)
                    break
    
    

    # --- 再帰ステップ ---
    if hasattr(expr, 'args'):
        for arg in expr.args:
            if isinstance(arg, Basic):
                 analyze_recursive(arg, rules)

def analyze_expression(expr_str):
    """
    数式の文字列を受け取り、分析して「ルールのリスト」と「ASTの文字列」を返す。
    （主に問題マスターのタグ付けや、人間の確認用）
    """
    x = symbols('x')
    local_functions = {"sin": sin, "cos": cos, "tan": tan, "exp": exp, "log": log, "ln": log, "sqrt": sqrt}
    
    # === 前処理ステップ ===
    try:
        if not isinstance(expr_str, str):
             raise TypeError("Input must be a string")
        
        processed_str = expr_str.strip()
        processed_str = processed_str.replace('^', '**')
        processed_str = processed_str.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

        transformations = (standard_transformations + (implicit_multiplication_application,))
        
        parsed_expression = parse_expr(processed_str, 
                                       local_dict=local_functions, 
                                       transformations=transformations)
                                       
    except Exception as parse_error:
        return ["パースエラー"], f"Error during parsing: {type(parse_error).__name__}"
    # === 前処理ここまで ===

    ast_representation = srepr(parsed_expression)
    
    # === ルール分析 ===
    detected_rules = set()
    try:
        if parsed_expression is not None:
            analyze_recursive(parsed_expression, detected_rules)
        else:
             raise ValueError("Parsed expression is None")
    except Exception as analysis_error:
       return ["分析エラー"], f"Error during analysis: {type(analysis_error).__name__}"

    return list(detected_rules), ast_representation


# =============================================================================
# STEP 2: 展開エンジン用パーサー（★今回追加する新機能）
# =============================================================================
def safe_parse(expr_str):
    """
    文字列を安全な前処理に通し、SymPyの「操作可能なオブジェクト(AST)」として返す。
    自動計算を防ぐため evaluate=False を適用する。
    生徒の未熟な式変形（x*xなど）をそのままの構造で維持するための必須関数。
    """
    x = symbols('x')
    local_functions = {"sin": sin, "cos": cos, "tan": tan, "exp": exp, "log": log, "ln": log, "sqrt": sqrt}
    
    try:
        if not isinstance(expr_str, str):
             raise TypeError("Input must be a string")
        
        # 既存コードと同じ、実績のある強固な前処理
        processed_str = expr_str.strip()
        processed_str = processed_str.replace('^', '**')
        processed_str = processed_str.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))

        transformations = (standard_transformations + (implicit_multiplication_application,))
        
        # ★ evaluate=False を指定してパース（勝手に計算させない！）
        parsed_expression = parse_expr(
            processed_str, 
            local_dict=local_functions, 
            transformations=transformations, 
            evaluate=False  
        )
        
        # 文字列ではなく、SymPyオブジェクトそのものを返す
        return parsed_expression

    except Exception as e:
        print(f"[safe_parse Error] 文字列のパースに失敗しました: '{expr_str}' -> {type(e).__name__}: {e}")
        return None