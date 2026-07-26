---
status: approved-for-v2-matrix
approved_by_user: 2026-07-26
source_id: ABALONE-RULES-SCHMIDT-4P
rulebook: inputs/games/abalone/game_rules.pdf
sha256: c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550
scope: two-player untimed base game; optional clock excluded
---

# Abalone V2 atomic rule facts

## Source register

The only gameplay source is the supplied four-page Schmidt Spiele German PDF, role `publisher_rulebook`, SHA-256 `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`. All four pages were freshly rendered at 150 DPI with `pdftoppm 24.04.0`; the render manifest records page hashes. Figure evidence is explicitly diagram-derived. `claims_v2.json`, this file, scenarios, adapters, historical results, and user decisions are derived experiment artifacts, not publisher sources.

## Atomic inventory

`claims_v2.json` is canonical: 46 atomic claims comprising 36 source-clear claims, one material ambiguous interpretation, nine missing claims, and one clear-but-socially-untestable color-lottery claim within the clear count. Thirty-three material deterministic clear claims require hard mapping; `ABAL-C-COLOR-LOTTERY`, `ABAL-C-MOVE-FINAL`, and `ABAL-C-CLOCK-OPTIONAL` carry explicit coverage exceptions where applicable.

Core source-clear groups:

- Page 1: exactly two players; Figure-1 board/setup (61 pits, 14 black, 14 white, 33 empty); black starts; turns alternate; one movement; one-step, six-direction, one-to-three-marble movement; straight contiguous groups; maximum three; subsets from longer rows.
- Pages 1–2: inline and broadside movement and ordinary empty-destination requirements.
- Pages 2–3: strict-superiority inline Sumito; 2v1, 3v1, 3v2; adjacency; free-behind requirement; blocked, gap, and non-collinear prohibitions; Sumito is optional.
- Pages 3–4: 1v1, 2v2, 3v3 Patt; 4v3 adds no strength; legal Patt withdrawal/broadside; crossing-angle Sumito; edge ejection; immediate victory on the sixth opposing ejection.
- Page 4: clocks are optional, but mechanics and timeout outcomes are absent and excluded.

Physical box inventory is not stated. Only the in-play Figure-1 inventory is hard-scoreable.

## Approved human decisions

These frozen evaluator decisions are separately attributed in `decisions_v2.json` and are not publisher claims. The model-facing clarification artifact is created only after the original run has been evaluated:

1. Every broadside destination is on-board and empty.
2. Exactly one forced pass exists only when no legal movement exists; no voluntary pass exists.
3. On the sixth ejection, terminal is immediate, terminal legal actions are empty, and `current_player` remains the winner.
4. Returns are `[0,0]` before terminal and winner/loser `+1/-1` in player-ID order at terminal.
5. Exactly one canonical serialized action represents each physical movement.
6. Public state exposes board, current player, captures, terminal, winner, phase, and move number.
7. Player 0 is black, player 1 is white, and player 0 starts.

## Unresolved and unscored

The publisher source provides no draw, repetition, move-limit, box-inventory, or clock-expiration result. No such outcome becomes a hard failure. The social color lottery is not deterministically reproduced. Move irrevocability has no separate undo API; turn advancement is tested under the turn-order claim.

## Historical disposition

The V3 suite evaluated 22 configured clear-basis scenarios and one forced-pass human-decision scenario. All clear cases passed and forced pass failed. Its 100% coverage value meant configured-scenario evaluated coverage, not complete atomic-claim coverage. V2 replaces private alias probing and physically inconsistent sparse capture fixtures with the canonical public data contract and inventory-consistent states.
