import pandas as pd
import os

# -----------------------------------------------------------------------------
# 1. あなたの設計図に基づく問題リストの定義
# -----------------------------------------------------------------------------

# カテゴリA: 1ルールのみ (20問)
cat_A = {
    "A-001": "x**7",
    "A-002": "4*x**3",
    "A-003": "x**-5",
    "A-004": "x**(1/3)",
    "A-005": "sqrt(x)",
    "A-006": "5*x**(2/3)",
    "A-007": "sin(x)",
    "A-008": "3*cos(x)",
    "A-009": "tan(x)",
    "A-010": "exp(x)",
    "A-011": "6*exp(x)",
    "A-012": "log(x)",
    "A-013": "2*log(x)",
    "A-014": "1/x",
    "A-015": "1/(x**3)",
    "A-016": "5/x**2",
    "A-017": "x",
    "A-018": "5*x",
    "A-019": "4",
    "A-020": "3*x**-4",
}

# カテゴリB: 2ルール (積/商 + 基本) (20問)
cat_B = {
    "B-001": "x*sin(x)",
    "B-002": "x**2*cos(x)",
    "B-003": "exp(x)*sin(x)",
    "B-004": "x**3*log(x)",
    "B-005": "log(x)*cos(x)",
    "B-006": "exp(x)*log(x)",
    "B-007": "x**4*exp(x)",
    "B-008": "sin(x)*tan(x)",
    "B-009": "x*sqrt(x)",
    "B-010": "x**2 * (x**3 + 1)",
    "B-011": "sin(x)/x",
    "B-012": "x**2/cos(x)",
    "B-013": "exp(x)/sin(x)",
    "B-014": "log(x)/x**3",
    "B-015": "x/log(x)",
    "B-016": "tan(x)/exp(x)",
    "B-017": "x**2 / (x+1)",
    "B-018": "(x+1) / (x-1)",
    "B-019": "sqrt(x) / sin(x)",
    "B-020": "x**3 / (x**2 - 1)",
}

# カテゴリC: 2ルール (合成関数 + 基本) (20問)
cat_C = {
    "C-001": "sin(x**2)",
    "C-002": "cos(3*x + 1)",
    "C-003": "tan(x**3)",
    "C-004": "sin(exp(x))",
    "C-005": "cos(log(x))",
    "C-006": "exp(x**3)",
    "C-007": "exp(-x)",
    "C-008": "exp(sin(x))",
    "C-009": "log(x**2 + 1)",
    "C-010": "log(cos(x))",
    "C-011": "(x**2 + 3*x + 1)**5",
    "C-012": "sqrt(x**2 + 1)",
    "C-013": "(x+5)**-3",
    "C-014": "1/(x**2 + 1)",
    "C-015": "exp(1/x)",
    "C-016": "sin(sqrt(x))",
    "C-017": "log(x**-2)",
    "C-018": "tan(5*x)",
    "C-019": "(sin(x))**3",
    "C-020": "(log(x))**4",
}

# カテゴリD: 3ルール以上 (複雑な組み合わせ) (15問)
cat_D = {
    "D-001": "x*sin(x**2)",
    "D-002": "x**2*exp(3*x)",
    "D-003": "exp(x)*cos(x**2)",
    "D-004": "log(x)*sin(2*x)",
    "D-005": "sin(x**2)/x**3",
    "D-006": "exp(x**2)/(x+1)",
    "D-007": "log(x**2)/cos(x)",
    "D-008": "sin(x**2)*cos(x**3)",
    "D-009": "exp(x+1)*log(x**2)",
    "D-010": "sin(cos(x**2))",
    "D-011": "exp(sin(log(x)))",
    "D-012": "sqrt(exp(x**2) + 1)",
    "D-013": "x*sin(x)/exp(x)",
    "D-014": "x**x",
    "D-015": "(sin(x))**x",
}

# -----------------------------------------------------------------------------
# 2. 辞書を結合し、DataFrameに変換
# -----------------------------------------------------------------------------

# 全カテゴリの辞書を結合
all_problems = {}
all_problems.update(cat_A)
all_problems.update(cat_B)
all_problems.update(cat_C)
all_problems.update(cat_D)

# 辞書からDataFrameを作成
# ご要望通り、列は 'problem_id' と 'problem_formula' のみ
df = pd.DataFrame(all_problems.items(), columns=['problem_id', 'problem_formula'])

# -----------------------------------------------------------------------------
# 3. CSVファイルとして出力
# -----------------------------------------------------------------------------
output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "test_problems_generated_75.csv")

df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"合計 {len(df)} 件の問題を生成し、'{output_path}' に保存しました。")
print("CSVファイルには 'problem_id' と 'problem_formula' のみが含まれています。")