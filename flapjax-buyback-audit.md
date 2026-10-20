# FlapJax buyback, 10-09 to 10-18: an on-chain tally

Window: blocks 126,536,085 to 128,454,491 (2026-10-09 00:00 to 2026-10-19 00:00 UTC). Token FLAPJAX `0x90c8889f428F9Ebb77BB8f15CAD3a50a9aC680df`, treasury `0x7C34E9e21eE28A49Ff0b84B61774119E6633359f`, pool `0xcA93EC685b8623688E6B236f9068034B298c2150`. Every Transfer log for the token in the window was pulled (223 events, 480 chunks of 4,000 blocks, zero failed chunks), then filtered locally by address.

## The nine buys

| # | Block | Time (UTC) | Tx hash | BNB | FLAPJAX received | Recipient |
|---|---|---|---|---|---|---|
| 1 | 126684151 | 10-09 18:30 | `0xbeefabdc89f9148f9daaef6082d34a60dc5b4b612972ca0fd39d6bd4eb03b4b0` | 0.01 | 24,052,995.308271524 | treasury |
| 2 | 126875701 | 10-10 18:27 | `0x8ce8e8578da26f8c7acb0f44c6ca0d0b8dcba868cafe2d729bb48562863f2d62` | 0.01 | 23,979,958.557395637 | treasury |
| 3 | 127067713 | 10-11 18:30 | `0x82d01172ae26f1c86287643e123af1675ca5c18b984b7740c1a0c1647d2801eb` | 0.01 | 23,907,253.965589990 | treasury |
| 4 | 127261246 | 10-12 18:46 | `0x9afdc96e3ca876b5b617a26ba5105012ed8c33e805c77b1616bf48c198d5cbf1` | 0.01 | 23,834,879.521763890 | treasury |
| 5 | 127452454 | 10-13 18:41 | `0xc94de373d1fb00093431224a97475b3b2b48b9a4962d15acbe9d9c5c016d720c` | 0.01 | 23,762,833.230024090 | treasury |
| 6 | 127643212 | 10-14 18:32 | `0x172349c64ed3c45663650049f9e2ad3d763b1243c5c849b7d66f144f221d3186` | 0.01 | 23,691,113.109537147 | treasury |
| 7 | 128086717 | 10-17 02:00 | `0xc999000f16f326e8868fe37f83871219be1a63f98043b0aef9ee57f469232156` | 0.01 | 23,669,235.465921230 | treasury |
| 8 | 128178495 | 10-17 13:29 | `0x6ec66780e0518da7c3c8b55d13b66d57400046f89ebe9df479c3c878f7b3311f` | 0.01 | 23,597,938.349722730 | treasury |
| 9 | 128370339 | 10-18 13:28 | `0x05a9acf81b0eae4b7ff9a12168aead25964b6b2c0a16d3d1e667b7db6f17ad99` | 0.01 | 23,506,585.156697210 | treasury |

Each transaction is a swap through PancakeSwap V3 router `0x1b81d678ff...`, sent by the treasury, with the FLAPJAX leg arriving at the treasury in the same transaction. The pool is the sender of the token leg.

## Totals and formulas

- BNB spent = 9 x 0.01 = **0.09 BNB**
- FLAPJAX received = **214,002,792.664923460**
- Average price = 0.09 / 214,002,792.664923460 = **4.2056e-10 BNB per FLAPJAX**
- First buy = 0.01 / 24,052,995.308271524 = **4.1575e-10 BNB/FLAPJAX**
- Last buy = 0.01 / 23,506,585.156697210 = **4.2541e-10 BNB/FLAPJAX**
- Drift: the last buy is **2.32%** dearer per FLAPJAX than the first, so each day's 0.01 BNB bought slightly fewer tokens.

## Their statements

**1. Nine buys of 0.01 BNB each, 0.09 BNB total — MATCH.** Nine Transfer logs into the treasury, each in a 0.01 BNB transaction.

**2. One a day except 10-15, owed as a make-up on 10-23 — MISMATCH.** 10-15 was missed and so was **10-16**. Buys landed on 10-09, 10-10, 10-11, 10-12, 10-13, 10-14, then 10-17 twice (02:00 and 13:29) and 10-18 once. The gap is two days, so either a second make-up is owed for 10-16, or the two 10-17 buys are the make-up and one day remains short.

**3. Every buy's FLAPJAX went to the treasury — MATCH.** All nine logs name the treasury as the token recipient.

**4. The treasury sent no FLAPJAX to the pool in that window — MATCH.** Zero Transfers with the treasury as sender and the pool as recipient.

## What else the window shows

The treasury sent FLAPJAX out 191 times, 114,630,000 in total, to addresses other than the pool. Six transfers went into the pool from other addresses and two came out of the pool to other addresses; those sit outside the buyback program and explain why the pool balance is not the sum of the buys.

## Method

`eth_getLogs` for the token's Transfer topic, 4,000 blocks per call, 480 chunks, none failed. Per-buy BNB value read from the full block body, because the node no longer serves `eth_getTransactionByHash` for blocks that old. Sender and recipient decoded from topics 1 and 2, amount from the data field at 18 decimals.

Data: `tmp/flapjax_q35.json` (223 transfers) and `tmp/flapjax_buys.json` (nine buys with BNB values).

