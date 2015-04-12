def sqs(n, s):
    if n == 0:
        return s
    sqs(n-1, s+n**2)
