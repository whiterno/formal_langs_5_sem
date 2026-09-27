from .automaton import Automaton


class RegexParser:
    def __init__(self, regex):
        self.tokens = []
        self.position = 0
        self.automaton = Automaton(set(), set(), {}, set(), set())

        index = 0

        while index < len(regex):
            symbol = regex[index]

            if symbol == '\\':
                index += 1
                self.tokens.append(('letter', regex[index]))

            elif symbol in '+|*()10':
                self.tokens.append((symbol, symbol))

            elif not symbol.isspace():
                self.tokens.append(('letter', symbol))

            index += 1

    def current(self):
        if self.position == len(self.tokens):
            return None

        return self.tokens[self.position][0]

    def new_state(self):
        state = len(self.automaton.states)
        self.automaton.states.add(state)
        return state

    def build(self, alphabet):
        """
            Строим автомат для всего выражения и задаём его вход, выход и алфавит.
        """

        if self.tokens:
            start, end = self.parse_union()
        else:
            start = self.new_state()
            end = self.new_state()
            self.automaton.add_transition(start, None, end)

        self.automaton.start_states = {start}
        self.automaton.final_states = {end}

        if alphabet is not None:
            self.automaton.alphabet = set(alphabet)

        return self.automaton

    def parse_union(self):
        """
            R + S: новый вход и выход, ε-переходы к двум веткам.
        """

        start, end = self.parse_concat()

        while self.current() in ('+', '|'):
            self.position += 1
            right_start, right_end = self.parse_concat()

            new_start = self.new_state()
            new_end = self.new_state()

            self.automaton.add_transition(new_start, None, start)
            self.automaton.add_transition(new_start, None, right_start)
            self.automaton.add_transition(end, None, new_end)
            self.automaton.add_transition(right_end, None, new_end)

            start, end = new_start, new_end

        return start, end

    def parse_concat(self):
        """
            RS: соединяем выход R со входом S ε-переходом.
        """

        start, end = self.parse_star()

        while self.current() in ('letter', '(', '1', '0'):
            right_start, right_end = self.parse_star()
            self.automaton.add_transition(end, None, right_start)
            end = right_end

        return start, end

    def parse_star(self):
        """
            R*: разрешаем пропустить R и возвращаться к его началу.
        """

        start, end = self.parse_atom()

        while self.current() == '*':
            self.position += 1
            new_start = self.new_state()
            new_end = self.new_state()

            self.automaton.add_transition(new_start, None, start)
            self.automaton.add_transition(new_start, None, new_end)
            self.automaton.add_transition(end, None, start)
            self.automaton.add_transition(end, None, new_end)

            start, end = new_start, new_end

        return start, end

    def parse_atom(self):
        """
            Один символ, ε, 0 или выражение в скобках.
        """

        kind, symbol = self.tokens[self.position]
        self.position += 1

        if kind == '(':
            start, end = self.parse_union()
            self.position += 1
            return start, end

        start = self.new_state()
        end = self.new_state()

        if kind == 'letter':
            self.automaton.add_transition(start, symbol, end)
        elif kind == '1':
            self.automaton.add_transition(start, None, end)

        return start, end
