from random import randint, shuffle

def rand():
    return randint(1, 9)

class Defaults:
    debug = False # prints after every function
    max_width = 10 # max_width of a row
    num_start_rows = 6 # number of rows to start with
    sum_value = 10 # numbers can add up to add_value to match
    min_solve_for_scramble = 0.2 # Must solve min_solve_for_scramble/1.0 of available matches before scramble
    min_rows_multiple_for_scramble = 4 # if < min_solve_for_scramble/1.0 matches exist, after min_rows_multiple_for_scramble * num_start_rows, replace build button with scramble button

class Puzzle:

    def __init__(self, debug=Defaults.debug, max_width=Defaults.max_width, num_start_rows=Defaults.num_start_rows, sum_value=Defaults.sum_value, min_solve_for_scramble=Defaults.min_solve_for_scramble, min_rows_multiple_for_scramble=Defaults.min_rows_multiple_for_scramble):
        self.debug = debug

        self.max_width = max_width
        self.num_start_rows = num_start_rows
        self.sum_value = sum_value
        self.min_solve_for_scramble = min_solve_for_scramble
        self.min_rows_multiple_for_scramble = min_rows_multiple_for_scramble

        self.generate()

    def generate(self):
        self.values = []
        self.num_rows = self.num_start_rows
        for row in range(self.num_start_rows):
            for column in range(self.max_width):
                self.values.append(rand())

        # if no matches exist, re-generate
        if not self.find_match():
            if self.debug:
                print('GENERATE:')
                self.display()
                print('')
                print('  NO MATCHES - RE-GENERATING')
                print('')
            return self.generate()

        if self.debug:
            print('GENERATE:')
            self.display()
            print('')

    def build(self):
        self.values += [val for val in self.values if val > 0]

        self.count_rows()

        if self.debug:
            print('BUILD:')
            self.display()
            print('')

    def scramble(self):
        # remove all None values from self.values
        self.values = [val for val in self.values if val > 0]

        # randomize self.values
        shuffle(self.values)

        # if no matches exist, re-generate
        if not self.find_match():
            if self.debug:
                print('SCRAMBLE:')
                self.display()
                print('')
                print('  NO MATCHES - RE-SCRAMBLING')
                print('')
            return self.scramble()

        if self.debug:
            print('SCRAMBLE:')
            self.display()
            print('')

    def match(self, m1, m2):
        match = False
        (m1_col, m1_row) = m1
        (m2_col, m2_row) = m2
        
        m1 = (m1_row - 1) * self.max_width + (m1_col - 1)
        m2 = (m2_row - 1) * self.max_width + (m2_col - 1)

        v1 = self.values[m1]
        v2 = self.values[m2]

        if self.is_match(v1, v2):
            match = True
            self.values[m1] *= -1
            self.values[m2] *= -1
            self.count_rows()

        if self.debug:
            print('MATCH:')
            if match:
                self.display()
            else:
                v1 = self.value_format(v1)
                v2 = self.value_format(v2)
                print('  INVALID MATCH:')
                print('    ({0}, {1}) = {2}'.format(m1_col, m1_row, v1))
                print('    ({0}, {1}) = {2}'.format(m2_col, m2_row, v2))
            print('')

    def is_match(self, v1, v2):
        if v1 == v2:
            return True
        if v1 + v2 == self.sum_value:
            return True
        return False

    def col_row_from_index(self, index):
        col = (index + 1) - (self.max_width * ((index + 1) // self.max_width))
        row = ((index + 1) // self.max_width) + 1
        return (col, row)

    def build_columns(self):
        rows = [self.values[col: col + self.max_width] for col in range(0, len(self.values), self.max_width)]
        cols = []
        for index in range(self.max_width):
            _col = []
            for row in rows:
                if len(row) >= index + 1:
                    _col.append(row[index])
            cols.append(_col)
        return cols

    def col_row_from_col_index(self, col_num, index):
        col = col_num + 1
        row = index + 1
        return (col, row)

    def find_match(self):
        for index, val in enumerate(self.values[:-1]):
            if val > 0:
                if index == 0:
                    if self.values[-1] > 0 and self.is_match(val, self.values[-1]):
                        m1 = self.col_row_from_index(index)
                        m2 = self.col_row_from_index(len(self.values) - 1)
                        return m1, m2
                for _index, _val in enumerate(self.values[index + 1:]):
                    if _val > 0:
                        if self.is_match(val, _val):
                            m1 = self.col_row_from_index(index)
                            m2 = self.col_row_from_index(_index + index + 1)
                            return m1, m2
                        break

        for col_num, col in enumerate(self.build_columns()):
            for index, val in enumerate(col[:-1]):
                if val > 0:
                    for _index, _val in enumerate(col[index + 1:]):
                        if _val > 0:
                            if self.is_match(val, _val):
                                m1 = self.col_row_from_col_index(col_num, index)
                                m2 = self.col_row_from_col_index(col_num, _index + index + 1)
                                return m1, m2
                            break
        return False

    def find_invalid_match(self):
        for index, val in enumerate(self.values[:-1]):
            if val > 0:
                for _index, _val in enumerate(self.values[index + 1:]):
                    if _val > 0:
                        if self.is_match(val, _val):
                            break
                        m1 = self.col_row_from_index(index)
                        m2 = self.col_row_from_index(_index + index + 1)
                        return m1, m2

    def value_format(self, value):
        used_fmt = '({0})'
        fmt = ' {0} '

        if value > 0:
            return fmt.format(value)
        else:
            return used_fmt.format(value * -1)

    def display(self, values=None):
        out = []

        if values == None:
            values = self.values

        rows = [values[col: col + self.max_width] for col in range(0, len(values), self.max_width)]
        for row in rows:
            _out = []
            for value in row:
                _out.append(self.value_format(value))
            out.append(_out)
        print('\n'.join([' '.join(row) for row in out]))


def unit_test():
    # attempt to generate without matches
    p = Puzzle(debug=True, max_width=4, num_start_rows=1)
    p = Puzzle(debug=True, max_width=4, num_start_rows=1)
    p = Puzzle(debug=True, max_width=4, num_start_rows=1)

    # attempt to scramble without matches
    p.scramble()
    p.scramble()
    p.scramble()

    # generate puzzle
    p = Puzzle(debug=True)

    # attempt invalid match
    m1, m2 = p.find_invalid_match()
    p.match(m1, m2)

    # attempt match
    m1, m2 = p.find_match()
    p.match(m1, m2)

    # build new rows
    p.build()
    
    # scramble puzzle
    p.scramble()
    


## TODO:
#    find_all_matches  (to calculcate min_solve_for_scramble)
#    count_rows
#    remove rows during count_rows
#    starting score multiplier
#    score for matches
#    score for removed row
#    score multiplier randomization during scramble