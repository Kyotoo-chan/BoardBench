# BoardBench judge packet

- game: exploding_kittens

- OpenSpiel reference: none

- variant: oneshot

- generated code: outputs/exploding_kittens_oneshot.py

- expected judge reply path: outputs/exploding_kittens_oneshot_judge.md



## Judge prompt

# LLM judge scoring prompt

Use this as a qualitative scoring step after a game implementation has been generated. The judge is not the source of truth and must not rewrite the implementation. Its job is to score how well the generated BoardBench environment appears to implement the provided rulebook.

## Inputs to use

Use only the artifacts provided in the packet:

1. the original rulebook text, or the attached/rendered rulebook page images
2. the implementation brief, if one was created
3. the generation prompt/backbones used
4. the generated Python file

Do **not** use outside game knowledge, remembered rules, internet knowledge, or OpenSpiel knowledge unless that material is explicitly included in the packet. If something is not clear from the rulebook, mark it as uncertain rather than wrong.

Do not rerun deterministic checks and do not judge mainly by check logs. The deterministic BoardBench checks are separate. This review should focus on rule fidelity, game logic, assumptions, and testability.

## Scoring target

Give one overall score from `0.0` to `1.0`:

- `1.0`: faithful, complete, and benchmark-ready based on the provided rulebook
- `0.8`: mostly correct with only minor issues or harmless assumptions
- `0.6`: playable but with notable uncertain or partially implemented rule areas
- `0.4`: major rule or state-transition issues likely affect gameplay
- `0.2`: severe missing mechanics or unreliable terminal/scoring logic
- `0.0`: unusable or largely unrelated to the rulebook

Use the full range when justified. Do not give a high score only because the API exists or the code looks clean.

## Review focus

Prioritize:

- setup and board/components
- player count and turn order
- legal actions
- state transitions
- terminal/win/loss/draw conditions
- scoring/returns
- chance handling, if any
- hidden information, if any
- simultaneous moves, if any
- action names/rendering as a BoardBench interface
- unsupported assumptions or invented rules
- likely missing deterministic scenario tests

## Required output format

### 1. Score

Give:

- `score: <number from 0.0 to 1.0>`
- `confidence: low|medium|high`
- a short 2-4 sentence justification

### 2. Top findings

List the most important findings first. For each finding include:

- severity: critical / major / minor / question
- evidence from the rulebook, generated code, or provided artifacts
- why it matters for gameplay or benchmarking
- suggested next action

### 3. Rule coverage review

Create a table with columns:

- rule area
- covered correctly / partially covered / missing / unclear
- evidence
- notes

Cover at least: setup, player count and turn order, legal actions, state transitions, terminal conditions, scoring/returns, rendering/action names, chance/hidden/simultaneous if relevant.

### 4. Unsupported assumptions or invented rules

List every place where the implementation appears to decide something not specified by the provided rulebook. Distinguish harmless conventions from risky invented rules.

### 5. Missing scenario tests

Suggest concrete additional deterministic tests. Prefer action-name sequences that could later be turned into checks.

### 6. Open questions for the human

Ask only questions that materially affect implementation correctness or benchmark scoring.

### 7. Machine-readable summary

End with exactly this compact YAML-like block:

```text
score: <0.0-1.0>
confidence: low|medium|high
critical_issues: <number>
major_issues: <number>
minor_issues: <number>
needs_rulebook_clarification: true|false
needs_code_change: true|false
needs_more_tests: true|false
```




## Generation prompt (prompts/rulebook_to_python.txt)

You will receive rule text.

Use only that information.
Do not use outside knowledge or remembered rules for the game.
If an implementation brief or backbone context is provided, use it only as an interpretation aid; the rule text wins if there is a conflict.

Write one simple, self-contained Python file using only the standard library.
Do not import any non-standard-library package or external game framework.
Do not require external files, images, environment variables, network access, subprocesses, API keys, or interactive input.
Keep top-level code limited to definitions and constants.

If rules are unclear or incomplete, state the assumptions briefly before the code and in comments where relevant.
Do not silently fill missing rules with outside knowledge.
Prefer a smaller explicit implementation with documented gaps over broad invented mechanics.

If possible, include this minimal game API:
- `GameState`
- `Game`
- `initial_state(self)`
- `current_player(self, state)`
- `legal_actions(self, state)`
- `apply_action(self, state, action)` returning the next state, or clearly documenting in-place mutation
- `is_terminal(self, state)`
- `returns(self, state)` returning one numeric value per player
- `render(self, state)` returning a stable, compact, human-readable string suitable for side-by-side inspection
- `action_to_name(self, action)` returning a unique canonical action name
- `name_to_action(self, name)` reversing a canonical action name

Rules for actions and state presentation:
- `legal_actions` must only return actions that `apply_action` accepts.
- `action_to_name` and `name_to_action` must round-trip exactly.
- Action names must be human-readable, stable, unique in sampled states, and must not rely on raw internal indices alone.
- If action names contain signed numeric coordinates, encode signs unambiguously (for example `pos1`/`neg1` or `p1`/`n1`) so different points cannot collapse when punctuation is normalized.
- If the rule text defines labels for squares, points, regions, cards, or other move targets, use those labels in action names and render output.
- If the rule text explicitly defines or clearly implies a standard move notation, use that notation consistently; otherwise use a simple explicit format such as `place:<target>`, `move:<source>-><target>`, `remove:<target>`, or similarly clear equivalents.
- `render` should be deterministic across repeated calls on the same state and avoid decorative prose.
- Terminal states should have no legal actions and stable returns.

Only if required by the rule text, include:
- `chance_outcomes(self, state)` for stochastic rules
- `information_state(self, state, player)` for hidden-information rules

Output:
1. `Open questions / assumptions`
2. one fenced `python` code block with the full file




## OpenSpiel backbone (prompts/open_spiel_backbone.md)

# OpenSpiel-inspired BoardBench backbone

Use this as extra context with `prompts/rulebook_to_python.txt` and the rulebook.

This is an interface/backbone, not a dependency. Generated code must stay one self-contained standard-library Python file. Do not import `pyspiel`, `open_spiel`, external frameworks, files, network, subprocesses, or API keys.

Use OpenSpiel only for structure: explicit state, legal actions, deterministic transitions, optional chance nodes, optional information states, stable action names, and numeric returns. The rulebook is always the source of truth.

## Required shape

Implement:

```python
class GameState:
    ...

class Game:
    def initial_state(self): ...
    def current_player(self, state): ...
    def legal_actions(self, state): ...
    def apply_action(self, state, action): ...
    def is_terminal(self, state): ...
    def returns(self, state): ...
    def render(self, state): ...
    def action_to_name(self, action): ...
    def name_to_action(self, name): ...
```

Optional only if the rulebook needs them:

```python
def chance_outcomes(self, state): ...        # [(action, probability), ...]
def information_state(self, state, player): ...
def observation(self, state, player): ...
def rewards(self, state): ...               # latest step rewards if separate from returns
```

Suggested sentinel constants:

```python
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3
```

`current_player(state)` should return a player index, `TERMINAL`, `CHANCE`, or `SIMULTANEOUS`.

## Implementation recipe

1. Classify the game from the rulebook: player count, turn structure, chance, hidden information, scoring type.
2. Define `GameState` fields first: public state, private state, phase, current player, scores/returns, history.
3. Define action objects and canonical action names before transition logic.
4. Implement `legal_actions` as a pure deterministic function of state.
5. Implement `apply_action` by validating the action, updating state, switching player/phase, and updating terminal/returns.
6. Keep scoring and terminal rules separate enough to inspect and test.
7. Make `render` compact, deterministic, and useful for side-by-side comparison.
8. Document assumptions exactly where the rulebook is unclear.

Prefer returning a fresh state from `apply_action`. If mutating in place, document it clearly.

## Invariants

- `initial_state()` returns a fresh state.
- terminal states have no legal actions.
- non-terminal player states have legal actions unless the rulebook explicitly allows a dead state.
- `legal_actions` lists only actions accepted by `apply_action`.
- `returns` always has one numeric value per player.
- `render` is deterministic for the same state.
- `action_to_name` and `name_to_action` round-trip for legal actions.
- chance probabilities, if present, are non-negative and sum to 1.
- hidden-information views, if present, do not reveal private data to the wrong player.
- max length / repetition / pass rules are encoded when needed to avoid accidental infinite games.

## Action names

Use rulebook labels whenever available. Otherwise use explicit names:

- `place:<target>`
- `move:<source>-><target>`
- `remove:<target>`
- `claim:<item>`
- `bid:<amount>`
- `pass`
- `chance:deal:<card>`
- `chance:roll:<value>`
- `p0:<a0>|p1:<a1>` for simultaneous joint actions

Avoid names that only expose internal indices unless the rulebook itself uses those indices.

## Game-type add-ons

### Sequential perfect-information games

Use when exactly one player acts and all relevant state is public.

- no `chance_outcomes` or `information_state` needed
- switch the current player after each normal action unless the rules say otherwise
- test wins/draws, blocked/illegal moves, and terminal no-actions behavior

### Chance/stochastic games

Use when cards, dice, random setup, or random events affect play.

- model randomness as explicit chance actions, never hidden calls to `random`
- `current_player` returns `CHANCE` at chance nodes
- `chance_outcomes(state)` returns probabilities for the same chance actions that `legal_actions(state)` returns without probabilities
- `apply_action` consumes the selected chance action deterministically

### Hidden-information games

Use when hands, cards, objectives, or other facts are private.

- keep full truth in `GameState` for correctness
- expose player-visible data through `information_state(state, player)`
- `render(state)` may be full debug state, but document that it is not player-visible
- action names must not leak hidden data unless the action legally reveals it

### Simultaneous-move games

Use when players commit actions before seeing others' choices.

```python
def legal_actions(self, state, player=None): ...
def legal_joint_actions(self, state): ...
def apply_actions(self, state, actions_by_player): ...
```

For simple BoardBench rollouts, `legal_actions(state)` at a simultaneous node should return joint actions that `apply_action(state, joint_action)` can resolve. Name joint actions as `p0:<a0>|p1:<a1>`.

### Multiplayer, teams, or general-sum scoring

- set `num_players` from the rulebook
- `returns(state)` length must equal `num_players`
- map team scores to each individual player explicitly
- handle skipped/eliminated players in turn order

### Repeated rounds or step rewards

- keep cumulative returns separate from latest `rewards(state)` if step rewards matter
- reset round-local state without losing cumulative scores
- encode round limits, target score, or other stop rules

### Games with OpenSpiel references

If comparing against OpenSpiel later:

- prefer rulebook-compatible action names that canonicalize well against OpenSpiel action strings
- keep `render` compact enough for side-by-side inspection
- document deliberate mismatches caused by incomplete rulebook text




## Rule text (inputs/game_rules.pdf)

NSFW EDITION!
so funktioniert’s spielaufbau Spielzug
spielende
Einige Karten in diesem Spiel zeigen Exploding 
Kittens. Ihr spielt, indem ihr reihum eine 
verdeckte Karte vom Spielstapel zieht. So 
lange, bis jemand ein Exploding Kitten zieht.
In dem Augenblick explodiert dieser Spieler. 
Er ist tot und scheidet aus dem Spiel aus.
Legt alle 4 Exploding Kittens und alle 
6 Karten „Entschärfung“ beiseite.
Nimm deine 8 Startkarten auf die Hand, 
schau sie dir an und entscheide dich für:
Du beendest deinen Zug, indem du die 
oberste Karte vom Spielstapel ziehst.
Hoffentlich ist es kein Exploding Kitten.
(Im Gegensatz zu vielen anderen Spielen 
ziehst du die Karte am ENDE deines Zuges.)
Die Partie geht im Uhrzeigersinn weiter.
Mischt die restlichen Karten sorgfältig. Teilt 
danach an jeden Spieler verdeckt 7 Karten aus.
Mischt zuletzt alle übrigen Karten „Entschärfung“ 
in den Spielstapel.
Bestimmt einen Startspieler. (Mögliche Kriterien: 
der beeindruckendste Bart, dominanter Geruch 
oder die Länge des Blinddarms etc.)
Mischt den Spielstapel und legt ihn verdeckt in 
die Mitte des Tisches. Von diesem Stapel werdet 
ihr im Spielverlauf reihum Karten ziehen.
Das ist der Spielstapel.
(Lasst etwas Platz für einen Ablagestapel.)
Zusätzlich erhält jeder Spieler eine 
Karte „Entschärfung“. So starten 
alle mit 8 Karten auf der Hand. 
Halte dein Blatt stets verdeckt.
Nehmt jetzt von den zur Seite gelegten 
Exploding Kittens eine Karte weniger als Spieler 
teilnehmen und mischt sie in den Spielstapel. 
Legt die übrigen Exploding Kittens in die 
Schachtel zurück.
Eine Runde endet, wenn nur noch ein 
Spieler am Leben ist: der Gewinner.
Je mehr Karten du ziehst, desto wahr­
scheinlicher ziehst du ein Exploding Kitten.
blick in die zukunft
hops!
Du kannst die Karte Blick 
in die Zukunft ausspielen, 
um dir die oberen drei Karten des 
Spielstapels anzusehen. Wenn 
dort ein Exploding Kitten lauert, 
kannst du mit der Hops!­Karte 
deinen Zug beenden, ohne eine 
Karte vom Spielstapel zu ziehen.
Jeder Spieler beginnt mit einer Karte „Entschärfung“, 
der mächtigsten Karte im Spiel. Sie ist deine einzige 
Rettung vor Exploding Kittens. Wenn du mit dieser 
Karte auf ein Exploding Kitten reagierst, darfst du es 
zurück in den Spielstapel legen, ohne zu explodieren. 
Und zwar geheim an eine Stelle deiner Wahl.
Sammle so viele Karten „Entschärfung“ wie möglich.
Nehmt 3 Exploding Kittens bei 4 Spielern 
und 2 Exploding Kittens bei 3 Spielern.
Auf diese Weise ist ganz sicher, dass 
alle Spieler explodieren – außer einem.
Mischt nur 2 Karten „Entschärfung“ in den 
Spielstapel und legt die übrigen in die 
Schachtel zurück.
beispiel
Beispiel
variante für zwei spieler
ENTSchärfung
denk dran
Gut zu wissen
PASSEn 
Spiele keine Karte aus.
spielen 
Wähle eine deiner Handkarten aus, lege sie OFFEN 
auf den Ablagestapel und befolge ihre Anweisung.
Der Text auf der 
Karte beschreibt, 
was die Karte macht.
Nachdem du die Anweisung der Karte befolgt hast, 
kannst du weitere Karten spielen, so viele du möchtest.
Spiele so viele (oder so wenige) Karten aus, wie du 
möchtest, und ziehe am Ende eine Karte nach.
Passen oder spielen, dann ziehen. 
Passen oder spielen, dann ziehen.
Der Spieler, der nicht explodiert 
und als Letzter übrig ist, gewinnt.
Keine Sorge, der Spielstapel wird nie leer, 
weil alle Spieler (außer einem) vorher Exploding 
Kittens ziehen werden – Explosionen garantiert!
Versuche zu Beginn ein paar Karten auf der Hand 
zu behalten, wenn die Wahrscheinlichkeit zu 
explodieren noch gering ist.
Du darfst die Anzahl der übrigen Karten im 
Spielstapel jederzeit nachzählen.
Es gibt keine minimale oder maximale Handkarten­
zahl. Falls du keine Karten mehr auf der Hand 
hast – keine Panik. Spiele einfach weiter. Am Ende 
deines nächsten Zuges ziehst du wieder eine!
schluss mit lesen! geh spielen!  
falls ihr fragen zu bestimmten Karten habt, dreht die spielregel um.
exploding kittens
spielregeln
spieler: 2–5
spielmaterial: 56 Karten
komm, leg die anleitung weg!
ein spiel lernt man nicht,
indem man regeln liest.
schau dir lieber dieses
video online an:
WWW.EXPLODINGKITTENS.COM/HOW
gründsätzlich
wer explodiert, verliert.
du bist ein verlierer, ein armseliges HÄUFCHEN elend.
wer nicht explodiert, gewinnt.
du bist zu etwas höherem bestimmt. gut gemacht!
alle weiteren karten 
reduzieren die WAHRSCHEINLICHKEIT, 
durch exploding kittens zu explodieren.
oder
Copyright Exploding Kittens 2018

kittensEXPLODING
Krieche in einen Ziegenarsch und erblicke 
lauter wundersame Dinge
NSFW
Blick in die Zukunft
Blick in die Zukunft
Schau dir die obersten drei 
Karten des Spielstapels an.
Beende deinen Zug, ohne eine Karte zu ziehen. 
Der nächste Spieler muss zwei Züge machen.
Angriff
Lass die Folterhäschen frei
Angriff
NSFW
NSFW
Nö!
Das NÖ! Zum Sonntag
Nö!
GELOBET SEI DAS  
NÖÖÖ!
Verhindere eine Aktion eines Mitspielers. 
Immer einsetzbar.
Misch den Spielstapel neu.
Mischen
Rauch Crack mit einer Baby-Eule
Mischen
NSFW
LASS ‘MA EINEN DURCHZIEHEN, 
BRO!
Zombiekatze
Zombiekatze
Augenmampfende
Augenmampfende
Alleine ist diese Katzen-Karte machtlos.  
Spiele zwei Zombiekatzen als Pärchen aus,  
um eine Karte von einem Mitspieler zu stehlen.
NSFW
 MAMPF
SCHMATZ
SCHMATZ
Zombiekatze
Zombiekatze
Augenmampfende
Augenmampfende
Alleine ist diese Katzen-Karte machtlos.  
Spiele zwei Zombiekatzen als Pärchen aus,  
um eine Karte von einem Mitspieler zu stehlen.
NSFW
 MAMPF
SCHMATZ
SCHMATZ
beispielzug
Exploding Kitten 4 karten angriff 4 karten
hops! 4 karten
katzen-karten  
4 jeder art
wunsch 4 karten
mischen 4 karten
blick in die zukunft 5 karten
entschärfung 6 karten
Nö! 5 karten
Du spielst die KArte  
„blick in die zukunft“ aus.
du schaust dir die 3 obersten karten 
an und siehst, dass du gleich ein 
exploding kitten ziehen würdest.
du ENTSCHEIDEST dich, eine 
karte „angriff“ auszuspielen. 
dadurch beendest du deinen 
zug und zwingst gleichzeitig 
den nächsten spieler, zwei 
spielzüge zu machen.
doch dann spielt ein anderer 
spieler eine nö!-karte aus und 
setzt deinen angriff ausser 
kraft. du bist weiter am zug.
du willst auf keinen fall 
die nächste karte ziehen 
und explodieren. Daher 
spielst du eine karte 
„mischen“ aus und darfst den 
spielstapel neu mischen.
neuE reihenfolge, 
neues glück! du ziehst 
die oberste karte und 
beendest deinen spiel-
zug. hoffentlich ist es 
kein exploding kitten.
Diese Karte musst du sofort offen zeigen. Solltest 
du keine „Entschärfung“ mehr besitzen, war’s das.
Alle deine restlichen Karten und das Exploding Kitten 
wandern auf den Ablagestapel.
Beende sofort deinen Zug, ohne eine Karte zu 
ziehen. (Falls du „Hops!“ ausspielst, um einen 
Angriff abzuwehren, überspringst du nur einen der 
zwei Züge. Du müsstest schon zweimal „Hops!“ 
ausspielen, um beide Züge zu beenden.)
Pärchen
Jetzt können ALLE gleichen Karten als Pärchen 
gespielt werden, um einem Mitspieler eine 
zufällige Karte zu stehlen. Die Regel gilt also 
nicht mehr nur für Katzen­Karten, sondern für 
alle Karten mit dem gleichen Titel (ein Pärchen 
Wunsch­Karten, ein Pärchen Hops!­Karten ...).
drilling 
Wie ein Pärchen, außer dass du dir eine Karte 
von dem Mitspieler wünschen darfst. Besitzt er 
solch eine Karte, muss er sie dir geben. Hat er 
keine solche Karte, hast du Pech gehabt.
fünfling 
Wenn du 5 verschiedene Karten (jede mit 
einem anderen Titel) spielst, darfst du dir eine 
beliebige Karte aus dem Ablagestapel nehmen.
(Nicht trödeln, sonst hält dich noch jemand mit 
einem NÖ! von deinem Vorhaben ab.)
Wenn du eine Kombination spielst, gelten die 
Anweisungen auf den Karten nicht.
Einzeln sind diese Karten machtlos, doch wenn 
du 2 gleiche Katzen­Karten hast, kannst du sie als 
Pärchen spielen, um eine zufällige Karte von einem 
Mitspieler zu stehlen. Oder du nutzt sie für eine 
andere Kombination, siehe rechts.
Zwinge einen Mitspieler deiner Wahl, dir eine Karte 
zu geben. Dieser Spieler entscheidet, welche Karte 
du bekommst.
Misch den Spielstapel sorgfältig neu. (Diese Karte 
ist besonders nützlich, wenn du weißt, dass ein 
Exploding Kitten oben auf dem Stapel liegt.)
Schau dir die obersten drei Karten des 
Spielstapels an und lege sie zurück, ohne deren 
Reihenfolge zu verändern. Zeige diese Karten bloß 
nicht deinen Mitspielern.
Du beendest deinen eigenen Zug, ohne eine Karte 
zu ziehen, und zwingst den nächsten Spieler, zwei 
Spielzüge direkt nacheinander auszuführen. Dein 
Opfer macht seinen ersten Zug und direkt danach 
noch einen. (Spielt dein Opfer dabei selbst eine Karte 
„Angriff“ aus, ist er nicht mehr an der Reihe und der 
nächste Spieler muss zwei Spielzüge ausführen.)
Wenn du ein Exploding Kitten ziehst, kannst du eine 
„Entschärfung“ ausspielen, statt zu sterben. Spiele 
sie einfach aus und lege sie auf den Ablagestapel.
Mit NÖ! setzt du eine 
andere Karte und deren 
Aktion außer Kraft, 
ausgenommen Exploding 
Kittens und Entschärfung. 
Es ist so, als würde sich 
die Karte, das Pärchen oder die Kombination 
durch ein NÖ! in Luft auflösen. 
Du kannst ein NÖ! auf ein anderes NÖ! legen, um 
es aufzuheben und daraus ein DOCH! zu machen.
Du kannst ein NÖ! auch 
spielen, wenn du nicht 
an der Reihe bist. Alle 
Karten, die ge­NÖ!­t 
wurden, sind raus 
und bleiben auf dem 
Ablagestapel.
Lege danach das Exploding Kitten zurück in den 
Spielstapel, und zwar geheim an eine Stelle deiner 
Wahl, ohne die anderen Karten anzusehen oder 
umzusortieren.
Du willst dem nächsten Spieler eins auswischen? 
Lege das Exploding Kitten ganz oben auf den 
Spielstapel. Mach das z. B. unter dem Tisch, damit 
niemand sieht, an welche Stelle du das Kitten 
zurücklegst. Dann ist dein Spielzug beendet.
Ich spiele Blick in die Zukunft. NO!
Mist.
PAFF!
Doch!
Gib mir deine 
ENTSCHARFUNG. Bitte.
kombinationen
(lies das hier erst nach ein paar partien.)
schlachtplan
schaue hier nur nach, wenn du eine frage zu einer bestimmten karte hast.



## Generated code (outputs/exploding_kittens_oneshot.py)

```python
from dataclasses import dataclass, replace
from collections import Counter
from itertools import combinations
from typing import Optional, Tuple


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

EXPLODING = "Exploding-Kitten"
DEFUSE = "Entschaerfung"
ATTACK = "Angriff"
SKIP = "Hops"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE_FUTURE = "Blick-in-die-Zukunft"
NOPE = "Noe"

CAT1 = "Augenmampfende-Zombiekatze"
CAT2 = "Katzenkarte-2"
CAT3 = "Katzenkarte-3"
CAT4 = "Katzenkarte-4"
CAT5 = "Katzenkarte-5"

CARD_ORDER = (
    EXPLODING,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
    CAT1,
    CAT2,
    CAT3,
    CAT4,
    CAT5,
)
HAND_CARD_ORDER = tuple(c for c in CARD_ORDER if c != EXPLODING)
CARD_INDEX = {c: i for i, c in enumerate(CARD_ORDER)}

CARD_LABEL = {
    EXPLODING: "Exploding Kitten",
    DEFUSE: "Entschärfung",
    ATTACK: "Angriff",
    SKIP: "Hops!",
    FAVOR: "Wunsch",
    SHUFFLE: "Mischen",
    SEE_FUTURE: "Blick in die Zukunft",
    NOPE: "Nö!",
    CAT1: "Augenmampfende Zombiekatze",
    CAT2: "Katzenkarte 2",
    CAT3: "Katzenkarte 3",
    CAT4: "Katzenkarte 4",
    CAT5: "Katzenkarte 5",
}

BASE_COUNTS = {
    EXPLODING: 4,
    DEFUSE: 6,
    ATTACK: 4,
    SKIP: 4,
    FAVOR: 4,
    SHUFFLE: 4,
    SEE_FUTURE: 5,
    NOPE: 5,
    CAT1: 4,
    CAT2: 4,
    CAT3: 4,
    CAT4: 4,
    CAT5: 4,
}


@dataclass(frozen=True)
class GameState:
    num_players: int
    phase: str
    hands: Tuple[Tuple[str, ...], ...]
    deck: Tuple[str, ...] = ()
    discard: Tuple[str, ...] = ()
    alive: Tuple[bool, ...] = ()
    current: int = 0
    turns_remaining: int = 1

    setup_counts: Tuple[int, ...] = ()
    deal_index: int = 0
    build_deck: Tuple[str, ...] = ()

    shuffle_counts: Tuple[int, ...] = ()
    shuffle_build: Tuple[str, ...] = ()

    pending_effect: Optional[Tuple] = None
    pending_steal: Optional[Tuple[int, int]] = None

    nope_count: int = 0
    last_nope_player: int = -1
    reaction_player: int = -1
    passes_since_nope: int = 0

    # Simplified private memory: only latest "Blick in die Zukunft" result.
    seen_top: Tuple[Tuple[str, ...], ...] = ()
    history: Tuple[str, ...] = ()


def _empty_seen(n):
    return tuple(() for _ in range(n))


def _counts_from_mapping(mapping):
    return tuple(int(mapping.get(c, 0)) for c in CARD_ORDER)


def _counts_from_cards(cards):
    return _counts_from_mapping(Counter(cards))


def _counts_total(counts):
    return sum(counts)


def _decrement_count(counts, card):
    idx = CARD_INDEX[card]
    if counts[idx] <= 0:
        raise ValueError("count is already zero")
    data = list(counts)
    data[idx] -= 1
    return tuple(data)


def _sort_cards(cards):
    return tuple(sorted(cards, key=lambda c: CARD_INDEX[c]))


def _hand_count(hand, card):
    return hand.count(card)


def _remove_cards_from_hand(hand, cards):
    data = list(hand)
    for card in cards:
        try:
            data.remove(card)
        except ValueError:
            raise ValueError("card not in hand")
    return _sort_cards(data)


def _add_card_to_hand(hand, card):
    return _sort_cards(tuple(hand) + (card,))


def _replace_hand(hands, player, new_hand):
    data = list(hands)
    data[player] = new_hand
    return tuple(data)


def _remove_cards_from_player(hands, player, cards):
    return _replace_hand(hands, player, _remove_cards_from_hand(hands[player], cards))


def _add_card_to_player(hands, player, card):
    return _replace_hand(hands, player, _add_card_to_hand(hands[player], card))


def _remove_one_from_discard(discard, card):
    data = list(discard)
    try:
        data.remove(card)
    except ValueError:
        raise ValueError("card not in discard")
    return tuple(data)


def _alive_count(alive):
    return sum(1 for x in alive if x)


def _next_alive_after(alive, player):
    n = len(alive)
    for step in range(1, n + 1):
        idx = (player + step) % n
        if alive[idx]:
            return idx
    return -1


def _distinct_cards(cards, order=CARD_ORDER):
    present = set(cards)
    return tuple(c for c in order if c in present)


def _format_ordered(cards):
    if not cards:
        return "[]"
    return "[" + ",".join(CARD_LABEL.get(c, c) for c in cards) + "]"


def _format_multiset(cards):
    if not cards:
        return "{}"
    counts = Counter(cards)
    parts = []
    for card in CARD_ORDER:
        if counts.get(card, 0):
            parts.append(f"{CARD_LABEL[card]}x{counts[card]}")
    return "{" + ";".join(parts) + "}"


def _format_counts_tuple(counts):
    if not counts:
        return "{}"
    parts = []
    for card, count in zip(CARD_ORDER, counts):
        if count:
            parts.append(f"{CARD_LABEL[card]}x{count}")
    return "{" + ";".join(parts) + "}" if parts else "{}"


def _format_pending_effect(effect):
    if effect is None:
        return "-"
    kind = effect[0]
    actor = effect[1]
    if kind in ("attack", "skip", "shuffle", "see"):
        return f"{kind}:p{actor}"
    if kind == "favor":
        return f"Wunsch:p{actor}->p{effect[2]}"
    if kind == "favor_give":
        return f"Wunsch-give:p{effect[2]}->p{effect[1]}"
    if kind == "pair":
        return f"Pärchen:p{actor}->p{effect[2]}"
    if kind == "triple":
        return f"Drilling:p{actor}->p{effect[2]}:{CARD_LABEL[effect[3]]}"
    if kind == "five":
        return f"Fünfling:p{actor}:take:{CARD_LABEL[effect[2]]}"
    return str(effect)


def _parse_player(token):
    if not token.startswith("p") or token == "p":
        raise ValueError("bad player token")
    value = int(token[1:])
    if value < 0:
        raise ValueError("bad player token")
    return value


def _parse_pos(token):
    if not token.startswith("pos") or token == "pos":
        raise ValueError("bad position token")
    value = int(token[3:])
    if value < 0:
        raise ValueError("bad position token")
    return value


def _require_card(card):
    if card not in CARD_INDEX:
        raise ValueError("unknown card")
    return card


class Game:
    def __init__(self, num_players=2, start_player=0):
        if not 2 <= num_players <= 5:
            raise ValueError("rules allow 2-5 players")
        if not 0 <= start_player < num_players:
            raise ValueError("bad start player")
        self.num_players = num_players
        self.start_player = start_player

    def initial_state(self):
        counts = dict(BASE_COUNTS)
        counts[EXPLODING] = 0
        counts[DEFUSE] = 0
        hands = tuple(_sort_cards((DEFUSE,)) for _ in range(self.num_players))
        return GameState(
            num_players=self.num_players,
            phase="deal",
            hands=hands,
            alive=tuple(True for _ in range(self.num_players)),
            current=self.start_player,
            setup_counts=_counts_from_mapping(counts),
            seen_top=_empty_seen(self.num_players),
        )

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("deal", "build_deck", "shuffle", "steal"):
            return CHANCE
        if state.phase == "nope":
            return state.reaction_player
        return state.current

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []

        if state.phase == "deal":
            if state.deal_index >= state.num_players * 7:
                return []
            target = state.deal_index % state.num_players
            return [
                ("chance_deal", target, card)
                for card in CARD_ORDER
                if state.setup_counts[CARD_INDEX[card]] > 0
            ]

        if state.phase == "build_deck":
            return [
                ("chance_deck", card)
                for card in CARD_ORDER
                if state.setup_counts[CARD_INDEX[card]] > 0
            ]

        if state.phase == "shuffle":
            return [
                ("chance_shuffle", card)
                for card in CARD_ORDER
                if state.shuffle_counts[CARD_INDEX[card]] > 0
            ]

        if state.phase == "steal":
            if state.pending_steal is None:
                return []
            _, target = state.pending_steal
            return [("chance_steal", target, c) for c in _distinct_cards(state.hands[target])]

        if state.phase == "defuse_insert":
            return [("insert", pos) for pos in range(len(state.deck) + 1)]

        if state.phase == "favor_give":
            actor = state.pending_effect[1]
            target = state.current
            return [("give", actor, c) for c in _distinct_cards(state.hands[target])]

        if state.phase == "nope":
            actions = [("nope_pass",)]
            if self._can_play_nope(state):
                actions.append(("nope_play",))
            return actions

        if state.phase == "play":
            return self._legal_play_actions(state)

        return []

    def _legal_play_actions(self, state):
        p = state.current
        hand = state.hands[p]
        counts = Counter(hand)
        targets = [i for i, alive in enumerate(state.alive) if alive and i != p]
        actions = []

        if state.deck:
            actions.append(("pass",))

        for card in (ATTACK, SKIP, SHUFFLE, SEE_FUTURE):
            if counts[card] > 0:
                actions.append(("play", card))

        if counts[FAVOR] > 0:
            for t in targets:
                if len(state.hands[t]) > 0:
                    actions.append(("play", FAVOR, t))

        # Combination assumption: any hand-card title except Exploding Kitten.
        for card in HAND_CARD_ORDER:
            if counts[card] >= 2:
                for t in targets:
                    if len(state.hands[t]) > 0:
                        actions.append(("combo_pair", card, t))
            if counts[card] >= 3:
                for t in targets:
                    for wish in HAND_CARD_ORDER:
                        actions.append(("combo_triple", card, t, wish))

        distinct = [c for c in HAND_CARD_ORDER if counts[c] > 0]
        discard_distinct = _distinct_cards(state.discard)
        if len(distinct) >= 5 and discard_distinct:
            for combo in combinations(distinct, 5):
                for take in discard_distinct:
                    actions.append(("combo_five", tuple(combo), take))

        return actions

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action {action!r} in phase {state.phase}")
        state = replace(state, history=state.history + (self.action_to_name(action),))

        if state.phase == "deal":
            return self._apply_deal(state, action)
        if state.phase == "build_deck":
            return self._apply_build_deck(state, action)
        if state.phase == "shuffle":
            return self._apply_shuffle(state, action)
        if state.phase == "steal":
            return self._apply_chance_steal(state, action)
        if state.phase == "play":
            return self._apply_play(state, action)
        if state.phase == "nope":
            return self._apply_nope(state, action)
        if state.phase == "defuse_insert":
            return self._apply_insert(state, action)
        if state.phase == "favor_give":
            return self._apply_favor_give(state, action)
        raise ValueError("unknown phase")

    def _deck_defuses_for_setup(self):
        # Two-player variant: only 2 Entschärfung cards are shuffled into the deck.
        if self.num_players == 2:
            return 2
        return 6 - self.num_players

    def _kittens_for_setup(self):
        return self.num_players - 1

    def _apply_deal(self, state, action):
        _, target, card = action
        counts = _decrement_count(state.setup_counts, card)
        hands = _add_card_to_player(state.hands, target, card)
        deal_index = state.deal_index + 1
        state = replace(state, setup_counts=counts, hands=hands, deal_index=deal_index)

        if deal_index == state.num_players * 7:
            data = list(counts)
            data[CARD_INDEX[DEFUSE]] += self._deck_defuses_for_setup()
            data[CARD_INDEX[EXPLODING]] += self._kittens_for_setup()
            state = replace(state, phase="build_deck", setup_counts=tuple(data), build_deck=())
        return state

    def _apply_build_deck(self, state, action):
        _, card = action
        counts = _decrement_count(state.setup_counts, card)
        built = state.build_deck + (card,)
        state = replace(state, setup_counts=counts, build_deck=built)

        if _counts_total(counts) == 0:
            return replace(
                state,
                phase="play",
                deck=built,
                build_deck=(),
                current=self.start_player,
                turns_remaining=1,
            )
        return state

    def _apply_shuffle(self, state, action):
        _, card = action
        counts = _decrement_count(state.shuffle_counts, card)
        built = state.shuffle_build + (card,)
        state = replace(state, shuffle_counts=counts, shuffle_build=built)
        if _counts_total(counts) == 0:
            return replace(
                state,
                phase="play",
                deck=built,
                shuffle_build=(),
                current=state.current,
            )
        return state

    def _apply_chance_steal(self, state, action):
        actor, target = state.pending_steal
        _, action_target, card = action
        if action_target != target:
            raise ValueError("wrong steal target")
        hands = _remove_cards_from_player(state.hands, target, (card,))
        hands = _add_card_to_player(hands, actor, card)
        return replace(state, phase="play", current=actor, hands=hands, pending_steal=None)

    def _apply_play(self, state, action):
        kind = action[0]
        p = state.current

        if kind == "pass":
            return self._draw_for_turn(state)

        if kind == "play":
            card = action[1]
            hands = _remove_cards_from_player(state.hands, p, (card,))
            discard = state.discard + (card,)
            if card == ATTACK:
                effect = ("attack", p)
            elif card == SKIP:
                effect = ("skip", p)
            elif card == SHUFFLE:
                effect = ("shuffle", p)
            elif card == SEE_FUTURE:
                effect = ("see", p)
            elif card == FAVOR:
                effect = ("favor", p, action[2])
            else:
                raise ValueError("unsupported single card")
            return self._start_nope_or_resolve(
                replace(state, hands=hands, discard=discard, pending_effect=effect)
            )

        if kind == "combo_pair":
            _, card, target = action
            hands = _remove_cards_from_player(state.hands, p, (card, card))
            discard = state.discard + (card, card)
            effect = ("pair", p, target)
            return self._start_nope_or_resolve(
                replace(state, hands=hands, discard=discard, pending_effect=effect)
            )

        if kind == "combo_triple":
            _, card, target, wish = action
            hands = _remove_cards_from_player(state.hands, p, (card, card, card))
            discard = state.discard + (card, card, card)
            effect = ("triple", p, target, wish)
            return self._start_nope_or_resolve(
                replace(state, hands=hands, discard=discard, pending_effect=effect)
            )

        if kind == "combo_five":
            _, cards, take = action
            hands = _remove_cards_from_player(state.hands, p, cards)
            discard = state.discard + tuple(cards)
            effect = ("five", p, take)
            return self._start_nope_or_resolve(
                replace(state, hands=hands, discard=discard, pending_effect=effect)
            )

        raise ValueError("bad play action")

    def _can_play_nope(self, state):
        p = state.reaction_player
        if p < 0 or _hand_count(state.hands[p], NOPE) <= 0:
            return False
        if p == state.last_nope_player:
            return False
        # Base actor may not Nö! their own base action, but may Nö! a Nö!.
        if state.nope_count == 0 and state.pending_effect is not None:
            if p == state.pending_effect[1]:
                return False
        return True

    def _start_nope_or_resolve(self, state):
        effect = state.pending_effect
        actor = effect[1]
        has_responder = any(
            i != actor and alive and _hand_count(state.hands[i], NOPE) > 0
            for i, alive in enumerate(state.alive)
        )
        if not has_responder:
            clean = replace(state, pending_effect=None, phase="play", current=actor)
            return self._resolve_effect(clean, effect)

        return replace(
            state,
            phase="nope",
            reaction_player=_next_alive_after(state.alive, actor),
            last_nope_player=actor,
            nope_count=0,
            passes_since_nope=0,
        )

    def _apply_nope(self, state, action):
        p = state.reaction_player
        if action[0] == "nope_play":
            hands = _remove_cards_from_player(state.hands, p, (NOPE,))
            state = replace(
                state,
                hands=hands,
                discard=state.discard + (NOPE,),
                nope_count=state.nope_count + 1,
                last_nope_player=p,
                passes_since_nope=0,
                reaction_player=_next_alive_after(state.alive, p),
            )
            return state

        needed = max(0, _alive_count(state.alive) - 1)
        passes = state.passes_since_nope + 1
        if passes >= needed:
            effective = (state.nope_count % 2) == 0
            return self._finish_nope(state, effective)
        return replace(
            state,
            passes_since_nope=passes,
            reaction_player=_next_alive_after(state.alive, p),
        )

    def _finish_nope(self, state, effective):
        effect = state.pending_effect
        actor = effect[1]
        clean = replace(
            state,
            phase="play",
            current=actor,
            pending_effect=None,
            nope_count=0,
            last_nope_player=-1,
            reaction_player=-1,
            passes_since_nope=0,
        )
        if effective:
            return self._resolve_effect(clean, effect)
        return clean

    def _resolve_effect(self, state, effect):
        kind = effect[0]
        actor = effect[1]
        state = replace(state, phase="play", current=actor, pending_effect=None)

        if kind == "attack":
            if _alive_count(state.alive) <= 1:
                return self._make_terminal(state)
            nxt = _next_alive_after(state.alive, actor)
            return replace(state, current=nxt, turns_remaining=2)

        if kind == "skip":
            return self._complete_one_turn(state)

        if kind == "shuffle":
            counts = _counts_from_cards(state.deck)
            if _counts_total(counts) == 0:
                return state
            return replace(
                state,
                phase="shuffle",
                deck=(),
                shuffle_counts=counts,
                shuffle_build=(),
                seen_top=_empty_seen(state.num_players),
            )

        if kind == "see":
            seen = list(state.seen_top)
            seen[actor] = state.deck[:3]
            return replace(state, seen_top=tuple(seen))

        if kind == "favor":
            target = effect[2]
            if not state.alive[target] or not state.hands[target]:
                return state
            return replace(state, phase="favor_give", current=target, pending_effect=("favor_give", actor, target))

        if kind == "pair":
            target = effect[2]
            if not state.alive[target] or not state.hands[target]:
                return state
            return replace(state, phase="steal", current=actor, pending_steal=(actor, target))

        if kind == "triple":
            target, wish = effect[2], effect[3]
            if state.alive[target] and _hand_count(state.hands[target], wish) > 0:
                hands = _remove_cards_from_player(state.hands, target, (wish,))
                hands = _add_card_to_player(hands, actor, wish)
                state = replace(state, hands=hands)
            return state

        if kind == "five":
            take = effect[2]
            if take in state.discard:
                discard = _remove_one_from_discard(state.discard, take)
                hands = _add_card_to_player(state.hands, actor, take)
                state = replace(state, discard=discard, hands=hands)
            return state

        raise ValueError("unknown effect")

    def _apply_favor_give(self, state, action):
        _, actor, card = action
        target = state.current
        hands = _remove_cards_from_player(state.hands, target, (card,))
        hands = _add_card_to_player(hands, actor, card)
        return replace(state, phase="play", current=actor, hands=hands, pending_effect=None)

    def _draw_for_turn(self, state):
        p = state.current
        card = state.deck[0]
        state = replace(state, deck=state.deck[1:], seen_top=_empty_seen(state.num_players))

        if card == EXPLODING:
            if _hand_count(state.hands[p], DEFUSE) > 0:
                # Assumption: a player with Entschärfung uses it automatically.
                hands = _remove_cards_from_player(state.hands, p, (DEFUSE,))
                return replace(
                    state,
                    phase="defuse_insert",
                    current=p,
                    hands=hands,
                    discard=state.discard + (DEFUSE,),
                )

            hands_list = list(state.hands)
            dead_cards = hands_list[p]
            hands_list[p] = ()
            alive = list(state.alive)
            alive[p] = False
            state = replace(
                state,
                hands=tuple(hands_list),
                alive=tuple(alive),
                discard=state.discard + dead_cards + (EXPLODING,),
            )
            if _alive_count(state.alive) <= 1:
                return self._make_terminal(state)
            return replace(state, phase="play", current=_next_alive_after(state.alive, p), turns_remaining=1)

        hands = _add_card_to_player(state.hands, p, card)
        return self._complete_one_turn(replace(state, hands=hands))

    def _apply_insert(self, state, action):
        _, pos = action
        deck = state.deck[:pos] + (EXPLODING,) + state.deck[pos:]
        state = replace(state, deck=deck, phase="play", seen_top=_empty_seen(state.num_players))
        return self._complete_one_turn(state)

    def _complete_one_turn(self, state):
        if _alive_count(state.alive) <= 1:
            return self._make_terminal(state)
        p = state.current
        remaining = state.turns_remaining - 1
        if remaining > 0 and state.alive[p]:
            return replace(state, phase="play", current=p, turns_remaining=remaining)
        nxt = _next_alive_after(state.alive, p)
        return replace(state, phase="play", current=nxt, turns_remaining=1)

    def _make_terminal(self, state):
        return replace(
            state,
            phase="terminal",
            current=TERMINAL,
            turns_remaining=0,
            pending_effect=None,
            pending_steal=None,
            reaction_player=-1,
        )

    def is_terminal(self, state):
        return state.phase == "terminal"

    def returns(self, state):
        if not self.is_terminal(state):
            return [0.0 for _ in range(state.num_players)]
        alive = [i for i, a in enumerate(state.alive) if a]
        if len(alive) == 1:
            winner = alive[0]
            return [1.0 if i == winner else 0.0 for i in range(state.num_players)]
        return [0.0 for _ in range(state.num_players)]

    def chance_outcomes(self, state):
        if self.current_player(state) != CHANCE:
            return []

        if state.phase == "deal":
            total = _counts_total(state.setup_counts)
            return [(a, state.setup_counts[CARD_INDEX[a[2]]] / total) for a in self.legal_actions(state)]

        if state.phase == "build_deck":
            total = _counts_total(state.setup_counts)
            return [(a, state.setup_counts[CARD_INDEX[a[1]]] / total) for a in self.legal_actions(state)]

        if state.phase == "shuffle":
            total = _counts_total(state.shuffle_counts)
            return [(a, state.shuffle_counts[CARD_INDEX[a[1]]] / total) for a in self.legal_actions(state)]

        if state.phase == "steal":
            actor, target = state.pending_steal
            total = len(state.hands[target])
            counts = Counter(state.hands[target])
            return [(a, counts[a[2]] / total) for a in self.legal_actions(state)]

        return []

    def information_state(self, state, player):
        if not 0 <= player < state.num_players:
            raise ValueError("bad player")

        cp = self.current_player(state)
        cp_s = "TERMINAL" if cp == TERMINAL else "CHANCE" if cp == CHANCE else f"p{cp}"
        alive_s = ",".join(f"p{i}" for i, a in enumerate(state.alive) if a) or "-"

        if state.phase == "shuffle":
            deck_size = len(state.shuffle_build) + _counts_total(state.shuffle_counts)
        elif state.phase == "build_deck":
            deck_size = len(state.build_deck) + _counts_total(state.setup_counts)
        else:
            deck_size = len(state.deck)

        others = ";".join(
            f"p{i}:{len(state.hands[i])}"
            for i in range(state.num_players)
            if i != player
        )
        seen = state.seen_top[player] if player < len(state.seen_top) else ()

        return (
            f"player=p{player}\n"
            f"phase={state.phase} current={cp_s} turns={state.turns_remaining} alive={alive_s}\n"
            f"my_hand={_format_multiset(state.hands[player])}\n"
            f"other_hand_sizes={{{others}}}\n"
            f"deck_size={deck_size}\n"
            f"discard={_format_ordered(state.discard)}\n"
            f"seen_top={_format_ordered(seen)}\n"
            f"pending={_format_pending_effect(state.pending_effect)}"
        )

    def render(self, state):
        cp = self.current_player(state)
        cp_s = "TERMINAL" if cp == TERMINAL else "CHANCE" if cp == CHANCE else f"p{cp}"
        alive_s = ",".join(f"p{i}" for i, a in enumerate(state.alive) if a) or "-"

        lines = [
            f"phase={state.phase} current={cp_s} turns={state.turns_remaining} alive={alive_s}",
            "hands " + " | ".join(f"p{i}={_format_multiset(h)}" for i, h in enumerate(state.hands)),
            f"deck(n={len(state.deck)})={_format_ordered(state.deck)}",
            f"discard={_format_ordered(state.discard)}",
        ]

        if state.phase in ("deal", "build_deck"):
            lines.append(
                f"setup_counts={_format_counts_tuple(state.setup_counts)} "
                f"deal_index={state.deal_index} build={_format_ordered(state.build_deck)}"
            )

        if state.phase == "shuffle":
            lines.append(
                f"shuffle_counts={_format_counts_tuple(state.shuffle_counts)} "
                f"shuffle_build={_format_ordered(state.shuffle_build)}"
            )

        if any(state.seen_top):
            lines.append("seen " + " | ".join(f"p{i}={_format_ordered(s)}" for i, s in enumerate(state.seen_top)))

        if state.pending_effect is not None:
            lines.append(f"pending={_format_pending_effect(state.pending_effect)}")
        if state.pending_steal is not None:
            lines.append(f"pending_steal=p{state.pending_steal[0]}<-p{state.pending_steal[1]}")

        return "\n".join(lines)

    def action_to_name(self, action):
        kind = action[0]

        if kind == "pass":
            return "pass"
        if kind == "play":
            if len(action) == 2:
                return f"play:{action[1]}"
            return f"play:{action[1]}:target:p{action[2]}"
        if kind == "combo_pair":
            return f"combo:pair:{action[1]}:target:p{action[2]}"
        if kind == "combo_triple":
            return f"combo:triple:{action[1]}:target:p{action[2]}:wish:{action[3]}"
        if kind == "combo_five":
            return f"combo:five:{'+'.join(action[1])}:take:{action[2]}"
        if kind == "nope_pass":
            return "nope:pass"
        if kind == "nope_play":
            return "nope:play"
        if kind == "insert":
            return f"insert:{EXPLODING}:pos{action[1]}"
        if kind == "give":
            return f"give:{action[2]}:to:p{action[1]}"
        if kind == "chance_deal":
            return f"chance:deal:p{action[1]}:{action[2]}"
        if kind == "chance_deck":
            return f"chance:setup-deck:{action[1]}"
        if kind == "chance_shuffle":
            return f"chance:shuffle:{action[1]}"
        if kind == "chance_steal":
            return f"chance:steal:p{action[1]}:{action[2]}"
        raise ValueError("unknown action")

    def name_to_action(self, name):
        if name == "pass":
            return ("pass",)
        if name == "nope:pass":
            return ("nope_pass",)
        if name == "nope:play":
            return ("nope_play",)

        parts = name.split(":")
        if parts[0] == "play":
            card = _require_card(parts[1])
            if len(parts) == 2:
                return ("play", card)
            if len(parts) == 4 and parts[2] == "target":
                return ("play", card, _parse_player(parts[3]))

        if parts[0] == "combo":
            if parts[1] == "pair" and len(parts) == 5 and parts[3] == "target":
                return ("combo_pair", _require_card(parts[2]), _parse_player(parts[4]))
            if parts[1] == "triple" and len(parts) == 7 and parts[3] == "target" and parts[5] == "wish":
                return ("combo_triple", _require_card(parts[2]), _parse_player(parts[4]), _require_card(parts[6]))
            if parts[1] == "five" and len(parts) == 5 and parts[3] == "take":
                cards = tuple(_require_card(c) for c in parts[2].split("+") if c)
                return ("combo_five", cards, _require_card(parts[4]))

        if parts[0] == "insert" and len(parts) == 3:
            return ("insert", _parse_pos(parts[2]))

        if parts[0] == "give" and len(parts) == 4 and parts[2] == "to":
            return ("give", _parse_player(parts[3]), _require_card(parts[1]))

        if parts[0] == "chance":
            if parts[1] == "deal" and len(parts) == 4:
                return ("chance_deal", _parse_player(parts[2]), _require_card(parts[3]))
            if parts[1] == "setup-deck" and len(parts) == 3:
                return ("chance_deck", _require_card(parts[2]))
            if parts[1] == "shuffle" and len(parts) == 3:
                return ("chance_shuffle", _require_card(parts[2]))
            if parts[1] == "steal" and len(parts) == 4:
                return ("chance_steal", _parse_player(parts[2]), _require_card(parts[3]))

        raise ValueError("cannot parse action name")
```