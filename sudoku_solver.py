import os
import time
import collections


class SudokuSolver(object):

    def __init__(self, use_naked_twins=False):
        self.digits = '123456789'
        self.rows = 'ABCDEFGHI'
        self.cols = self.digits
        self.squares = self._cross(self.rows, self.cols)
        self.unitlist = ([self._cross(self.rows, c) for c in self.cols] +
                         [self._cross(r, self.cols) for r in self.rows] +
                         [self._cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
        self.units = collections.OrderedDict((s, [u for u in self.unitlist if s in u])
                                             for s in self.squares)
        self.peers = collections.OrderedDict((s, set(sum(self.units[s], [])) - set([s]))
                                             for s in self.squares)

        self._use_naked_twins = use_naked_twins

    """
    Parsing sudoku grid
    """

    def grid_values(self, grid):
        """"Convert grid into a dict of {square: char} with '0' or '.' for empties."""
        chars = [c for c in grid if c in self.digits or c in '0.']
        assert len(chars) == 81
        return collections.OrderedDict(zip(self.squares, chars))

    def parse_grid(self, grid):
        """Convert grid to a dict of possible values, {square: digits}, or
        return False if a contradiction is detected."""
        # To start, every square can be any digit; then assign values from the grid.
        values = collections.OrderedDict((s, self.digits) for s in self.squares)
        for s, d in self.grid_values(grid).items():
            if d in self.digits and not self.assign(values, s, d):
                return False  # (Fail if we can't assign d to square s.)
        return values

    def display(self, values):
        """Display these values as a 2-D grid."""
        width = 1 + max(len(values[s]) for s in self.squares)
        line = '+'.join(['-' * (width * 3)] * 3)
        for r in self.rows:
            print(''.join(values[r + c].center(width) + ('|' if c in '36' else '') for c in self.cols))
            if r in 'CF': print(line)
        print()

    """
    Constraint propagation
    """

    def assign(self, values, s, d):
        """Eliminate all the other values (except d) from values[s] and propagate.
        Return values, except return False if a contradiction is detected."""
        values[s] = d
        if self.reduce_puzzle(values):
            return values
        else:
            return False

    def eliminate(self, values):
        """
        Iterate through all squares and every time 
           if there is a square with one value, 
           then eliminate this value from the peers

        input: sudoku in dictionary form
        output: resulting sudoku in dictionary form
        """
        for square in values:
            if len(values[square]) == 0:
                return False  # Contradiction: square is empty

            elif len(values[square]) == 1:
                for peer in self.peers[square]:
                    if values[square] in values[peer]:
                        values[peer] = values[peer].replace(values[square], '')

        return values

    def only_choice(self, values):
        """
        Iterate through all squares and every time
            if there is a square with a value that only fits in one square, 
            assign the value to this square

        input: sudoku in dictionary form
        output: resulting sudoku in dictionary form
        """
        for square in values:

            for unit in self.units[square]:

                for digit in self.digits:

                    dplaces = [s for s in unit if digit in values[s]]

                    if len(dplaces) == 0:
                        return False  # Contradiction: no place for this value

                    elif len(dplaces) == 1 and values[dplaces[0]] is not digit:
                        # d can only be in one place in unit; assign it there
                        if not self.assign(values, dplaces[0], digit):
                            return False

        return values

    def naked_twins(self, values):
        """
        eliminate values using the naked twins strategy

        input: A sudoku in dictionary form.
        output: The resulting sudoku in dictionary form.
        """
        for square in values:

            if len(values[square]) == 2:
                # search for naked twins
                for unit in self.units[square]:
                    for peer in unit:
                        if peer != square and values[peer] == values[square]:
                            # remove possibilities from other squares in unit
                            for p in unit:
                                if p != square and p != peer:
                                    values[p] = values[p].replace(values[square][0], '')
                                    values[p] = values[p].replace(values[square][1], '')

                                    if len(values[p]) == 0:
                                        return False

        return values

    def reduce_puzzle(self, values):
        """
        Solve sudoku using eliminate() and only_choice()

        input: sudoku in dictionary form
        output: resulting sudoku in dictionary form
        """
        if not self.eliminate(values):
            return False
        if self._use_naked_twins and not self.naked_twins(values):
            return False
        if not self.only_choice(values):
            return False
        else:
            return values

    """
    Solvers
    """

    def solve(self, grid):
        return self.search(self.parse_grid(grid))

    def search(self, values):
        """Using depth-first search and propagation, try all possible values."""
        if values is False:
            return False  # Failed earlier
        if all(len(values[s]) == 1 for s in self.squares):
            return values  # Solved!
        # Chose the unfilled square s with the fewest possibilities
        n, s = min((len(values[s]), s) for s in self.squares if len(values[s]) > 1)
        return self._some(self.search(self.assign(values.copy(), s, d)) for d in values[s])

    """
    Helpers
    """

    @staticmethod
    def _cross(A, B):
        """Cross product of elements in A and elements in B. Valid for strings."""
        return [a + b for a in A for b in B]

    @staticmethod
    def _some(seq):
        """Return some element of seq that is true."""
        for e in seq:
            if e:
                return e
        return False

    @staticmethod
    def from_file(filename, sep='\n'):
        """Parse a file into a list of strings, separated by sep."""
        with open(filename) as f:
            return f.read().strip().split(sep)

    def solve_all(self, grids):
        """Attempt to solve a sequence of grids. Report results.
        When showif is a number of seconds, display puzzles that take longer.
        When showif is None, don't display any puzzles."""

        time_list = list()
        for grid in grids:
            start = time.clock()
            _ = self.solve(grid)
            t = time.clock() - start
            print('Solved puzzle; took {0:.2f} second(s)'.format(t))
            time_list.append(t)


def main():
    sudoku_solver = SudokuSolver(use_naked_twins=False)

    grids_easy = sudoku_solver.from_file(os.path.join('grids', 'easy.txt'), sep='========')
    grids_hard = sudoku_solver.from_file(os.path.join('grids', 'hard.txt'))

    sudoku_solver.solve_all(grids_hard)


if __name__ == "__main__":
    main()