from datetime import datetime
from random import randint, shuffle, choice, choices
from statistics import median

DEBUG = 0 # PRINTS DEBUG INFO TO CONSOLE
          # -1 = PRINT DEBUG FOR SOLVE ONLY
          # 0 = OFF
          # 1 = ON
          # 2 = PRINTS GRID EACH STEP

# helper methods
def rand():
    return randint(1, 9)

def output(msg):
    out_fmt = '{0} : {1}'
    now = datetime.now()
    timestamp = now.strftime('%H:%M:%S.%f')

    if '\n' in msg:
        msg = '\n'.join([out_fmt.format(timestamp, line) for line in msg.split('\n')])
    else:
        msg = out_fmt.format(timestamp, msg)
    print(msg)

def cleanup(func):
    def wrapper(self, *func_args, **func_kwargs):
        func(self, *func_args, **func_kwargs)
        self.find_all()
        self.cleanup(func.__name__)
        if self.debug == 2:
            self.display()
    return wrapper

### CONVENTIONS ###
#  col = 1 indexed column number (excel-style)
#  row = 1 indexed row number (excel-style)
#  col_num = 0 indexed column number
#  row_num = 0 indexed row number
#  index = index per self.values

class Defaults:
    max_width = 10 # max_width of a row
    num_start_rows = 6 # number of rows to start with
    scramble_rows = 20 # number of rows before scramble is available
    build_count_min = 6 # minimum build counts by which if necessary rows for scramble haven't been reached, scramble is enabled
    build_count_max = 12 # maximum times build can be used before it is forcibly replaced by scramble
    build_scramble_threshold = 4 # number of matches must be less than this for build or scramble to be available

    # match valuation for finding matches and grading them
    row_match = 1.2
    col_match = 1.0
    reuse_match = 0.2

    # SCORING
    sum_value = 10 # numbers can add up to add_value to match

    single_score = 1 # score added per number for a match
    row_score = 10 # score added per row removed when a match is made
    sum_multiplier = 2 # score multiplier when match sums to the sum value

    multiplier = 1 # starting score multiplier
    multiplier_population = [1, 2, 3, 4, 5, 6, 7, 8] # multipliers from which to randomly select new multiplier on scramble
    # weights for population distribution of multipliers
    multipliers_weights_current_low = [0.04, 0.06, 0.1, 0.2, 0.3, 0.2, 0.1]
    multipliers_weights_current_high = [0.1, 0.2, 0.3, 0.2, 0.1, 0.06, 0.04]
    weighted_multiplier = True


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
        self._scramble_rows = Defaults.scramble_rows
        self._build_count_min = Defaults.build_count_min
        self._build_count_max = Defaults.build_count_max
        self._build_scramble_threshold = Defaults.build_scramble_threshold

        self._row_match = Defaults.row_match
        self._col_match = Defaults.col_match
        self._reuse_match = Defaults.reuse_match

        self._sum_value = Defaults.sum_value

        self._single_score = Defaults.single_score
        self._row_score = Defaults.row_score
        self._sum_multiplier = Defaults.sum_multiplier

        self._multiplier = Defaults.multiplier
        self._multiplier_population = Defaults.multiplier_population
        self._multipliers_weights_current_low = Defaults.multipliers_weights_current_low
        self._multipliers_weights_current_high = Defaults.multipliers_weights_current_high
        self._weighted_multiplier = Defaults.weighted_multiplier

        self.score = 0

        self.values = []
        self._matches = []
        self._grid_matches = 0
        self._grid_value = 0
        self._row_count = 0
        self._build_count = 0
        self._enable_build = False
        self._enable_scramble = False
        self._consecutive_builds = 0
        self._prev_cleanup = None
        self._start_scramble_rows = self._num_start_rows

        self.generate(test)

    @cleanup
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
        self._grid_matches = 0

        # if no matches exist, re-generate
        while self._grid_matches == 0:
            shuffle(self.values)
            self.find_all()
            if test:
                self._grid_matches = 0
                test = False
            if self._grid_matches == 0:
                if self.debug > 0:
                    output('### GENERATE: NO MATCHES, REGENERATING')

        if self.debug > 0:
            output('### GENERATE')

    @cleanup
    def build(self):
        self._build_count += 1
        self.values += [val for val in self.values if val > 0]
        if self.debug > 0:
            output('### BUILD')

    def safe_test_scramble(self):
        while True:
            try:
                self.scramble(test=True)
                break
            except RecursionError:
                self.generate()

    @cleanup
    def scramble(self, test=False):
        self._build_count = 0
        self.values = [val for val in self.values if val > 0]
        self._grid_matches = 0

        # if no matches exist, re-generate
        while self._grid_matches == 0:
            shuffle(self.values)
            self.find_all()
            if test:
                self._grid_matches = 0
                test = False
            if self._grid_matches == 0:
                if self.debug > 0:
                    output('### SCRAMBLE: NO MATCHES, SCRAMBLING')

        self.set_score_multiplier()
        self._start_scramble_rows = len(self.build_rows())

        if self.debug > 0:
            output('### SCRAMBLE: NEW MULTIPLIER = {0}'.format(self._multiplier))

    def is_match(self, v1, v2):
        if v1 == v2:
            return 1
        if v1 + v2 == self._sum_value:
            return 2
        return 0

    @cleanup
    def match(self, m1, m2):
        i1 = self.index_from_col_row(*m1)
        v1 = self.values[i1]
        i2 = self.index_from_col_row(*m2)
        v2 = self.values[i2]
        match = self.is_match(v1, v2)

        if match > 0:
            self.values[i1] *= -1
            self.values[i2] *= -1
            single_count = 2
            row_count = self.row_removal()
            score = self.score_match(match, single_count, row_count)
            self.score += score
            if self.debug > 0:
                match_text = 'PAIR' if match == 1 else 'SUM'
                if row_count > 0:
                    output('### MATCH: {0}: {1} & {2}: {3} | {4} + {5} ROW(s) REMOVED | SCORE: {6}'.format(m1, v1, m2, v2, match_text, row_count, score))
                else:
                    output('### MATCH: {0}: {1} & {2}: {3} | {4} | SCORE: {5}'.format(m1, v1, m2, v2, match_text, score))
        else:
            if self.debug > 0:
                v1 = v1 if v1 > 0 else '_'
                v2 = v2 if v2 > 0 else '_'
                output('### MATCH: {0}: {1} & {2}: {3} | INVALID MATCH'.format(m1, v1, m2, v2))

    def row_removal(self):
        rows = self.build_rows()
        self.values = []
        rows_removed = 0
        for row in rows:
            if all(val < 0 for val in row):
                rows_removed += 1
            else:
                self.values += row
        self._row_count = len(self.build_rows())
        return rows_removed

    def score_match(self, match, single_count, row_count):
        # score match
        match -= 1
        return self._multiplier * (self._sum_multiplier ** match) * (self._single_score * single_count + self._row_score * row_count)

    def set_score_multiplier(self):
        population = [multiplier for multiplier in self._multiplier_population if not multiplier == self._multiplier]
        if self._weighted_multiplier:
            if self._multiplier <= median(self._multiplier_population):
                self._multiplier = choices(population, weights=self._multipliers_weights_current_low)[0]
            else:
                self._multiplier = choices(population, weights=self._multipliers_weights_current_high)[0]
        else:
            self._multiplier = choice(population)

    def cleanup(self, calling_method):
        if (calling_method == 'build') and (self._prev_cleanup == calling_method):
            self._consecutive_builds += 1
        else:
            self._consecutive_builds = 0
        self._prev_cleanup = calling_method

        # generate matches
        self._row_count = len(self.build_rows())
        self._num_count = len([value for value in self.values if value > 0])
        self.find_all()

        prev_build = self._enable_build
        prev_scramble = self._enable_scramble

        self._enable_build = False
        self._enable_scramble = False

        if (self._grid_matches == 0) and (self._consecutive_builds == 2) and (self._row_count >= self._scramble_rows * 0.4):
            self._enable_scramble = True
        if (self._consecutive_builds == 2) and ((self._num_count / self._row_count) >= 0.4) and (self._row_count >= self._scramble_rows * 0.4) and (self._grid_matches <= self._build_scramble_threshold):
            self._enable_scramble = True
        elif (self._consecutive_builds == 3) and (self._row_count >= self._scramble_rows * 0.4) and (self._grid_matches <= self._build_scramble_threshold):
            self._enable_scramble = True
        elif (self._build_count >= self._build_count_min) and (self._row_count >= self._scramble_rows):
            self._enable_scramble = True
        elif self._grid_matches <= self._build_scramble_threshold:
            if self._build_count == self._build_count_max:
                self._enable_scramble = True
            elif self._row_count >= self._scramble_rows:
                self._enable_scramble = True
            else:
                self._enable_build = True

        if self.debug > 0:
            if self._enable_build and not prev_build:
                output('### + BUILD ENABLED')
            elif not self._enable_build and prev_build:
                output('### - BUILD DISABLED')
            if self._enable_scramble and not prev_scramble:
                output('### * SCRAMBLE ENABLED')
            elif not self._enable_scramble and prev_scramble:
                output('### o SCRAMBLE DISABLED')

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
        self._grid_matches = 0
        _used = []

        # by index (_row_match)
        for index, val in enumerate(self.values[:-1]):
            if val > 0:
                if index == 0:
                    if self.values[-1] > 0 and self.is_match(val, self.values[-1]):
                        m1 = self.col_row_from_index(index)
                        m2 = self.col_row_from_index(len(self.values) - 1)
                        self._matches.append((m1, m2))
                        self._grid_matches += 1
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
                            self._grid_matches += 1
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
                                self._grid_matches += 1
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

    def solve(self, fully_solve=True):
        start = datetime.now()
        out_fmt = 'STEP {0:>6} | {1:^8} | ROWS {2:>3} | NUMS {3:>4} | MATCHES {4:>5} | MULTIPLIER {5} | SCORE {6:>7} '
        solve_fmt = '### SOLVE\n'
        solve_fmt += '  TOTAL STEPS:       {0:>6}\n'
        solve_fmt += '  HIGHEST ROW COUNT: {1:>6}\n'
        solve_fmt += '  TOTAL MATCHES:     {2:>6}\n'
        solve_fmt += '  TOTAL BUILDS:      {3:>6}\n'
        solve_fmt += '  TOTAL SCRAMBLES:   {4:>6}\n'
        solve_fmt += '  SCORE:             {5:>6}\n'
        solve_fmt += '  MULTIPLIERS:'
        self.display()
        max_rows = 0
        matches = 0
        builds = 0
        scrambles = 0
        multis = {1: 1,
                  2: 0,
                  3: 0,
                  4: 0,
                  5: 0,
                  6: 0,
                  7: 0,
                  8: 0}
        step = 0
        cont1 = True
        skip_first_scramble = True
        try:
            while cont1:
                max_rows = self._row_count if self._row_count > max_rows else max_rows
                if skip_first_scramble:
                    skip_first_scramble = False
                else:
                    step += 1
                    scrambles += 1
                    self.scramble()
                    if self.debug < 0:
                        output(out_fmt.format(
                                step, 
                                'SCRAMBLE', 
                                self._row_count, 
                                self._num_count, 
                                self._grid_matches, 
                                self._multiplier, 
                                self.score))
                    multis[self._multiplier] += 1
                cont2 = True
                while cont2:
                    step += 1
                    max_rows = self._row_count if self._row_count > max_rows else max_rows
                    if self._grid_matches > 0:
                        matches += 1
                        m1, m2 = self.find_match()
                        self.match(m1, m2)
                        if self.debug < 0:
                            output(out_fmt.format(
                                step, 
                                'MATCH', 
                                self._row_count, 
                                self._num_count, 
                                self._grid_matches, 
                                self._multiplier, 
                                self.score))
                    elif len(self.values) == 0:
                        cont2 = False
                    elif self._enable_scramble:
                        cont2 = False
                    else:
                        builds += 1
                        self.build()
                        if self.debug < 0:
                            output(out_fmt.format(
                                step, 
                                'BUILD', 
                                self._row_count, 
                                self._num_count, 
                                self._grid_matches, 
                                self._multiplier, 
                                self.score))
                if len(self.values) == 0:
                    cont1 = False
                if not fully_solve:
                    cont1 = False
            output(solve_fmt.format(step, max_rows, matches, builds, scrambles, self.score))
            for i in range(1, 9):
                output('  {0} : {1}'.format(i, multis[i] * '*'))
        except KeyboardInterrupt:
            self.display()
        end = (datetime.now() - start).total_seconds()
        output('TOTAL RUNTIME: {0}'.format(end))
        return scrambles

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

        multi_text = 'MULTIPLIER: {0}'.format(self._multiplier)
        multi_offset = int((((self._max_width * 3) + (self._max_width - 2) - len(multi_text)) / 2) + 1)
        multi_offset = 1 if multi_offset <= 0 else multi_offset

        inner_sep = '-' * (self._max_width * 3 + (self._max_width - 1))
        outer_sep = '=' * (self._max_width * 3 + (self._max_width - 1))

        output(outer_sep)
        output(' ' * score_offset + score_text)
        output(' ' * multi_offset + multi_text)
        output('\n'.join([' '.join(row) for row in out]))
        output(inner_sep)
        output('  GRID MATCHES:   {0}'.format(self._grid_matches))
        output('  GRID VALUE:     {0:.2f}'.format(self._grid_value))
        output('  ROW COUNT:      {0}'.format(self._row_count))
        output('  BUILD COUNT:    {0}'.format(self._build_count))
        output(inner_sep)

        if self._enable_build:
            output(' +BUILD ENABLED')
        else:
            output('  BUILD DISABLED')
        if self._enable_scramble:
            output(' *SCRAMBLE ENABLED')
        else:
            output('  SCRAMBLE DISABLED')
        output(outer_sep)


def unit_test():
    output('????? attempt to generate without matches')
    _ = input('(press enter to continue)')
    p = Puzzle(debug=2, max_width=5, num_start_rows=1, test=True)

    output('????? attempt to scramble without matches')
    _ = input('(press enter to continue)')
    p.safe_test_scramble()

    output('????? generate puzzle')
    _ = input('(press enter to continue)')
    p = Puzzle(debug=2)

    output('????? attempt invalid match')
    _ = input('(press enter to continue)')
    m1, m2 = p.find_invalid_match()
    p.match(m1, m2)

    output('????? attempt match')
    _ = input('(press enter to continue)')
    m1, m2 = p.find_match()
    p.match(m1, m2)

    output('????? build new rows')
    _ = input('(press enter to continue)')
    p.build()

    output('????? solve until scramble enabled')
    _ = input('(press enter to continue)')
    p.solve(False)
    _ = input('(press enter to continue)')

    output('????? scramble puzzle')
    _ = input('(press enter to continue)')
    p.scramble()
    _ = input('(press enter to continue)')

    output('????? solve puzzle - debug 2')
    _ = input('(press enter to continue)')
    p = Puzzle(debug=2)
    p.solve()
    _ = input('(press enter to continue)')

    output('????? solve puzzle - debug 1')
    _ = input('(press enter to continue)')
    p = Puzzle(debug=1)
    p.solve()
    _ = input('(press enter to continue)')

    output('????? solve puzzle - debug -1')
    _ = input('(press enter to continue)')
    p = Puzzle(debug=-1)
    p.solve()
    _ = input('(press enter to continue)')

    output('????? solve puzzle - debug 0')
    _ = input('(press enter to continue)')
    p = Puzzle()
    p.solve()
    _ = input('(press enter to continue)')

if __name__ == '__main__':
    # unit_test()
    p = Puzzle(debug=-1)
    p.solve()