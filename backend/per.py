"""Phoneme Error Rate (PER) with alignment.

Reference and hypothesis are lists of IPA phoneme tokens.
PER = (S + D + I) / N, with N = number of reference phonemes.
Pure Python, no dependencies. Run `python per.py` for the self test.
"""
from __future__ import annotations


def align(ref: list[str], hyp: list[str]) -> list[tuple[str, str | None, str | None]]:
    """Levenshtein alignment. Returns ops: ('ok'|'sub'|'del'|'ins', ref_ph, hyp_ph)."""
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + cost, dp[i - 1][j] + 1, dp[i][j - 1] + 1)
    ops: list[tuple[str, str | None, str | None]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            ops.append(("ok" if ref[i - 1] == hyp[j - 1] else "sub", ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            ops.append(("del", ref[i - 1], None))
            i -= 1
        else:
            ops.append(("ins", None, hyp[j - 1]))
            j -= 1
    ops.reverse()
    return ops


def per(ref: list[str], hyp: list[str]) -> dict:
    ops = align(ref, hyp)
    s = sum(1 for o in ops if o[0] == "sub")
    d = sum(1 for o in ops if o[0] == "del")
    i = sum(1 for o in ops if o[0] == "ins")
    n = len(ref)
    value = (s + d + i) / n if n else (0.0 if not hyp else float(len(hyp)))
    errors = [{"op": o, "ref": r, "heard": h} for o, r, h in ops if o != "ok"]
    return {"per": value, "S": s, "D": d, "I": i, "N": n, "errors": errors}


def _selftest() -> None:
    assert per(["a", "b"], ["a", "b"])["per"] == 0.0
    r = per(["θ", "ɪ", "ŋ", "k"], ["t", "ɪ", "ŋ", "k"])
    assert (r["S"], r["D"], r["I"], r["N"]) == (1, 0, 0, 4)
    assert abs(r["per"] - 0.25) < 1e-9
    assert r["errors"][0] == {"op": "sub", "ref": "θ", "heard": "t"}
    r = per(["a", "b", "c"], ["a", "c"])
    assert (r["S"], r["D"], r["I"]) == (0, 1, 0)
    r = per(["a"], ["a", "x"])
    assert (r["S"], r["D"], r["I"]) == (0, 0, 1)
    r = per(["a", "b"], [])
    assert r["D"] == 2 and r["per"] == 1.0
    print("per.py selftest OK")


if __name__ == "__main__":
    _selftest()
