#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chit402 回执离线验证器(stdlib only): 公开回执 -> Merkle 包含 -> 签名树头 -> Base 锚定.

不复用 chit402-verify 代码, 只用公开材料与标准密码学原语, 便于任何人重跑。
用法:
  chit402_offline_verify.py <receipt-json-or-url> [--rpc URL]
退出码: 0=链上可核部分全部通过; 1=有检查失败; 2=输入不可用。
"""
import base64
import hashlib
import json
import sys
import urllib.request

UA = {"User-Agent": "llmrt-chit402-verify/1.0", "Accept": "application/json"}
RPC = "https://mainnet.base.org"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers=UA)
    with OPENER.open(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC, data=body, headers={**UA, "Content-Type": "application/json"})
    with OPENER.open(req, timeout=45) as r:
        return json.loads(r.read().decode()).get("result")


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sha(b):
    return hashlib.sha256(b).digest()


def node(left, right):
    return sha(b"\x01" + left + right)


def fold(leaf_hex, index, size, proof):
    """RFC 9162 折叠: 兄弟节点左右由 (index,size) 决定, 不读 position 标签。"""
    h, fn, sn = bytes.fromhex(leaf_hex), int(index), int(size) - 1
    for step in proof:
        sib = bytes.fromhex(step["hash"])
        sib_left = (fn % 2 == 1) or (fn == sn)
        if sib_left:
            h = node(sib, h)
            if fn % 2 == 0:
                while fn % 2 == 0 and fn != 0:
                    fn //= 2
                    sn //= 2
        else:
            h = node(h, sib)
        fn //= 2
        sn //= 2
    return h.hex() if sn == 0 else None


def verify_jws(jws, jwk):
    """ES256 验签, 用 cryptography 若可用, 否则返回 None(跳过而非假装通过)."""
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.exceptions import InvalidSignature
    except Exception:
        return None
    h, p, s = jws.split(".")
    x = int.from_bytes(b64d(jwk["x"]), "big")
    y = int.from_bytes(b64d(jwk["y"]), "big")
    pub = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256R1()).public_key()
    raw = b64d(s)
    der = utils.encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")) \
        if len(raw) == 64 else raw
    try:
        pub.verify(der, (h + "." + p).encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ""
    if not src:
        print(__doc__)
        return 2
    receipt = fetch(src) if src.startswith("http") else json.load(open(src))
    tid = receipt.get("task_id")
    print("receipt schema:", receipt.get("schema"), "unsigned:", receipt.get("unsigned"))
    print("task_id:", tid)

    inc = fetch("https://api.chit402.com/v1/receipts/%s/inclusion" % tid)
    head = fetch("https://api.chit402.com/v1/receipts/tree/head")
    jwks = fetch("https://api.chit402.com/.well-known/jwks.json")

    results = []
    # 1. 回执里的叶子必须等于包含接口返回的叶子
    leaf = (receipt.get("inclusion") or {}).get("leaf_hash")
    results.append(("receipt leaf == inclusion leaf", leaf == inc.get("leaf")))
    # 2. 折叠到签名树头
    root = fold(inc["leaf"], inc["leaf_index"], inc["tree_size"], inc["proof"])
    results.append(("merkle fold == inclusion root", root == inc.get("root")))
    results.append(("inclusion root == signed head root", inc.get("root") == head.get("root")))
    results.append(("inclusion tree_size == head tree_size", inc.get("tree_size") == head.get("tree_size")))
    # 3. 树头 JWS 验签
    jws = (head.get("issuer_signature") or {}).get("jws")
    ok = verify_jws(jws, jwks["keys"][0]) if jws else None
    results.append(("tree head ES256 signature", ok))
    # 4. JWS 载荷与返回的树头一致
    claims = json.loads(b64d(jws.split(".")[1])) if jws else {}
    results.append(("jws payload root == head root", claims.get("root") == head.get("root")))
    results.append(("jws payload anchor_tx == head anchor_tx", claims.get("anchor_tx") == head.get("anchor_tx")))
    # 5. Base 链上锚定: calldata 就是树根
    tx = rpc("eth_getTransactionByHash", [head.get("anchor_tx")])
    results.append(("anchor tx exists on Base", bool(tx)))
    if tx:
        results.append(("anchor calldata == root", (tx.get("input") or "").lower() == "0x" + head["root"]))
        results.append(("anchor from == claimed from", (tx.get("from") or "").lower() == head["anchor_from"].lower()))
        rcpt = rpc("eth_getTransactionReceipt", [head.get("anchor_tx")])
        results.append(("anchor tx status == success", bool(rcpt) and rcpt.get("status") == "0x1"))
    # 6. 回执字段是否绑定到叶子
    bound = any(k in receipt for k in ("row_hash", "book_chain"))
    results.append(("receipt carries a row_hash binding", bound))

    for name, value in results:
        print("%-40s %s" % (name, {True: "PASS", False: "FAIL", None: "SKIP"}[value]))
    return 0 if all(v is not False for _, v in results) else 1


if __name__ == "__main__":
    sys.exit(main())
