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
    scramble_multiplier = 3 # multiple of start rows after which scramble is available
    build_count_min = 3 # minimum builds before scramble can be used
    build_count_max = 8 # maximum times build can be used before it is forcibly replaced by scramble
    build_scramble_threshold = 0.2 # multiplies num_start_rows to create threshold when scramble can go back to build
    match_score = 1 # score added per match
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

        self._scramble_multiplier = Defaults.scramble_multiplier
        self._build_count_min = Defaults.build_count_min
        self._build_count_max = Defaults.build_count_max
        self._build_scramble_threshold = Defaults.build_scramble_threshold
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
        self._build_count = 0

        self.generate(test)

    def generate(self, test=False):
        self.values = []
        self.num_rows = self._num_start_rows
        length = self._num_start_rows * self._max_width
        if not length % 2 == 0:
            length += 1

        for _ in range(int(length / 2)):
            add = rand()
            self.values.append(add)
            self.values.append(add)
        shuffle(self.values)
        self._grid_value_base = None
        self.cleanup()
        self._grid_value_base = self._grid_value

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
        self._build_count += 1
        self.values += [val for val in self.values if val > 0]
        self._grid_value_base = None
        self.cleanup()
        self._grid_value_base = self._grid_value

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
        self._build_count = 0
        self.values = [val for val in self.values if val > 0]
        shuffle(self.values)
        self._grid_value_base = None
        self.cleanup()
        self._grid_value_base = self._grid_value

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

        self._enable_build = False
        self._enable_scramble = False

        if (self._grid_value_base == None) or (self._grid_value_base <= 2):
            if (self._build_count >= self._build_count_min) and (self._grid_value <= 2):
                if self.debug:
                    print('#' * 20 + 'SCRAMBLE CATCH!' + '#' * 20)
                self._enable_scramble = True

        if not self._grid_value_base == None:
            if self._grid_value <= self._build_scramble_threshold * self._grid_value_base:
                if self.debug:
                    print('{0} <= {1} - ENABLE BUILD'.format(self._grid_value, self._build_scramble_threshold * self._grid_value_base))
                self._enable_build = True

            if (self._build_count >= self._build_count_min) and (self._row_count >= self._num_start_rows * self._scramble_multiplier) and (self._grid_value <= self._build_scramble_threshold * self._grid_value_base):
                if self.debug:
                    print('{0} >= {1} && {2} >= {3} && {4} <= {5} - ENABLE SCRAMBLE'.format(self._build_count, self._build_count_min, self._row_count, self._num_start_rows * self._scramble_multiplier, self._grid_value, self._build_scramble_threshold * self._grid_value_base))
                self._enable_build = False
                self._enable_scramble = True

            if (self._build_count == self._build_count_max) and (self._grid_value <= self._build_scramble_threshold * self._grid_value_base):
                if self.debug:
                    print('{0} == {1} && {2} <= {3} - ENABLE SCRAMBLE'.format(self._build_count, self._build_count_max, self._grid_value, self._build_scramble_threshold * self._grid_value_base))
                self._enable_build = False
                self._enable_scramble = True

            if (self._grid_value == 0) and (self._row_count >= self._num_start_rows * self._scramble_multiplier):
                if self.debug:
                    print('{0} == 0 && {1} >= {2} - ENABLE SCRAMBLE'.format(self._grid_value, self._row_count, self._num_start_rows * self._scramble_multiplier))
                self._enable_build = False
                self._enable_scramble = True


    def score_match(self):
        # score match
        self.score += self._match_score * 2 * self._score_multiplier

    def score_row(self):
        # score cleared row
        self.score += (self._match_score * self._max_width) * self._score_multiplier

    def set_score_multiplier(self):
        multis = [multi for multi in self._score_multipliers if not multi == self._score_multiplier]
        if self._weighted_score_multiplier:
            if self._score_multiplier <= median(self._score_multipliers):
                self._score_multiplier = choices(multis, weights=self._score_multipliers_weights_low_multi)[0]
            else:
                self._score_multiplier = choices(multis, weights=self._score_multipliers_weights_high_multi)[0]
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


    ### AUTOMATED TESTING ###

    def solve_until_scramble(self):
        step = 0
        while not self._enable_scramble:
            step += 1
            print('## STEP: {0} ##'.format(step))
            if self._grid_value > 0:
                m1, m2 = self.find_match()
                self.match(m1, m2)
            else:
                self.build()

    def solve(self):
        self.display()
        max_rows = 0
        matches = 0
        builds = 0
        scrambles = 0
        step = 0
        cont1 = True
        try:
            while cont1:
                max_rows = self._row_count if self._row_count > max_rows else max_rows
                cont2 = True
                while cont2:
                    step += 1
                    max_rows = self._row_count if self._row_count > max_rows else max_rows
                    if self._grid_value > 0:
                        m1, m2 = self.find_match()
                        self.match(m1, m2)
                        matches += 1
                        if self.debug:
                            print('STEP {0:>6} : ROWS {1:>3} :  MATCH   : SCORE {2:>7}'.format(step, self._row_count, self.score))
                    elif len(self.values) == 0:
                        cont2 = False
                    elif self._enable_scramble:
                        cont2 = False
                    else:
                        self.build()
                        builds += 1
                        if self.debug:
                            print('STEP {0:>6} : ROWS {1:>3} :  BUILD   : SCORE {2:>7}'.format(step, self._row_count, self.score))
                if len(self.values) == 0:
                    cont1 = False
                else:
                    step += 1
                    self.scramble()
                    scrambles += 1
                    if self.debug:
                        print('STEP {0:>6} : ROWS {1:>3} : SCRAMBLE : SCORE {2:>7}'.format(step, self._row_count, self.score))
            print('\nDONE!\n  HIGHEST ROW COUNT: {0:>6}\n  TOTAL MATCHES:     {1:>6}\n  TOTAL BUILDS:      {2:>6}\n  TOTAL SCRAMBLES:   {3:>6}'.format(max_rows, matches, builds, scrambles))
        except KeyboardInterrupt:
            self.display()


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


        score_text = 'SCORE: {0}'.format(int(self.score))
        score_offset = int((((self._max_width * 3) + (self._max_width - 2) - len(score_text)) / 2) + 1)
        score_offset = 1 if score_offset <= 0 else score_offset

        multi_text = 'MULTIPLIER: {0}'.format(self._score_multiplier)
        multi_offset = int((((self._max_width * 3) + (self._max_width - 2) - len(multi_text)) / 2) + 1)
        multi_offset = 1 if multi_offset <= 0 else multi_offset

        print(' ' * score_offset + score_text)
        print(' ' * multi_offset + multi_text)
        print('\n'.join([' '.join(row) for row in out]))

        print('\n  GRID BASE:      {0:.2f}'.format(self._grid_value_base))
        print('  GRID VALUE:     {0:.2f}'.format(self._grid_value))
        print('  ROW COUNT:      {0}'.format(self._row_count))
        print('  BUILD COUNT:    {0}'.format(self._build_count))
        print('')

        if self._enable_build:
            print(' +BUILD ENABLED')
        else:
            print('  BUILD DISABLED')

        if self._enable_scramble:
            print(' *SCRAMBLE ENABLED')
        else:
            print('  SCRAMBLE DISABLED')


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

    # print('solve until scramble enabled')
    # p.solve_until_scramble()
    
    # print('scramble puzzle')
    # p.scramble()

    _ = input('solve puzzle')
    p = Puzzle()
    p.solve()

if __name__ == '__main__':
    # unit_test()
    p = Puzzle()
    p.solve()