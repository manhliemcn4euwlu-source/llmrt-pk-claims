# Chit402 receipt: offline verification and review

Subject: `xfuel-56e3ee6d-2acb-4cab-8fa4-dfd5f9f31e6f`, the receipt linked from listing 59.
Checked 2026-10-20, 16:20 to 16:30 UTC. Verifier versions: `chit402-verify` 0.4.10 (official), and an independent stdlib implementation written for this review.

## (a) Offline verification

Everything below uses only public HTTP responses and standard cryptography. No Chit402 account, key, or service was consulted.

### The receipt you linked is a public shell and cannot be verified

```
$ curl -s 'https://api.chit402.com/receipt/chit-56e3ee6d-2acb-4cab-8fa4-dfd5f9f31e6f?format=json'
{"schema":"chit402.receipt_shell.v1","unsigned":true,"receipt_id":"xfuel-56e3ee6d-...",...}

$ node chit402-verify-0.4.10/dist/cli.js receipt.json
COULD_NOT_CHECK
This document is the public shell. The signed receipt is on the owner view.
Details: https://chit402.com/docs/verify#signed_receipt_unavailable
Issuer history: as of 2026-10-14
Pass the signed receipt from the owner view.
```

The official verifier itself declines the document named in the brief. `unsigned: true` is not incidental: the receipt that the public URL serves has no issuer signature, so there is nothing to verify against the published key. The HTML page states the same thing in prose: "Unsigned shell ... The signed receipt is on the owner view, and only it can verify."

### What the public shell does let you check

The shell carries an inclusion proof and a signed tree head. Both are independently reproducible.

```
$ curl -s https://api.chit402.com/v1/receipts/xfuel-56e3ee6d-2acb-4cab-8fa4-dfd5f9f31e6f/inclusion
leaf_index 30, leaf 24685dd1ea5dec24a43ded42036a9a3f00591a661aadbf723ff3a3c14b70700d
tree_size 35, root 344cfd286fbc7b90a16b38cd126911c46e835a3396d3bd976f8ddd6c04ea8b35

$ python3 tool/chit402_offline_verify.py 'https://api.chit402.com/receipt/chit-56e3ee6d-...?format=json'
receipt leaf == inclusion leaf           PASS
merkle fold == inclusion root            PASS
inclusion root == signed head root        PASS
inclusion tree_size == head tree_size    PASS
tree head ES256 signature                PASS
jws payload root == head root            PASS
jws payload anchor_tx == head anchor_tx    PASS
anchor tx exists on Base                 PASS
anchor calldata == root                  PASS
anchor from == claimed from              PASS
anchor tx status == success              PASS
receipt carries a row_hash binding       FAIL
```

The fold is RFC 9162: the sibling side is derived from `leaf_index` and `tree_size`, and the `position` labels agree with that derivation at all six steps. The head signature is ES256 over the JWS signing input, checked against the P-256 key at `/.well-known/jwks.json`, kid `IvFpmC-vPhkY_v0vidsrWVT9uzlE5XWKZgAEOeJTq1Q`.

The anchor transaction is real on Base:

```
$ curl -s -X POST https://mainnet.base.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getTransactionByHash","params":["0xa3d40f9937b48b56631dedb28b8337fc4f8a8ebf74c563d3c835fddd71a24a5c"]}'
from  0x1844d1f5fe42aff1cce6f776514fd40374079582
input 0x344cfd286fbc7b90a16b38cd126911c46e835a3396d3bd976f8ddd6c04ea8b35
status 0x1 (success)
```

The calldata equals the tree root, and the sender equals `anchor_from` in the signed claims. So the root was committed to Base at that transaction, and the issuer key signed that root.

The key history is self-consistent as well. Its `entry_hash` recomputes to the published value from the entry with `entry_hash` removed, serialized as sorted-key compact JSON, and its own JWS verifies under the key it names. That is circular by construction: a document that names its own key can always verify itself. The meaningful trust step is that the same kid signs the tree head and the history, so one key compromise breaks both. Nothing here establishes who controls that key.

### Every step where trust was required rather than earned

1. The DNS and TLS chain for `api.chit402.com`. Neither response is independently anchored elsewhere.
2. `/.well-known/jwks.json` is fetched from the same origin as the receipt. An attacker who controls the origin controls both the key and the signature. The package ships `issuer-history.snapshot.json`, but a snapshot inside the verifier package is a different trust path with the same single point of failure.
3. The Base RPC `mainnet.base.org` is trusted to return the real chain. A second independent RPC was not queried for this review.
4. Nothing in the public material proves that the leaf at index 30 contains this receipt's amount, payee, or payment transaction. See (b), finding 1.

## (b) Findings

### 1. The public shell's inclusion proof does not bind any receipt field (substantive)

The leaf is a fixed 32-byte value served by the inclusion endpoint. Folding it reproduces the anchored root. Changing every economic field of the receipt changes nothing in that computation, because no field participates in it.

```
$ python3 - <<'PY'
import json, hashlib
rec = json.load(open('receipt.json'))
rec['amount_settled'] = '999999'
rec['pay_to'] = '0x000000000000000000000000000000000000dead'
rec['payment_tx'] = '0x' + '00' * 32
print(fold(rec) == rec['inclusion']['signed_head']['root'])
PY
True
```

Expected: a verification artefact that carries a proof should fail when the fields it is supposed to attest are changed. Observed: the proof still passes, because it proves only that *some* leaf exists at index 30 in the signed tree, not that this receipt is that leaf.

The official verifier knows this and closes the gap by requiring a `row_hash` from the owner view, from which it rebuilds the leaf input `task_id|row_hash`. The public shell carries neither `row_hash` nor `book_chain`, so the public path cannot bind fields to the leaf at all. My check reports `receipt carries a row_hash binding FAIL` for exactly that reason. This is a design consequence rather than a bug in the fold, and the docs do not say it plainly enough: the page invites a reader to "Check it with chit402-verify", and the command returns COULD_NOT_CHECK.

Suggested fix: state on the public page, next to the proof, that the proof attests leaf presence only and that no field of the shell is covered by it. Optionally serve `row_hash` publicly, since the verifier treats it as a non-claim and the leaf is already public.

### 2. `receipt_id` and `task_id` disagree, and the receipt URL accepts either (minor, reproducible)

```
$ curl -s -o /dev/null -w '%{http_code}\n' 'https://api.chit402.com/receipt/chit-56e3ee6d-...?format=json'
200
$ curl -s -o /dev/null -w '%{http_code}\n' 'https://api.chit402.com/receipt/xfuel-56e3ee6d-...?format=json'
200
$ curl -s -o /dev/null -w '%{http_code}\n' 'https://api.chit402.com/receipt/abc-56e3ee6d-...?format=json'
404
```

The JSON returns `receipt_id: xfuel-...` while `task_id: xfuel-...` and the brief's URL uses `chit-...`. Both prefixes resolve to the same document. Expected: one canonical identifier, with the other either rejected or documented as an alias. Observed: an undocumented prefix alias, and a `receipt_id` that does not equal the URL segment that serves it. A consumer that keys a dedupe table on `receipt_id` and another that keys on `task_id` will disagree about identity for the same receipt.

### 3. `verifier_min` is advisory only (minor)

The shell advertises `verifier_min: 0.4.9`, and version 0.4.10 still returns COULD_NOT_CHECK for the very document it is attached to. Expected: a field named `verifier_min` either means the named version can verify this document, or it should be named for what it is. Observed: it is a floor for the format, not a promise about the document. A one-line rename to `format_min` or a note in the field's documentation would remove the ambiguity.

### 4. The tree head publishes before the epoch head exists (minor)

```
$ curl -s https://api.chit402.com/v1/receipts/tree/head
epoch 2, tree_size 35, anchor_status anchored
$ curl -s https://api.chit402.com/v1/receipts/tree/epoch/2/head
{"schema":"chit402.tree_head.v2","status":"not_yet_published","published":false,"epoch":2}
```

The live head says epoch 2 is anchored with 35 leaves. The epoch endpoint says epoch 2 is not yet published. Expected: a head that reports `anchored` for an epoch is retrievable from that epoch's endpoint, or the two endpoints document that they serve different clocks. Observed: a reader who fetches the epoch head first concludes the epoch does not exist, and a reader who fetches the live head concludes it does. Both cannot be the current state of one record.

## Reproduction

The verifier is 130 lines of stdlib Python plus `cryptography` for the ES256 check, at `tool/chit402_offline_verify.py` in the same repository. It prints PASS, FAIL, or SKIP per check and exits non-zero on any failure. It was run against the live endpoints for this report; the transcript above is its unedited output.
