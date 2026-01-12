# solver.py
import time
from functools import lru_cache

def parse_clue_line(line):
    line = line.strip()
    if not line:
        return []
    parts = [p for p in line.replace(',', ' ').split() if p]
    return [int(p) for p in parts]

@lru_cache(maxsize=None)
def line_possibilities(length, clues):
    """Generate all possible binary tuples matching clues for a line of given length."""
    if not clues:
        return [tuple(0 for _ in range(length))]
    total_blocks = sum(clues)
    min_required = total_blocks + (len(clues) - 1)
    if min_required > length:
        return []
    results = []
    def build(pos, clue_index, acc):
        if clue_index == len(clues):
            if len(acc) <= length and all(v == 0 for v in acc[length:]):
                acc = acc[:length] if len(acc) >= length else acc + [0] * (length - len(acc))
                results.append(tuple(acc))
            return
        
        k = clues[clue_index]
        remaining_space = length - len(acc)
        remaining_blocks = sum(clues[clue_index:])
        min_spaces = len(clues) - clue_index - 1  # minimum spaces needed between remaining blocks
        
        max_pos = remaining_space - (remaining_blocks + min_spaces)
        for i in range(max_pos + 1):
            new_acc = acc + [0] * i + [1] * k
            if clue_index < len(clues) - 1:
                new_acc.append(0)  # mandatory space between blocks
            build(len(new_acc), clue_index + 1, new_acc)
            
    build(0, 0, [])
    return results

class NonogramSolver:
    """
    Nonogram solver with a backtracking search.

    solve(time_limit=None, allow_partial=True, debug=False)
      - allow_partial=True (default): do NOT fast-fail when a precomputed line
        has zero possibilities; the backtracker will still try (useful when
        inputs might be partial or clipped).
      - allow_partial=False: perform the static fast-fail check (old behavior).
      - debug=True prints a few helpful debug lines.
    """
    def __init__(self, row_clues, col_clues):
        self.R = len(row_clues)
        self.C = len(col_clues)
        self.row_clues = tuple(tuple(rc) for rc in row_clues)
        self.col_clues = tuple(tuple(cc) for cc in col_clues)

        self.row_poss = [line_possibilities(self.C, rc) for rc in self.row_clues]
        self.col_poss = [line_possibilities(self.R, cc) for cc in self.col_clues]
        # board: None unknown, 0 empty, 1 filled
        self.board = [[None] * self.C for _ in range(self.R)]

        # order rows by fewest possibilities (heuristic)
        self.row_order = sorted(range(self.R), key=lambda r: len(self.row_poss[r]))

        self.start_time = None
        self.nodes = 0

    def is_consistent_with_partial_row(self, r, candidate):
        for c in range(self.C):
            val = self.board[r][c]
            if val is not None and val != candidate[c]:
                return False
        return True

    def solve(self, time_limit=None, allow_partial=True, debug=True):
        """
        Backtracking solver. Returns True if solved (and self.board is filled),
        otherwise False.

        allow_partial:
          - True  -> skip the immediate 'if not poss: return False' static check
                     and let the backtracking try (useful for partial inputs).
          - False -> keep the static check (fast-fail if clues impossible for line length).
        """
        self.start_time = time.time()
        self.nodes = 0
        if debug:
            print(f"[solver] R={self.R}, C={self.C}")
            print(f"[solver] precomputed row possibilities counts: {[len(p) for p in self.row_poss]}")
            print(f"[solver] precomputed col possibilities counts: {[len(p) for p in self.col_poss]}")

        # Static impossibility check (only when allow_partial is False)
        if not allow_partial:
            for r, poss in enumerate(self.row_poss):
                if not poss:
                    if debug:
                        print(f"[solver] static fail: row {r} has 0 possibilities")
                    return False
            for c, poss in enumerate(self.col_poss):
                if not poss:
                    if debug:
                        print(f"[solver] static fail: col {c} has 0 possibilities")
                    return False

        # Work copies of column possibilities
        col_poss_lists = [list(poss) for poss in self.col_poss]

        def col_candidate_compatible_with_partial_col(c, col_candidate):
            for rr in range(self.R):
                b = self.board[rr][c]
                if b is not None and b != col_candidate[rr]:
                    return False
            return True

        def backtrack(idx):
            # timeout
            if time_limit and (time.time() - self.start_time) > time_limit:
                if debug: print("[solver] timeout in backtrack")
                return False
            if idx == len(self.row_order):
                if debug: print("[solver] all rows assigned -> success")
                return True

            self.nodes += 1
            r = self.row_order[idx]
            # Candidates filtered against current partial row
            candidates = [p for p in self.row_poss[r] if self.is_consistent_with_partial_row(r, p)]
            if not candidates:
                # No candidate fits current partial board -> backtrack
                if debug: print(f"[solver] row {r} has no candidates under current board -> backtrack")
                return False

            for candidate in candidates:
                # apply candidate to board row r
                old_row = list(self.board[r])
                for c in range(self.C):
                    self.board[r][c] = candidate[c]

                # Check columns still have at least one compatible possibility
                ok = True
                for c in range(self.C):
                    compatible = False
                    for col_candidate in col_poss_lists[c]:
                        if col_candidate_compatible_with_partial_col(c, col_candidate):
                            compatible = True
                            break
                    if not compatible:
                        ok = False
                        break

                if ok:
                    if backtrack(idx + 1):
                        return True

                # undo row
                for c in range(self.C):
                    self.board[r][c] = old_row[c]

            return False

        return backtrack(0)
