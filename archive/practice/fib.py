def fibonacci(n):
    fib_list = [0]*(n+1)

    if n <= 1:
        return 1
    
    fib_list[0] = 1
    fib_list[1] = 1
    for i in range(2,n+1):
        fib_list[i] = fib_list[i-1] + fib_list[i-2]
        
    return fib_list[n]

print(fibonacci(5))
