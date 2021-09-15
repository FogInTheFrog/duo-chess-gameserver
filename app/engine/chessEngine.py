# Structure responsible for keeping game instance states: position, moves, etc

from enum import Enum
from typing import List, Tuple
import copy


class Column(Enum):
    A = 0
    B = 1
    C = 2
    D = 3
    E = 4
    F = 5
    G = 6
    H = 7


COLUMN = {
    'A': 'a',
    'B': 'b',
    'C': 'c',
    'D': 'd',
    'E': 'e',
    'F': 'f',
    'G': 'g',
    'H': 'h'
}

COLUMN_NUM_TO_LITERAL = {
    0: 'a',
    1: 'b',
    2: 'c',
    3: 'd',
    4: 'e',
    5: 'f',
    6: 'g',
    7: 'h'
}

COLUMN_LITERAL_TO_NUM = {
    'a': 0,
    'b': 1,
    'c': 2,
    'd': 3,
    'e': 4,
    'f': 5,
    'g': 6,
    'h': 7
}


class PieceBoardRepr(Enum):
    e = " "
    p = "p"
    n = "n"
    b = "b"
    r = "r"
    q = "q"
    k = "k"
    P = "P"
    N = "N"
    B = "B"
    R = "R"
    Q = "Q"
    K = "K"


WHITE_PIECES = {
    'P': "white pawn",
    'N': "white knight",
    'B': "white bishop",
    'R': "white rook",
    'Q': "white queen",
    'K': "white king"
}

BLACK_PIECES = {
    'p': "black pawn",
    'n': "black knight",
    'b': "black bishop",
    'r': "black rook",
    'q': "black queen",
    'k': "black king"
}

PIECES = {
    'e': "empty square"
}
PIECES.update(BLACK_PIECES)
PIECES.update(WHITE_PIECES)


class Colors(Enum):
    white = int(0)
    black = int(1)
    neutral = int(404)

# CONSTANTS

PIECES_NAMES_TO_SHORTCUTS = {v: k for k, v in PIECES.items()}
START_POSITION_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

DIAGONAL_MOVES_LIST = [[(k, k) for k in range(1, 8)], [(-k, k) for k in range(1, 8)],
                       [(k, -k) for k in range(1, 8)], [(-k, -k) for k in range(1, 8)]]

SIDE_MOVES_LIST = [[(0, k) for k in range(1, 8)], [(0, -k) for k in range(1, 8)],
                   [(k, 0) for k in range(1, 8)], [(-k, 0) for k in range(1, 8)]]

KNIGHT_MOVES_LIST = [[(1, 2)], [(1, -2)], [(-1, 2)], [(-1, -2)],
                     [(2, 1)], [(-2, 1)], [(2, -1)], [(-2, -1)]]

# King moves list doesn't include castling
KING_MOVES_LIST = []
for c in range(-1, 2):
    for r in range(-1, 2):
        if abs(c) + abs(r) > 0:
            KING_MOVES_LIST.append([(c, r)])

SHORT_CASTLE_MOVES_LIST = [[(1, 0), (2, 0)]]
LONG_CASTLE_MOVES_LIST = [[(-1, 0), (-2, 0)]]

WHITE_PAWN_ONE_MOVES_LIST = [[(0, 1)]]
BLACK_PAWN_ONE_MOVES_LIST = [[(0, -1)]]
WHITE_PAWN_TWO_MOVES_LIST = [[(0, 1), (0, 2)]]
BLACK_PAWN_TWO_MOVES_LIST = [[(0, -1), (0, -2)]]
WHITE_PAWN_TAKES_MOVES_LIST = [[(1, 1)], [(-1, 1)]]
BLACK_PAWN_TAKES_MOVES_LIST = [[(1, -1)], [(-1, -1)]]
# special moves that need extra check (castle, pawn 2 fields, pawn takes, en passant, promotion)

MOVE_NOT_FOUND = -1
ILLEGAL_EN_PASSANT = ('-', '-')
WHITE_KING_START_POSITION = (4, 0)
BLACK_KING_START_POSITION = (4, 7)
WHITE_PAWN_START_ROW = 1
BLACK_PAWN_START_ROW = 6
WHITE_KING_AFTER_SHORT_CASTLE_POSITION = (6, 0)
BLACK_KING_AFTER_SHORT_CASTLE_POSITION = (6, 7)
WHITE_KING_AFTER_LONG_CASTLE_POSITION = (2, 0)
BLACK_KING_AFTER_LONG_CASTLE_POSITION = (2, 7)


def get_id_of_move_in_moves_list(diff: (int, int), moves_list) -> int:
    pos = MOVE_NOT_FOUND
    for i in range(len(moves_list)):
        if diff == moves_list[i]:
            pos = i
            break
    return pos


def check_legality_on_moves_list(start: (int, int), pos: int, move_diff_list, board) -> bool:
    is_move_on_list = True
    for i in range(pos):
        new_col = start[0] + move_diff_list[i][0]
        new_row = start[1] + move_diff_list[i][1]
        piece_on_new_field = board[new_col][new_row]
        if piece_on_new_field != PieceBoardRepr.e:
            is_move_on_list = False
            break
    return is_move_on_list


def get_start_end_diff(start: (int, int), end: (int, int)) -> (int, int):
    return end[0] - start[0], end[1] - start[1]


# when field on board is empty (there is no piece)
def is_piece_empty(piece):
    return piece == PieceBoardRepr.e


def is_rook(piece):
    return piece == PieceBoardRepr.R or piece == PieceBoardRepr.r


def is_pawn(piece):
    return piece == PieceBoardRepr.P or piece == PieceBoardRepr.p


def is_bishop(piece):
    return piece == PieceBoardRepr.B or piece == PieceBoardRepr.b


def is_knight(piece):
    return piece == PieceBoardRepr.N or piece == PieceBoardRepr.n


def is_queen(piece):
    return piece == PieceBoardRepr.Q or piece == PieceBoardRepr.q


def is_king(piece):
    return piece == PieceBoardRepr.K or piece == PieceBoardRepr.k


def get_color_of_piece(piece) -> Colors:
    if piece.name in BLACK_PIECES:
        return Colors.black
    elif piece.name in WHITE_PIECES:
        return Colors.white
    else:
        return Colors.neutral


# Checks whether during the move we are not trying to capture our own piece
def validate_capturing_our_own_piece(start_piece: PieceBoardRepr, end_piece: PieceBoardRepr):
    start_piece_color = get_color_of_piece(start_piece)
    return start_piece_color != get_color_of_piece(end_piece) and start_piece_color != Colors.neutral


# Checks whether during the move we are capturing piece of opposite color
def is_capturing_opposite_piece(start_piece: PieceBoardRepr, end_piece: PieceBoardRepr):
    start_piece_color = get_color_of_piece(start_piece)
    end_piece_color = get_color_of_piece(end_piece)
    return start_piece_color != end_piece_color and end_piece_color != Colors.neutral \
        and start_piece_color != Colors.neutral


# Returns position of where opponent's pawn should be to perform en_passant
def get_opponents_pawn_position_while_enpassant(start: (int, int), end: (int, int)) -> (int, int):
    return end[0], start[1]


def board_coordinates_to_literal(cord: (int, int)):
    return COLUMN_NUM_TO_LITERAL[cord[0]] + str((int(cord[1]) + 1))


def is_square_on_board(cord: (int, int)):
    return 0 <= cord[0] < 8 and 0 <= cord[1] < 8


# TODO: Extract some code
def is_square_under_attack(cord: (int, int), board, square_owner_color: Colors) -> bool:
    for move_list in SIDE_MOVES_LIST:
        for move in move_list:
            new_col = cord[0] + move[0]
            new_row = cord[1] + move[1]
            if not is_square_on_board((new_col, new_row)):
                break

            piece = board[new_col][new_row]
            piece_color = get_color_of_piece(piece)

            if piece_color == square_owner_color:
                break
            elif piece_color == Colors.neutral:
                continue
            else:
                if is_rook(piece) or is_queen(piece):
                    return True
                elif is_king(piece) and abs(cord[0] - new_col) <= 1 and abs(cord[1] - new_row) <= 1:
                    return True
                break

    for move_list in DIAGONAL_MOVES_LIST:
        for move in move_list:
            new_col = cord[0] + move[0]
            new_row = cord[1] + move[1]
            if not is_square_on_board((new_col, new_row)):
                break

            piece = board[new_col][new_row]
            piece_color = get_color_of_piece(piece)

            if piece_color == square_owner_color:
                break
            elif piece_color == Colors.neutral:
                continue
            else:
                if is_bishop(piece) or is_queen(piece):
                    return True
                elif is_king(piece) and abs(cord[0] - new_col) <= 1 and abs(cord[1] - new_row) <= 1:
                    return True
                elif is_pawn(piece) and new_row == cord[1] + 1 - 2 * square_owner_color.value:
                    return True
                break

    # Is square attacked by knight?
    for move_list in KNIGHT_MOVES_LIST:
        for move in move_list:
            new_col = cord[0] + move[0]
            new_row = cord[1] + move[1]
            if not is_square_on_board((new_col, new_row)):
                break

            piece = board[new_col][new_row]
            piece_color = get_color_of_piece(piece)

            if piece_color == square_owner_color:
                break
            elif piece_color == Colors.neutral:
                continue
            else:
                if is_knight(piece):
                    return True
    return False


# Switches e.g. f3 -> 52
def literal_to_board_coordinates(literal: str) -> Tuple[int, int]:
    if len(literal) != 2:
        raise ValueError("Incorrect position length")
    return COLUMN_LITERAL_TO_NUM[literal[0]], int(literal[1]) - 1


def get_copy_of_modified_board_after_cord_changes(changes: List[Tuple[Tuple[int, int], PieceBoardRepr]], board):
    new_board = copy.deepcopy(board)
    for change in changes:
        cord = change[0]
        piece = change[1]
        new_board[cord[0]][cord[1]] = copy.deepcopy(piece)
    return new_board


def get_copy_of_modified_board_after_literal_changes(changes: List[Tuple[str, PieceBoardRepr]], board):
    new_board = copy.deepcopy(board)
    for change in changes:
        literal_cord = change[0]
        piece = change[1]
        cord = literal_to_board_coordinates(literal_cord)
        new_board[cord[0]][cord[1]] = piece
    return new_board


def get_piece_repr_from_board_cord(cords: (int, int), board) -> PieceBoardRepr:
    return board[cords[0]][cords[1]]


def get_piece_repr_from_board_literal(literal: str, board) -> PieceBoardRepr:
    cords = literal_to_board_coordinates(literal)
    return get_piece_repr_from_board_cord(cords, board)


def get_copy_of_modified_board_after_move_literal(start: str, end: str, board):
    piece_moving = get_piece_repr_from_board_literal(start, board)
    change_list = [(start, PieceBoardRepr.e), (end, piece_moving)]
    return get_copy_of_modified_board_after_literal_changes(change_list, board)


def is_promotion(end: (int, int), piece_moving: PieceBoardRepr):
    if piece_moving == PieceBoardRepr.P and end[1] == 7:
        return True
    if piece_moving == PieceBoardRepr.p and end[1] == 0:
        return True
    return False


def get_copy_of_modified_board_after_move_cords(start: (int, int), end: (int, int), board):
    piece_moving = get_piece_repr_from_board_cord(start, board)
    change_list = [(start, PieceBoardRepr.e)]
    new_board = copy.deepcopy(board)

    if is_promotion(end, piece_moving):
        if get_color_of_piece(piece_moving) == Colors.white:
            change_list.append((end, PieceBoardRepr.Q))
        elif get_color_of_piece(piece_moving) == Colors.black:
            change_list.append((end, PieceBoardRepr.q))
    else:
        change_list.append((end, piece_moving))

    return get_copy_of_modified_board_after_cord_changes(change_list, new_board)


def get_king_cords_by_color(board, color: Colors) -> (int, int):
    if color == Colors.neutral:
        raise ValueError("Error while trying to find king position, King can be either black or white")

    for col in range(8):
        for row in range(8):
            piece = board[col][row]
            if is_king(piece) and get_color_of_piece(piece) == color:
                return col, row

    raise Exception("Unable to find king on board")


def will_our_king_be_in_check_after_move(start: (int, int), end: (int, int), board, color: Colors) -> bool:
    board_after_move = get_copy_of_modified_board_after_move_cords(start, end, board)
    king_cords = get_king_cords_by_color(board_after_move, color)
    return is_square_under_attack(king_cords, board_after_move, color)


class ResponseGameState:
    def __init__(self, board, legal_white_short_castle, legal_white_long_castle,
                 legal_black_short_castle, legal_black_long_castle, en_passant,
                 half_moves_since_capture):
        self.board = board
        self.legal_white_short_castle = legal_white_short_castle
        self.legal_white_long_castle = legal_white_long_castle
        self.legal_black_short_castle = legal_black_short_castle
        self.legal_black_long_castle = legal_black_long_castle
        self.en_passant = en_passant
        self.half_moves_since_capture = half_moves_since_capture


class GameState:
    def __init__(self):
        self.board = self.get_starting_position()
        self.color_to_move = Colors.white
        self.legal_white_short_castle = True
        self.legal_white_long_castle = True
        self.legal_black_short_castle = True
        self.legal_black_long_castle = True
        self.en_passant = ILLEGAL_EN_PASSANT
        self.half_moves_since_capture = 0
        self.full_moves = 1

    def load_position_from_fen(self, fen: str):
        self.board = self.get_board_from_fen(fen)

    # We assume that fen is correct
    def load_game_state_from_fen(self, fen: str):
        fen_params_list = fen.split()
        if fen_params_list.__len__() != 6:
            raise AttributeError("Wrong number of arguments in FEN")
        fen_board = fen_params_list[0]
        self.color_to_move = Colors.white if fen_params_list[1] == 'w' else Colors.black
        fen_possible_castles = fen_params_list[2]
        fen_enpassant = fen_params_list[3]
        fen_half_move_clock = fen_params_list[4]
        fen_full_move_number = fen_params_list[5]

        self.load_position_from_fen(fen_board)

        if 'Q' in fen_possible_castles:
            self.legal_white_long_castle = True
        if 'K' in fen_possible_castles:
            self.legal_white_short_castle = True
        if 'q' in fen_possible_castles:
            self.legal_black_long_castle = True
        if 'k' in fen_possible_castles:
            self.legal_black_short_castle = True

        if fen_enpassant != '-':
            self.en_passant = literal_to_board_coordinates(fen_enpassant)
        else:
            self.en_passant = ILLEGAL_EN_PASSANT

        self.half_moves_since_capture = int(fen_half_move_clock)
        self.full_moves = int(fen_full_move_number)
        return

    def position_to_fen(self):
        fen = ""
        for row in range(8):
            how_many_empty = 0
            for column in range(8):
                piece = self.get_piece_from_board((column, 7 - row))
                if piece == PieceBoardRepr.e:
                    how_many_empty += 1
                else:
                    if how_many_empty > 0:
                        fen += str(how_many_empty)
                        how_many_empty = 0
                    fen += piece.name
            if how_many_empty > 0:
                fen += str(how_many_empty)
            if row < 7:
                fen += '/'
        return fen

    def game_state_to_fen(self):
        # Board position
        fen = self.position_to_fen()
        fen += ' '

        # Active color
        if self.color_to_move == Colors.white:
            fen += 'w '
        else:
            fen += 'b '

        # Castling availability
        available_castlings = ""
        if self.legal_white_short_castle:
            available_castlings += 'K'
        if self.legal_white_long_castle:
            available_castlings += 'Q'
        if self.legal_black_short_castle:
            available_castlings += 'k'
        if self.legal_black_long_castle:
            available_castlings += 'q'

        if not available_castlings:
            available_castlings = '-'
        fen += available_castlings + ' '
        
        # En passant target square
        if self.en_passant == ILLEGAL_EN_PASSANT:
            fen += '- '
        else:
            en_passant_cords = board_coordinates_to_literal(self.en_passant)
            fen += str(en_passant_cords) + ' '

        # Halfmoves
        fen += str(self.half_moves_since_capture)
        fen += ' '

        # Fullmoves
        fen += str(self.full_moves)

        return fen

    # Checks whether move played is castling
    def is_castle(self, start: (int, int), end: (int, int), piece_color: Colors) -> bool:
        is_move_on_list = False
        start_end_diff = (end[0] - start[0], end[1] - start[1])
        is_king_in_check = is_square_under_attack(start, self.board, piece_color)

        # We can't castle while being in check
        if is_king_in_check:
            return False

        # Check whether move is short castle
        for move_diff_list in SHORT_CASTLE_MOVES_LIST:
            pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
            if pos != MOVE_NOT_FOUND:
                is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                break

        if is_move_on_list:
            if piece_color == Colors.white and self.legal_white_short_castle:
                return self.board[6][0] == PieceBoardRepr.e and self.board[5][0] == PieceBoardRepr.e \
                       and self.board[7][0] == PieceBoardRepr.R
            elif piece_color == Colors.black and self.legal_black_short_castle:
                return self.board[6][7] == PieceBoardRepr.e and self.board[5][7] == PieceBoardRepr.e \
                       and self.board[7][7] == PieceBoardRepr.r
            return False

        # Check whether move is long castle
        for move_diff_list in LONG_CASTLE_MOVES_LIST:
            pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
            if pos != MOVE_NOT_FOUND:
                is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                break

        if is_move_on_list:
            if piece_color == Colors.white and self.legal_white_long_castle:
                return self.board[1][0] == PieceBoardRepr.e and self.board[2][0] == PieceBoardRepr.e \
                       and self.board[3][0] == PieceBoardRepr.e and self.board[0][0] == PieceBoardRepr.R
            elif piece_color == Colors.black and self.legal_black_long_castle:
                return self.board[1][7] == PieceBoardRepr.e and self.board[2][7] == PieceBoardRepr.e \
                       and self.board[3][7] == PieceBoardRepr.e and self.board[0][7] == PieceBoardRepr.r
        return False

    def is_field_free(self, pos: (int, int)) -> bool:
        return self.board[pos[0]][pos[1]] == PieceBoardRepr.e

    def pawn_two_steps_legal(self, start: (int, int), end: (int, int), pawn_start_row: int) -> bool:
        return pawn_start_row == start[1] and self.is_field_free(end)

    def get_piece_from_board(self, position: (int, int)):
        return self.board[position[0]][position[1]]

    def get_players_squares_list(self, color: Colors):
        list_of_players_squares = []
        for col in range(8):
            for row in range(8):
                piece = self.board[col][row]
                if get_color_of_piece(piece) == color:
                    list_of_players_squares.append((col, row))
        return list_of_players_squares

    def is_stale_mated(self, color: Colors) -> bool:
        kings_cords = get_king_cords_by_color(self.board, color)
        under_check = is_square_under_attack(kings_cords, self.board, color)

        # If king is not under attack can't be mated
        if under_check:
            return False

        list_of_players_squares = self.get_players_squares_list(color)

        for square in list_of_players_squares:
            for col in range(8):
                for row in range(8):
                    target_square = (col, row)
                    if self.is_move_legal(square, target_square, True)[0] is True:
                        return False
        print("Player is stalemated", color.name)
        return True

    def is_mated(self, color: Colors) -> bool:
        kings_cords = get_king_cords_by_color(self.board, color)
        under_check = is_square_under_attack(kings_cords, self.board, color)

        # If king is not under attack can't be mated
        if not under_check:
            return False

        list_of_players_squares = self.get_players_squares_list(color)

        for square in list_of_players_squares:
            for col in range(8):
                for row in range(8):
                    target_square = (col, row)
                    if self.is_move_legal(square, target_square, ignore_color=True)[0] is True:
                        return False
        print("Player is mated", color.name)
        return True

    def is_move_legal(self, start: (int, int), end: (int, int), ignore_color=False) -> Tuple:
        piece = self.board[start[0]][start[1]]
        piece_color = get_color_of_piece(piece)

        # Check whether start and end are on board
        if not is_square_on_board(start) or not is_square_on_board(end):
            return False, None

        # Check whether start and end field are distinct cause such move is illegal
        if start == end:
            return False, None

        # Checks whether player is trying to move opponent's piece
        if ignore_color is not True:
            if not piece_color == self.color_to_move:
                return False, None

        # Check whether piece on target square is opposite's color or square is empty
        if not validate_capturing_our_own_piece(piece, self.board[end[0]][end[1]]):
            return False, None

        if will_our_king_be_in_check_after_move(start, end, self.board, piece_color):
            return False, None

        # Recognize piece
        # TODO: clean up this part
        if is_piece_empty(piece):
            return False, None

        elif is_pawn(piece):
            start_end_diff = get_start_end_diff(start, end)
            is_move_on_list = False

            pawn_one_moves_list = WHITE_PAWN_ONE_MOVES_LIST
            pawn_two_moves_list = WHITE_PAWN_TWO_MOVES_LIST
            pawn_takes_moves_list = WHITE_PAWN_TAKES_MOVES_LIST
            pawn_start_row = WHITE_PAWN_START_ROW
            if piece_color == Colors.black:
                pawn_one_moves_list = BLACK_PAWN_ONE_MOVES_LIST
                pawn_two_moves_list = BLACK_PAWN_TWO_MOVES_LIST
                pawn_takes_moves_list = BLACK_PAWN_TAKES_MOVES_LIST
                pawn_start_row = BLACK_PAWN_START_ROW

            # Check single front move
            for move_diff_list in pawn_one_moves_list:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = True
                    break
            if is_move_on_list:
                if self.is_field_free(end):
                    new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                    return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                                   self.legal_white_long_castle, self.legal_black_short_castle,
                                                   self.legal_black_long_castle, ILLEGAL_EN_PASSANT,
                                                   self.half_moves_since_capture + 1)
                return False, None

            # Check two steps pawn move
            for move_diff_list in pawn_two_moves_list:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break
            if is_move_on_list:
                if self.pawn_two_steps_legal(start, end, pawn_start_row):
                    new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                    return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                                   self.legal_white_long_castle, self.legal_black_short_castle,
                                                   self.legal_black_long_castle, (start[0], (start[1] + end[1]) // 2),
                                                   self.half_moves_since_capture + 1)
                return False, None

            # Check pawn takes and enpassant
            for move_diff_list in pawn_takes_moves_list:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break
            if is_move_on_list:
                piece_start = self.board[start[0]][start[1]]
                piece_end = self.board[end[0]][end[1]]
                if is_capturing_opposite_piece(piece_start, piece_end):
                    new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                    return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                                   self.legal_white_long_castle, self.legal_black_short_castle,
                                                   self.legal_black_long_castle, ILLEGAL_EN_PASSANT, 0)
                else:
                    # check for enpassant
                    enpassant_opponents_pawn_position = \
                        get_opponents_pawn_position_while_enpassant(start, end)
                    enpassant_piece = self.get_piece_from_board(enpassant_opponents_pawn_position)

                    if is_capturing_opposite_piece(piece_start, enpassant_piece) \
                            and self.is_field_free(end) and is_pawn(enpassant_piece) \
                            and self.en_passant == end:
                        tmp_new_board = get_copy_of_modified_board_after_move_cords(start,
                                                                                    enpassant_opponents_pawn_position,
                                                                                    self.board)
                        new_board = get_copy_of_modified_board_after_move_cords(enpassant_opponents_pawn_position,
                                                                                end, tmp_new_board)
                        return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                                       self.legal_white_long_castle, self.legal_black_short_castle,
                                                       self.legal_black_long_castle, ILLEGAL_EN_PASSANT, 0)
                    return False, None
            return False, None

        elif is_rook(piece):
            start_end_diff = get_start_end_diff(start, end)
            is_move_on_list = False

            # Check possible moves and whether fields between start and end are empty
            for move_diff_list in SIDE_MOVES_LIST:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break

            if is_move_on_list:
                new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                lwsc = False if start == (7, 0) else self.legal_white_short_castle
                lwlc = False if start == (0, 0) else self.legal_white_long_castle
                lbsc = False if start == (7, 7) else self.legal_black_short_castle
                lblc = False if start == (0, 7) else self.legal_black_long_castle
                piece_at_end = get_piece_repr_from_board_cord(end, self.board)
                hmsc = self.half_moves_since_capture + 1 if piece_at_end == PieceBoardRepr.e else 0
                return True, ResponseGameState(new_board, lwsc, lwlc, lbsc, lblc, ILLEGAL_EN_PASSANT, hmsc)
            return False, None

        elif is_knight(piece):
            start_end_diff = get_start_end_diff(start, end)
            is_move_on_list = False

            # Check possible moves and whether fields between start and end are empty
            for move_diff_list in KNIGHT_MOVES_LIST:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break

            if is_move_on_list:
                new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                piece_at_end = get_piece_repr_from_board_cord(end, self.board)
                hmsc = self.half_moves_since_capture + 1 if piece_at_end == PieceBoardRepr.e else 0
                return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                               self.legal_white_long_castle, self.legal_black_short_castle,
                                               self.legal_black_long_castle, ILLEGAL_EN_PASSANT, hmsc)

            return False, None

        elif is_bishop(piece):
            start_end_diff = get_start_end_diff(start, end)
            is_move_on_list = False

            # Check possible moves and whether fields between start and end are empty
            for move_diff_list in DIAGONAL_MOVES_LIST:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break

            if is_move_on_list:
                new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                piece_at_end = get_piece_repr_from_board_cord(end, self.board)
                hmsc = self.half_moves_since_capture + 1 if piece_at_end == PieceBoardRepr.e else 0
                return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                               self.legal_white_long_castle, self.legal_black_short_castle,
                                               self.legal_black_long_castle, ILLEGAL_EN_PASSANT, hmsc)

            return False, None

        elif is_queen(piece):
            start_end_diff = get_start_end_diff(start, end)
            is_move_on_list = False

            # Check possible moves and whether fields between start and end are empty
            for move_diff_list in DIAGONAL_MOVES_LIST:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break

            if not is_move_on_list:
                for move_diff_list in SIDE_MOVES_LIST:
                    pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                    if pos != MOVE_NOT_FOUND:
                        is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                        break

            if is_move_on_list:
                new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                piece_at_end = get_piece_repr_from_board_cord(end, self.board)
                hmsc = self.half_moves_since_capture + 1 if piece_at_end == PieceBoardRepr.e else 0
                return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                               self.legal_white_long_castle, self.legal_black_short_castle,
                                               self.legal_black_long_castle, ILLEGAL_EN_PASSANT, hmsc)

            return False, None

        elif is_king(piece):
            start_end_diff = get_start_end_diff(start, end)

            is_move_on_list = False

            # Check possible moves and whether fields between start and end are empty
            for move_diff_list in KING_MOVES_LIST:
                pos = get_id_of_move_in_moves_list(start_end_diff, move_diff_list)
                if pos != MOVE_NOT_FOUND:
                    is_move_on_list = check_legality_on_moves_list(start, pos, move_diff_list, self.board)
                    break

            if is_move_on_list:
                new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                piece_at_end = get_piece_repr_from_board_cord(end, self.board)
                hmsc = self.half_moves_since_capture + 1 if piece_at_end == PieceBoardRepr.e else 0
                if get_color_of_piece(piece) == Colors.white:
                    return True, ResponseGameState(new_board, False, False, self.legal_black_short_castle,
                                               self.legal_black_long_castle, ILLEGAL_EN_PASSANT, hmsc)
                return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                               self.legal_white_long_castle, False, False, ILLEGAL_EN_PASSANT, hmsc)
            else:
                if self.is_castle(start, end, piece_color):
                    rook_end_cords = (start[0] + end[0]) // 2, (start[1] + end[1]) // 2
                    rook_col = 0 if rook_end_cords[0] == 3 else 7
                    rook_start_cords = rook_col, rook_end_cords[1]
                    tmp_new_board = get_copy_of_modified_board_after_move_cords(start, end, self.board)
                    new_board = get_copy_of_modified_board_after_move_cords(rook_start_cords, rook_end_cords,
                                                                            tmp_new_board)
                    if get_color_of_piece(piece) == Colors.white:
                        return True, ResponseGameState(new_board, False, False, self.legal_black_short_castle,
                                                       self.legal_black_long_castle, ILLEGAL_EN_PASSANT,
                                                       self.half_moves_since_capture + 1)
                    return True, ResponseGameState(new_board, self.legal_white_short_castle,
                                                   self.legal_white_long_castle, False, False, ILLEGAL_EN_PASSANT,
                                                   self.half_moves_since_capture + 1)
            return False, None
        return False, None

    def move(self, start: (int, int), end: (int, int)):
        is_legal, response_game_state = self.is_move_legal(start, end)
        if is_legal is True:
            self.board = response_game_state.board
            self.color_to_move = Colors.black if self.color_to_move == Colors.white else Colors.white
            self.en_passant = response_game_state.en_passant
            self.legal_white_short_castle = response_game_state.legal_white_short_castle
            self.legal_white_long_castle = response_game_state.legal_white_long_castle
            self.legal_black_short_castle = response_game_state.legal_black_short_castle
            self.legal_black_long_castle = response_game_state.legal_black_long_castle
            self.half_moves_since_capture = response_game_state.half_moves_since_capture
            if self.color_to_move == Colors.white:
                self.full_moves += 1
            return True
        return False

    # Checks whether black or white is mated / stale mated.
    def is_game_over(self):
        if self.is_stale_mated(Colors.white) or self.is_stale_mated(Colors.black):
            return True
        if self.is_mated(Colors.white) or self.is_mated(Colors.black):
            return True
        return False

    def get_result(self) -> int:
        if self.is_mated(Colors.white):
            return 1
        elif self.is_mated(Colors.black):
            return 0
        elif self.is_game_over():
            return 2
        else:
            return 400

    @classmethod
    def get_empty_board(cls):
        board = []
        for i in range(8):
            board.append(8 * [PieceBoardRepr.e])
        return board

    @classmethod
    def get_starting_position(cls):
        board = GameState.get_board_from_fen(START_POSITION_FEN)
        return board

    @classmethod
    def board_to_string(cls, board):
        board_as_string = 28 * '-'
        board_as_string += '\n'
        for i in range(8):
            board_as_string += '| '
            for j in range(8):
                board_as_string += ' ' + board[j][8 - i - 1].value + ' '
            board_as_string += ' |\n'
        board_as_string += 28 * '-' + '\n'
        return board_as_string

    @classmethod
    def print_some_board(cls, board):
        print(GameState.board_to_string(board))

    def print_board(self):
        print(GameState.board_to_string(self.board))

    @classmethod
    def get_board_from_fen(cls, fen: str):
        board = GameState.get_empty_board()
        column = 0
        row = 7

        for x in fen:
            if x.isdigit():
                column += int(x)
            elif x == '/' and column == 8:
                row -= 1
                column = 0
            elif x in PIECES:
                board[column][row] = PieceBoardRepr(x)
                column += 1
            else:
                raise Exception("Incorrect Fen")

        if row != 0 and column != 8:
            raise Exception("Incorrect Fen")
        return board
