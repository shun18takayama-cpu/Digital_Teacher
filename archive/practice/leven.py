len_s = len("kitten")  # 6
len_t = len("sitting") # 7

# 問: 最終的に dp[len_s][len_t] で答えを取り出せるように、
# 全て 0 で埋まった 2次元配列 dp を作成してください。


def edit_distance(s:str, t:str):
    len_s = len(s)
    len_t = len(t)


#１.表の作成: dp = [[0] * (len_t + 1) for _ in range(len_s + 1)]
    dp = [[0] * (len_t + 1) for _ in range(len_s + 1)]
    for i in range(len_s + 1):
        dp[i][0] = i

    for j in range(len_t + 1):
        dp[0][j] = j

#２.表の埋め方: 

    for i in range(1,len_s + 1):
        for j in range(1,len_t + 1):

            #2.1 挿入
            temp_insert = dp[i][j-1] + 1
            #2.2 削除
            temp_delete = dp[i-1][j] + 1
            #2.3 置換
            if s[i-1] == t[j-1]:
                temp_replace = dp[i-1][j-1]
            else:
                temp_replace = dp[i-1][j-1] + 1
            #2.4 最小値を選択
            dp[i][j] = min(temp_insert, temp_delete, temp_replace)
    
    for row in dp:
        print(row)
    
    return dp[len_s][len_t]


print(edit_distance("kitten", "sitting"))