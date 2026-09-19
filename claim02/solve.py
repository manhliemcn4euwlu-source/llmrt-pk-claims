# Claim 2 re-derivation (from scratch, stdlib only).
# b(n) = # permutations p of {1..n} with p(i) != i for all i, and no decreasing
# subsequence of length 4 (avoids pattern 4321). Pass criterion minimum: b(1..12).
# Method: DP over (used-value mask, decreasing-pile tails b0,b1,b2) where b_i is
# the maximum tail value of a decreasing subsequence of length i+1 so far. The
# value is read in position order, so appending v at the next position: a length-4
# decreasing subsequence appears iff b2 > v (pruned); otherwise the new run length
# L is 1, 2 or 3 according as b0, b1 are <= v, and b[L-1] = max(b[L-1], v).
# Self-check inside the run (no external data): for n <= 9 the DP is cross-verified
# against an independent O(n^2)-per-step direct four-index scan of the same
# definition; both must agree before any b(n) is printed.
from collections import defaultdict

def count_dp(n):
    layers = [defaultdict(lambda: defaultdict(int)) for _ in range(n+1)]
    layers[0][0][(0,0,0)] = 1
    for k in range(n):
        pos = k + 1
        for mask, states in layers[k].items():
            for (b0,b1,b2), c in states.items():
                for v in range(1, n+1):
                    if mask >> (v-1) & 1: continue
                    if v == pos: continue          # derangement p(i) != i
                    if b2 > v: continue            # would form a 4-run
                    L = 1
                    if b0 > v: L = 2
                    if b1 > v: L = 3
                    nb0, nb1, nb2 = b0, b1, b2
                    if L == 1: nb0 = max(nb0, v)
                    elif L == 2: nb1 = max(nb1, v)
                    else: nb2 = max(nb2, v)
                    layers[k+1][mask | (1 << (v-1))][(nb0,nb1,nb2)] += c
    return sum(sum(s.values()) for s in layers[n].values())

def count_brute(n):
    # independent: direct scan of the definition, no piles. A pattern 4321 is
    # indices i < j < k < l with p[i] > p[j] > p[k] > p[l] (positions need not
    # be consecutive); when placing p[k] a new pattern can only end at k, so
    # check triples i < j < k (i.e. j2 < k-1 < k) in the prefix with p[i] >
    # p[j2] > p[k2] > p[k].
    p = [0]*n
    used = [False]*(n+1)
    total = 0
    def rec(k):
        nonlocal total
        if k == n:
            total += 1
            return
        for v in range(1, n+1):
            if used[v] or v == k+1: continue
            p[k] = v; used[v] = True
            ok = True
            for i in range(k-1):
                for j in range(i+1, k):
                    if p[i] > p[j]:
                        for m in range(j+1, k):
                            if p[j] > p[m] > p[k]:
                                ok = False
                                break
                            if not ok: break
                        if not ok: break
                if not ok: break
            if ok: rec(k+1)
            used[v] = False
    rec(0)
    return total

def main():
    import time
    t0 = time.time()
    for n in range(1, 10):
        a, b = count_dp(n), count_brute(n)
        assert a == b, 'self-check failed at n=%d: %d != %d' % (n, a, b)
    vals = [count_dp(n) for n in range(1, 13)]
    for n, b in enumerate(vals, 1):
        print('b(%d) = %d' % (n, b))
    print('b(1..12) = ' + ', '.join(map(str, vals)))
    print('self-check n<=9 dp==brute: OK, elapsed %.1f s' % (time.time()-t0))

if __name__ == '__main__':
    main()
