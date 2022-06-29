from random import randint, shuffle, choice, choices
from statistics import median

DEBUG = False # PRINTS AFTER BASIC GAME OPERATIONS

def rand():
    return randint(1, 9)

### CONVENTIONS ###
#  col = 1 indexed column number (excel-style)
#  row = 1 indexed row number (excel-style)
#  col_num = 0 indexed column number
#  row_num = 0 indexed row number
#  index = index per self.values

class Defaults:
    max_width = 10 # max_width of a row
    num_start_rows = 6 # number of rows to start with
    sum_value = 10 # numbers can add up to add_value to match
    min_solve_for_scramble = 0.2 # Must solve min_solve_for_scramble/1.0 of available matches before scramble
    min_rows_multiple_for_scramble = 4 # if < min_solve_for_scramble/1.0 matches exist, after min_rows_multiple_for_scramble * num_start_rows, replace build button with scramble button
    match_score = 10 # score added per match
    score_multiplier = 1 # starting score multiplier
    score_multipliers = [1, 2, 3, 4, 5, 6, 7, 8] # multipliers from which to randomly select new multiplier on scramble
    score_multipliers_weights_low_multi = [0.04, 0.06, 0.1, 0.2, 0.3, 0.2, 0.1]
    score_multipliers_weights_high_multi = [0.1, 0.2, 0.3, 0.2, 0.1, 0.06, 0.04]
    weighted_score_multiplier = True

    # match valuation for finding matches
    row_match = 1.2
    col_match = 1.0
    reuse_match = 0.2



class Puzzle:

    def __init__(
            self, 
            debug=DEBUG, 
            max_width=Defaults.max_width, 
            num_start_rows=Defaults.num_start_rows,
            test=False):

        self.debug = debug
        self._max_width = max_width
        self._num_start_rows = num_start_rows

        self._sum_value = Defaults.sum_value
        self._min_solve_for_scramble = Defaults.min_solve_for_scramble
        self._min_rows_multiple_for_scramble = Defaults.min_rows_multiple_for_scramble
        self._match_score = Defaults.match_score
        self._score_multiplier = Defaults.score_multiplier
        self._score_multipliers = Defaults.score_multipliers
        self._weighted_score_multiplier = Defaults.weighted_score_multiplier
        self._score_multipliers_weights_low_multi = Defaults.score_multipliers_weights_low_multi
        self._score_multipliers_weights_high_multi = Defaults.score_multipliers_weights_high_multi

        self._row_match = Defaults.row_match
        self._col_match = Defaults.col_match
        self._reuse_match = Defaults.reuse_match


        self.score = 0

        self.values = []
        self._matches = []
        self._grid_value = 0
        self._row_count = 0

        self.generate(test)

    def generate(self, test=False):
        self.values = []
        self.num_rows = self._num_start_rows
        for row in range(self._num_start_rows):
            for column in range(self._max_width):
                self.values.append(rand())
        self.cleanup()

        # if no matches exist, re-generate
        if self._grid_value == 0:
            if self.debug:
                print('GENERATE:')
                self.display()
                print('  NO MATCHES - RE-GENERATING')
                print('')
            return self.generate(test=False)

        if test:
            return self.generate(test)

        if self.debug:
            print('GENERATE:')
            self.display()
            print('')

    def build(self):
        self.values += [val for val in self.values if val > 0]
        self.cleanup()

        if self.debug:
            print('BUILD:')
            self.display()
            print('')

    def safe_test_scramble(self):
        while True:
            try:
                self.scramble(test=True)
                break
            except RecursionError:
                self.generate()


    def scramble(self, test=False):
        self.values = [val for val in self.values if val > 0]
        shuffle(self.values)
        self.cleanup()

        # if no matches exist, re-generate
        if self._grid_value == 0:
            if self.debug:
                print('SCRAMBLE:')
                self.display()
                print('  NO MATCHES - RE-SCRAMBLING')
                print('')
            return self.scramble(test=False)

        if test:
            return self.scramble(test)

        self.set_score_multiplier()

        if self.debug:
            print('SCRAMBLE:')
            self.display()
            print('')

    def match(self, m1, m2):
        match = False
        
        i1 = self.index_from_col_row(*m1)
        v1 = self.values[i1]
        i2 = self.index_from_col_row(*m2)
        v2 = self.values[i2]

        if self.is_match(v1, v2):
            match = True
            self.values[i1] *= -1
            self.values[i2] *= -1
            self.score_match()
            self.cleanup()
            if self.debug:
                print('MATCH:')
                self.display()
                print('')
        else:
            if self.debug:
                print('MATCH:')
                v1 = self.value_format(v1)
                v2 = self.value_format(v2)
                print('  INVALID MATCH:')
                print('    {0} = {1}'.format(m1, v1))
                print('    {0} = {1}'.format(m2, v2))
                print('')

    def is_match(self, v1, v2):
        if v1 == v2:
            return True
        if v1 + v2 == self._sum_value:
            return True
        return False

    def cleanup(self):
        rows = self.build_rows()
        self.values = []

        for row in rows:
            if all(val < 0 for val in row):
                self.score_row()
            else:
                self.values += row

        self._row_count = len(self.build_rows())

        # generate matches
        self.find_all()

    def score_match(self):
        # score match
        self.score += self._match_score * self._score_multiplier

    def score_row(self):
        # score cleared row
        self.score += (self._match_score * self._max_width) * self._score_multiplier

    def set_score_multiplier(self):
        multis = [multi for multi in self._score_multipliers if not multi == self._score_multiplier]
        if self._weighted_score_multiplier:
            if self._score_multiplier <= median(self._score_multipliers):
                self._score_multiplier = choices(multis, weights=self._score_multipliers_weights_low_multi)
            else:
                self._score_multiplier = choices(multis, weights=self._score_multipliers_weights_high_multi)
        else:
            self._score_multiplier = choice(multis)
        

    ### INDEX CONVERSION ###

    def index_from_col_row(self, col, row):
        return (row - 1) * self._max_width + (col - 1)

    def col_row_from_index(self, index):
        col = (index + 1) - (self._max_width * ((index + 1) // self._max_width))
        row = ((index + 1) // self._max_width) + 1
        return (col, row)

    def col_row_from_col_row_num(self, col_num, row_num):
        col = col_num + 1
        row = row_num + 1
        return (col, row)

    def index_from_col_index(self, col_num, row_num):
        (col, row) = self.col_row_from_col_row_num(col_num, row_num)
        return self.index_from_col_row(col, row)


    ### SEARCH ITERATION BUILDERS ###

    def build_rows(self, values=None):
        if values == None:
            values = self.values
        return [values[col: col + self._max_width] for col in range(0, len(values), self._max_width)]


    def build_columns(self):
        rows = [self.values[col: col + self._max_width] for col in range(0, len(self.values), self._max_width)]
        cols = []
        for col_num in range(self._max_width):
            _col = []
            for row in rows:
                if len(row) >= col_num + 1:
                    _col.append(row[col_num])
            cols.append(_col)
        return cols


    ### SEARCHING OPERATIONS ###

    def find_invalid_match(self):
        for index, val in enumerate(self.values[:-1]):
            if val > 0:
                for _index, _val in enumerate(self.values[index + 1:]):
                    if _val > 0:
                        if self.is_match(val, _val):
                            break
                        m1 = self.col_row_from_index(index)
                        m2 = self.col_row_from_index(_index + index + 1)
                        return (m1, m2)

    def find_match(self):
        return choice(self._matches)

    def find_all(self):
        self._matches = []
        self._grid_value = 0
        _used = []

        # by index (_row_match)
        for index, val in enumerate(self.values[:-1]):
            if val > 0:
                if index == 0:
                    if self.values[-1] > 0 and self.is_match(val, self.values[-1]):
                        m1 = self.col_row_from_index(index)
                        m2 = self.col_row_from_index(len(self.values) - 1)
                        self._matches.append((m1, m2))
                        if (m1 in _used) or (m2 in _used):
                            if not m1 in _used:
                                _used.append(m1)
                            if not m2 in _used:
                                _used.append(m2)
                            self._grid_value += self._row_match * self._reuse_match
                        else:
                            _used.append(m1)
                            _used.append(m2)
                            self._grid_value += self._row_match
                for _index, _val in enumerate(self.values[index + 1:]):
                    if _val > 0:
                        if self.is_match(val, _val):
                            m1 = self.col_row_from_index(index)
                            m2 = self.col_row_from_index(_index + index + 1)
                            self._matches.append((m1, m2))
                            if (m1 in _used) or (m2 in _used):
                                if not m1 in _used:
                                    _used.append(m1)
                                if not m2 in _used:
                                    _used.append(m2)
                                self._grid_value += self._row_match * self._reuse_match
                            else:
                                _used.append(m1)
                                _used.append(m2)
                                self._grid_value += self._row_match
                        break
        # by column (_col_match)
        for col_num, col in enumerate(self.build_columns()):
            for row_num, val in enumerate(col[:-1]):
                if val > 0:
                    for _row_num, _val in enumerate(col[row_num + 1:]):
                        if _val > 0:
                            if self.is_match(val, _val):
                                m1 = self.col_row_from_col_row_num(col_num, row_num)
                                m2 = self.col_row_from_col_row_num(col_num, _row_num + row_num + 1)
                                self._matches.append((m1, m2))
                                if (m1 in _used) or (m2 in _used):
                                    if not m1 in _used:
                                        _used.append(m1)
                                    if not m2 in _used:
                                        _used.append(m2)
                                    self._grid_value += self._col_match * self._reuse_match
                                else:
                                    _used.append(m1)
                                    _used.append(m2)
                                    self._grid_value += self._col_match
                            break


    ### DEBUG PRINTS ###

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

        rows = self.build_rows(values)
        for row in rows:
            _out = []
            for value in row:
                _out.append(self.value_format(value))
            out.append(_out)

        multi_text = 'MULTIPLIER: {0}'.format(self._score_multiplier)
        offset = int((((self._max_width * 3) + (self._max_width - 2) - len(multi_text)) / 2) + 1)
        offset = 1 if offset <= 0 else offset

        match_text = 'MATCH VALUE: {0}'.format(int(self._grid_value))

        print(' ' * offset + multi_text)
        print('\n'.join([' '.join(row) for row in out]))
        print(' ' * offset + match_text)


def unit_test():
    print('attempt to generate without matches')
    p = Puzzle(debug=True, max_width=5, num_start_rows=1, test=True)

    print('attempt to scramble without matches')
    p.safe_test_scramble()

    print('generate puzzle')
    p = Puzzle(debug=True)

    print('attempt invalid match')
    m1, m2 = p.find_invalid_match()
    p.match(m1, m2)

    print('attempt match')
    m1, m2 = p.find_match()
    p.match(m1, m2)

    print('build new rows')
    p.build()
    
    print('scramble puzzle')
    p.scramble()

if __name__ == '__main__':
    unit_test()
    


## TODO:
#    find_all_matches  (to calculcate min_solve_for_scramble)
#    count_rows
#    remove rows during count_rows
#    starting score multiplier
#    score for matches
#    score for removed row
#    score multiplier randomization during scramble