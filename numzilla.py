from random import randint, shuffle

DEBUG = True

def rand():
    return randint(1, 9)

class Puzzle:
    width = 10 # width of a row
    start_rows = 6 # number of rows to start with
    sum_value = 10 # numbers can add up to add_value to match
    min_solve = 0.4 # Must solve min_solve/1.0 of available matches before scramble
    max_build = 5 # if < min_solve/1.0 matches exist, after max_build, add scramble button

    def __init__(self):
        self.values = []
        self.build()

    def build(self):
        # if self.values is empty, build new self.values
        if len(self.values) == 0:
            for row in range(Puzzle.start_rows):
                for column in range(Puzzle.width):
                    self.values.append(rand())
        # if self.values is not empty, add all non-blank values to self.values
        else:
            self.values += [val for val in self.values if val > 0]

        if DEBUG:
            self.display()

    def scramble(self):
        # remove all None values from self.values
        self.values = [val for val in self.values if val > 0]

        # randomize self.values
        shuffle(self.values)

        if DEBUG:
            self.display()

    def display(self):
        used_fmt = '({0})'
        fmt = ' {0} '

        out = []

        rows = [self.values[col: col + Puzzle.width] for col in range(0, len(self.values), Puzzle.width)]
        for row in rows:
            _out = []
            for value in row:
                if value > 0:
                    _out.append(fmt.format(value))
                else:
                    _out.append(used_fmt.format(value * -1))
            out.append(_out)
        print('\n'.join([' '.join(row) for row in out]))

