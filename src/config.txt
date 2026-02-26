# 🐍 src/config.py (新規作成)

# --- 微分ルールの定義 ---
# (ルール名を変更したい場合は、ここの文字列だけを修正すればOK)

RULE_LOGARITHMIC = "対数微分法"
RULE_PRODUCT = "積の微分"
RULE_QUOTIENT = "商の微分"
RULE_TRIG = "三角関数の微分"
RULE_EXP = "expの微分" # ← これは e^x 用
RULE_GENERAL_EXP = "一般指数関数の微分" # ★追加 (a^x 用)
RULE_LOG = "対数関数の微分"
RULE_POWER = "べき乗微分 (x^n)"
# RULE_ROOT = "ルートの微分" # ← 古い名前はコメントアウト
RULE_ROOT = "累乗根の微分"   # ← ★ 新しい名前に変更 ★
RULE_CHAIN = "合成関数の微分"

# --- 全ルール名のリスト (Googleフォームの選択肢などに使う) ---
ALL_RULE_NAMES = [
    RULE_LOGARITHMIC,
    RULE_PRODUCT,
    RULE_QUOTIENT,
    RULE_TRIG,
    RULE_EXP,# 
    RULE_GENERAL_EXP, # ★追加
    RULE_LOG,
    RULE_POWER,
    RULE_ROOT, # ★ 自動的に新しい名前が使われる ★
    RULE_CHAIN,
]

# --- 主要ルール判定のための優先順位リスト (必要であれば) ---
RULE_PRIORITY = [
    RULE_LOGARITHMIC,
    RULE_QUOTIENT,
    RULE_PRODUCT,
    RULE_CHAIN,
    # ... (他のルール) ...
    RULE_ROOT, # ★ 自動的に新しい名前が使われる ★
    RULE_POWER,
]

# --- (今後、エラーメッセージなどもここで定義すると便利) ---
# ERROR_MSG_TYPE_MISMATCH = "型が一致しません..."