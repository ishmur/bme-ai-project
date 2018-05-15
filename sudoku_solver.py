import os
import time
import collections
import copy
import matplotlib.pyplot as plt


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
        """Display sudoku in dictionary form as a 2-D grid."""
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
        """Solve sudoku grid."""
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

    def solve_all(self, grids, label=''):
        """Attempt to solve a sequence of grids"""

        time_list = list()
        for grid in grids:
            start = time.clock()
            _ = self.solve(grid)
            t = time.clock() - start
            # print('Solved puzzle; took {0:.2f} second(s)'.format(t))
            time_list.append(t)
        return {
            'data': time_list,
            'label': label
        }

    @staticmethod
    def barplot(data_list, sort_data=True, title=''):

        def _define_subplot(data, index, ylim, xlabel):
            colors = ['black', 'black', 'blue', 'blue']
            num_puzzles = range(1, 1 + len(data['data']))

            plt.subplot(2, 2, index)
            plt.bar(x=num_puzzles, height=data['data'], facecolor=colors[index-1], alpha=0.75, label=data['label'])
            plt.gca().set_ylim([0, ylim])
            plt.xlabel(xlabel)
            plt.ylabel('Time to solve [s]')
            plt.legend()
            plt.grid(which='both', axis='y')

        if sort_data:
            for data in data_list:
                data['data'] = sorted(data['data'])
            xlabel = 'Puzzle index (sorted) [#]'
        else:
            xlabel = 'Puzzle index [#]'

        # get max value
        ylim = max([max(data['data']) for data in data_list])

        plt.figure()
        for counter, data in enumerate(data_list):
            _define_subplot(data, counter+1, ylim=ylim+0.1, xlabel=xlabel)

        plt.suptitle(title)


def main():
    NUM_PUZZLES = 10

    grids_easy = SudokuSolver.from_file(os.path.join('grids', 'easy.txt'), sep='========')
    grids_hard = SudokuSolver.from_file(os.path.join('grids', 'hard.txt'))

    # classic algorithm
    sudoku_solver = SudokuSolver(use_naked_twins=False)
    results_easy = sudoku_solver.solve_all(grids_easy[:NUM_PUZZLES], label='Easy')
    results_hard = sudoku_solver.solve_all(grids_hard[:NUM_PUZZLES], label='Hard')

    # twins
    sudoku_solver = SudokuSolver(use_naked_twins=True)
    results_easy_twins = sudoku_solver.solve_all(grids_easy[:NUM_PUZZLES], label='Easy (twins)')
    results_hard_twins = sudoku_solver.solve_all(grids_hard[:NUM_PUZZLES], label='Hard (twins)')

    # plot results
    results = [results_easy, results_hard, results_easy_twins, results_hard_twins]
    SudokuSolver.barplot(copy.deepcopy(results), title='Sudoku solver algorithm comparison')
    SudokuSolver.barplot(copy.deepcopy(results), sort_data=False, title='Per puzzle comparison')

    # plot
    plt.show()


if __name__ == "__main__":
    main()