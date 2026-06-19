from dataclasses import dataclass
from typing import List, Optional, Tuple

WHITE = 0
BLACK = 1
PLAYERS = (WHITE, BLACK)
PLAYER_NAMES = {WHITE: "white", BLACK: "black"}

FILES = "abcdefgh"
RANKS = "12345678"

KING = "K"      # Koenig
QUEEN = "D"     # Dame
ROOK = "T"      # Turm
BISHOP = "L"    # Laeufer
KNIGHT = "S"    # Springer
PAWN = "B"      # Bauer

PROMOTION_PIECES = (QUEEN, ROOK, BISHOP, KNIGHT, KING)

PIECE_NAMES = {
    KING: "Koenig",
    QUEEN: "Dame",
    ROOK: "Turm",
    BISHOP: "Laeufer",
    KNIGHT: "Springer",
    PAWN: "Bauer",
}
PIECE_FROM_NAME = {v: k for k, v in PIECE_NAMES.items()}


@dataclass(frozen=True)
class Action:
    kind: str  # "move", "capture", or "en_passant"
    source: str
    target: str
    promotion: Optional[str] = None


@dataclass(frozen=True)
class GameState:
    board: Tuple[Optional[str], ...]
    to_move: int
    en_passant_target: Optional[str] = None
    en_passant_capture_square: Optional[str] = None
    winner: Optional[int] = None
    draw: bool = False


def square_to_index(square: str) -> int:
    file_i = FILES.index(square[0])
    rank_i = RANKS.index(square[1])
    return rank_i * 8 + file_i


def index_to_square(index: int) -> str:
    return FILES[index % 8] + RANKS[index // 8]


def on_board(file_i: int, rank_i: int) -> bool:
    return 0 <= file_i < 8 and 0 <= rank_i < 8


def make_piece(player: int, kind: str) -> str:
    return ("w" if player == WHITE else "b") + kind


def piece_owner(piece: str) -> int:
    return WHITE if piece[0] == "w" else BLACK


def piece_kind(piece: str) -> str:
    return piece[1]


class Game:
    def initial_state(self) -> GameState:
        board: List[Optional[str]] = [None] * 64

        back_rank = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]

        for file_i, kind in enumerate(back_rank):
            board[file_i] = make_piece(WHITE, kind)          # rank 1
            board[56 + file_i] = make_piece(BLACK, kind)    # rank 8

        for file_i in range(8):
            board[8 + file_i] = make_piece(WHITE, PAWN)     # rank 2
            board[48 + file_i] = make_piece(BLACK, PAWN)    # rank 7

        return GameState(tuple(board), WHITE)

    def current_player(self, state: GameState) -> Optional[int]:
        return None if self.is_terminal(state) else state.to_move

    def legal_actions(self, state: GameState) -> List[Action]:
        terminal, _ = self._terminal_outcome(state)
        if terminal:
            return []
        return self._legal_actions_no_terminal(state)

    def apply_action(self, state: GameState, action) -> GameState:
        if isinstance(action, str):
            action = self.name_to_action(action)

        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError("illegal action: " + self.action_to_name(action))

        board = list(state.board)
        source_i = square_to_index(action.source)
        target_i = square_to_index(action.target)
        moving_piece = board[source_i]
        assert moving_piece is not None

        player = piece_owner(moving_piece)
        kind = piece_kind(moving_piece)

        board[source_i] = None

        if action.kind == "en_passant":
            # The captured pawn is not on the landing square.
            assert state.en_passant_capture_square is not None
            capture_i = square_to_index(state.en_passant_capture_square)
            board[capture_i] = None

        new_kind = action.promotion if action.promotion is not None else kind
        board[target_i] = make_piece(player, new_kind)

        new_ep_target = None
        new_ep_capture_square = None

        if kind == PAWN and action.kind == "move":
            src_rank = RANKS.index(action.source[1])
            tgt_rank = RANKS.index(action.target[1])
            if abs(tgt_rank - src_rank) == 2:
                mid_rank = (src_rank + tgt_rank) // 2
                new_ep_target = action.source[0] + RANKS[mid_rank]
                new_ep_capture_square = action.target

        new_board = tuple(board)

        no_piece_winner = self._winner_by_no_pieces(new_board)
        if no_piece_winner is not None:
            return GameState(
                new_board,
                state.to_move,
                new_ep_target,
                new_ep_capture_square,
                winner=no_piece_winner,
            )

        next_player = BLACK if state.to_move == WHITE else WHITE
        next_state = GameState(new_board, next_player, new_ep_target, new_ep_capture_square)

        # Zugunfaehigkeit: the side to move with no legal move wins immediately.
        if not self._legal_actions_no_terminal(next_state):
            return GameState(
                new_board,
                next_player,
                new_ep_target,
                new_ep_capture_square,
                winner=next_player,
            )

        return next_state

    def is_terminal(self, state: GameState) -> bool:
        terminal, _ = self._terminal_outcome(state)
        return terminal

    def returns(self, state: GameState) -> List[float]:
        terminal, winner = self._terminal_outcome(state)
        if not terminal or winner is None:
            return [0.0, 0.0]
        return [1.0 if player == winner else -1.0 for player in PLAYERS]

    def render(self, state: GameState) -> str:
        terminal, winner = self._terminal_outcome(state)
        winner_text = "-" if winner is None else PLAYER_NAMES[winner]

        lines = [
            "turn: " + PLAYER_NAMES[state.to_move],
            "terminal: " + ("yes" if terminal else "no"),
            "winner: " + winner_text,
            "en_passant: " + (state.en_passant_target or "-"),
        ]

        for rank_i in range(7, -1, -1):
            row = []
            for file_i in range(8):
                piece = state.board[rank_i * 8 + file_i]
                row.append(piece if piece is not None else "..")
            lines.append(str(rank_i + 1) + " " + " ".join(row))

        lines.append("  " + " ".join(FILES))
        return "\n".join(lines)

    def action_to_name(self, action: Action) -> str:
        if isinstance(action, str):
            action = self.name_to_action(action)

        if action.kind == "move":
            sep = "->"
        elif action.kind in ("capture", "en_passant"):
            sep = "x"
        else:
            raise ValueError("unknown action kind")

        name = f"{action.kind}:{action.source}{sep}{action.target}"
        if action.promotion is not None:
            name += "=" + PIECE_NAMES[action.promotion]
        return name

    def name_to_action(self, name: str) -> Action:
        for kind in ("en_passant", "capture", "move"):
            prefix = kind + ":"
            if name.startswith(prefix):
                body = name[len(prefix):]
                break
        else:
            raise ValueError("bad action name")

        promotion = None
        if "=" in body:
            body, promotion_name = body.rsplit("=", 1)
            if promotion_name not in PIECE_FROM_NAME:
                raise ValueError("bad promotion name")
            promotion = PIECE_FROM_NAME[promotion_name]

        sep = "->" if kind == "move" else "x"
        if sep not in body:
            raise ValueError("bad action separator")

        source, target = body.split(sep, 1)
        if not self._is_square(source) or not self._is_square(target):
            raise ValueError("bad square")

        return Action(kind, source, target, promotion)

    def _is_square(self, square: str) -> bool:
        return len(square) == 2 and square[0] in FILES and square[1] in RANKS

    def _terminal_outcome(self, state: GameState):
        if state.draw:
            return True, None
        if state.winner is not None:
            return True, state.winner

        winner = self._winner_by_no_pieces(state.board)
        if winner is not None:
            return True, winner

        if not self._legal_actions_no_terminal(state):
            return True, state.to_move

        return False, None

    def _winner_by_no_pieces(self, board: Tuple[Optional[str], ...]) -> Optional[int]:
        white_has = any(piece is not None and piece_owner(piece) == WHITE for piece in board)
        black_has = any(piece is not None and piece_owner(piece) == BLACK for piece in board)

        # This cannot arise through legal play here; treated as draw-like by returning None.
        if not white_has and not black_has:
            return None
        if not white_has:
            return WHITE
        if not black_has:
            return BLACK
        return None

    def _legal_actions_no_terminal(self, state: GameState) -> List[Action]:
        captures: List[Action] = []
        moves: List[Action] = []

        for index, piece in enumerate(state.board):
            if piece is None or piece_owner(piece) != state.to_move:
                continue
            piece_captures, piece_moves = self._piece_actions(state, index)
            captures.extend(piece_captures)
            moves.extend(piece_moves)

        chosen = captures if captures else moves
        return sorted(chosen, key=self.action_to_name)

    def _piece_actions(self, state: GameState, index: int):
        piece = state.board[index]
        assert piece is not None

        owner = piece_owner(piece)
        kind = piece_kind(piece)
        source = index_to_square(index)
        file_i = index % 8
        rank_i = index // 8

        captures: List[Action] = []
        moves: List[Action] = []

        if kind == KING:
            directions = [
                (-1, -1), (0, -1), (1, -1),
                (-1, 0),           (1, 0),
                (-1, 1),  (0, 1),  (1, 1),
            ]
            self._step_actions(state, owner, source, file_i, rank_i, directions, captures, moves)

        elif kind == QUEEN:
            self._slide_actions(
                state, owner, source, file_i, rank_i,
                [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)],
                captures, moves,
            )

        elif kind == ROOK:
            self._slide_actions(
                state, owner, source, file_i, rank_i,
                [(0, -1), (-1, 0), (1, 0), (0, 1)],
                captures, moves,
            )

        elif kind == BISHOP:
            self._slide_actions(
                state, owner, source, file_i, rank_i,
                [(-1, -1), (1, -1), (-1, 1), (1, 1)],
                captures, moves,
            )

        elif kind == KNIGHT:
            directions = [
                (-2, -1), (-1, -2), (1, -2), (2, -1),
                (-2, 1),  (-1, 2),  (1, 2),  (2, 1),
            ]
            self._step_actions(state, owner, source, file_i, rank_i, directions, captures, moves)

        elif kind == PAWN:
            self._pawn_actions(state, owner, source, file_i, rank_i, captures, moves)

        return captures, moves

    def _step_actions(self, state, owner, source, file_i, rank_i, directions, captures, moves):
        for df, dr in directions:
            nf = file_i + df
            nr = rank_i + dr
            if not on_board(nf, nr):
                continue

            target = FILES[nf] + RANKS[nr]
            occupant = state.board[nr * 8 + nf]

            if occupant is None:
                moves.append(Action("move", source, target))
            elif piece_owner(occupant) != owner:
                captures.append(Action("capture", source, target))

    def _slide_actions(self, state, owner, source, file_i, rank_i, directions, captures, moves):
        for df, dr in directions:
            nf = file_i + df
            nr = rank_i + dr

            while on_board(nf, nr):
                target = FILES[nf] + RANKS[nr]
                occupant = state.board[nr * 8 + nf]

                if occupant is None:
                    moves.append(Action("move", source, target))
                else:
                    if piece_owner(occupant) != owner:
                        captures.append(Action("capture", source, target))
                    break

                nf += df
                nr += dr

    def _pawn_actions(self, state, owner, source, file_i, rank_i, captures, moves):
        direction = 1 if owner == WHITE else -1
        start_rank = 1 if owner == WHITE else 6
        promotion_rank = 7 if owner == WHITE else 0

        # Non-capturing one-step move.
        one_rank = rank_i + direction
        if on_board(file_i, one_rank):
            one_index = one_rank * 8 + file_i
            if state.board[one_index] is None:
                target = FILES[file_i] + RANKS[one_rank]
                self._add_with_promotion("move", source, target, one_rank == promotion_rank, moves)

                # Two-step move from the starting rank, if both squares are free.
                two_rank = rank_i + 2 * direction
                if rank_i == start_rank and on_board(file_i, two_rank):
                    two_index = two_rank * 8 + file_i
                    if state.board[two_index] is None:
                        moves.append(Action("move", source, FILES[file_i] + RANKS[two_rank]))

        # Diagonal captures, including en passant.
        for df in (-1, 1):
            nf = file_i + df
            nr = rank_i + direction
            if not on_board(nf, nr):
                continue

            target = FILES[nf] + RANKS[nr]
            target_index = nr * 8 + nf
            occupant = state.board[target_index]

            if occupant is not None and piece_owner(occupant) != owner:
                self._add_with_promotion("capture", source, target, nr == promotion_rank, captures)

            if (
                state.en_passant_target == target
                and occupant is None
                and state.en_passant_capture_square is not None
            ):
                capture_i = square_to_index(state.en_passant_capture_square)
                captured = state.board[capture_i]
                if captured is not None and piece_owner(captured) != owner and piece_kind(captured) == PAWN:
                    captures.append(Action("en_passant", source, target))

    def _add_with_promotion(self, kind, source, target, promotes, actions):
        if promotes:
            for promotion in PROMOTION_PIECES:
                actions.append(Action(kind, source, target, promotion))
        else:
            actions.append(Action(kind, source, target))
