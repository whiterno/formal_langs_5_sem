import json
import subprocess
from pathlib import Path


class Automaton:
    def __init__(self, alphabet, states, transitions, start_states, final_states):
        self.alphabet = set(alphabet)
        self.states = set(states)
        self.start_states = set(start_states)
        self.final_states = set(final_states)

        self.transitions = {}

        for edge, targets in transitions.items():
            self.transitions[edge] = set(targets)

    @staticmethod
    def from_regex(regex, alphabet=None):
        """
            Строит НКА по алгоритму Томпсона.
        """

        from .regex_parser import RegexParser

        parser = RegexParser(regex)
        return parser.build(alphabet)

    def copy(self):
        return Automaton(
            self.alphabet,
            self.states,
            self.transitions,
            self.start_states,
            self.final_states,
        )

    def add_transition(self, source, symbol, target):
        """
            Добавляет переход. None обозначает ε.
        """

        self.states.add(source)
        self.states.add(target)

        if symbol is not None:
            self.alphabet.add(symbol)

        edge = (source, symbol)

        if edge not in self.transitions:
            self.transitions[edge] = set()

        self.transitions[edge].add(target)

    def epsilon_closure(self, states):
        """
            Все состояния, достижимые из states только по ε-переходам.
        """

        closure = set(states)
        stack = list(states)

        while stack:
            state = stack.pop()
            targets = self.transitions.get((state, None), set())

            for target in targets:
                if target not in closure:
                    closure.add(target)
                    stack.append(target)

        return closure

    def move(self, states, symbol):
        """
            Один шаг по символу из множества состояний, без ε-замыкания.
        """

        result = set()

        for state in states:
            targets = self.transitions.get((state, symbol), set())
            result.update(targets)

        return result

    def accepts(self, word):
        current = self.epsilon_closure(self.start_states)

        for symbol in word:
            current = self.move(current, symbol)
            current = self.epsilon_closure(current)

        return bool(current & self.final_states)

    def is_deterministic(self):
        if len(self.start_states) != 1:
            return False

        for (state, symbol), targets in self.transitions.items():
            if symbol is None and targets:
                return False

            if len(targets) > 1:
                return False

        return True

    def is_complete(self):
        if not self.is_deterministic():
            return False

        for state in self.states:
            for symbol in self.alphabet:
                if not self.transitions.get((state, symbol)):
                    return False

        return True

    def determinize(self):
        """
            Детерменизация через объединение префиксов.
        """

        start = self.epsilon_closure(self.start_states)
        subsets = [start]

        result = Automaton(self.alphabet, {0}, {}, {0}, set())
        index = 0

        while index < len(subsets):
            subset = subsets[index]

            if subset & self.final_states:
                result.final_states.add(index)

            for symbol in sorted(self.alphabet):
                target = self.move(subset, symbol)
                target = self.epsilon_closure(target)

                if not target:
                    continue

                if target not in subsets:
                    subsets.append(target)

                target_index = subsets.index(target)
                result.add_transition(index, symbol, target_index)

            index += 1

        return result

    def complete(self):
        """
            Приводит НКА к ДКА и добавляет недостающие переходы в сток.
        """

        result = self.copy() if self.is_deterministic() else self.determinize()
        sink = max(result.states) + 1
        need_sink = False

        for state in sorted(result.states):
            for symbol in sorted(result.alphabet):
                if not result.transitions.get((state, symbol)):
                    result.add_transition(state, symbol, sink)
                    need_sink = True

        if need_sink:
            for symbol in result.alphabet:
                result.add_transition(sink, symbol, sink)

        return result

    def minimize(self):
        """
            Минимизация полным разбиением на классы.
        """

        dfa = self.determinize().complete()
        alphabet = sorted(dfa.alphabet)
        groups = []

        if dfa.final_states:
            groups.append(dfa.final_states)

        non_final = dfa.states - dfa.final_states

        if non_final:
            groups.append(non_final)

        while True:
            group_number = {}

            for index, group in enumerate(groups):
                for state in group:
                    group_number[state] = index

            new_groups = []

            for group in groups:
                parts = {}

                for state in sorted(group):
                    signature = []

                    for symbol in alphabet:
                        target = min(dfa.transitions[(state, symbol)])
                        signature.append(group_number[target])

                    signature = tuple(signature)

                    if signature not in parts:
                        parts[signature] = set()

                    parts[signature].add(state)

                new_groups.extend(parts.values())

            if len(new_groups) == len(groups):
                break

            groups = new_groups

        result = Automaton(alphabet, range(len(groups)), {}, set(), set())

        for index, group in enumerate(groups):
            if group & dfa.start_states:
                result.start_states.add(index)

            if group & dfa.final_states:
                result.final_states.add(index)

            representative = min(group)

            for symbol in alphabet:
                target = min(dfa.transitions[(representative, symbol)])
                result.add_transition(index, symbol, group_number[target])

        return result

    def minimize_brzozowski(self):
        """
            Строит полный минимальный ДКА алгоритмом Бржозовского.
        """

        result = self.reverse().determinize().reverse().determinize()

        if not result.final_states:
            transitions = {(0, symbol): {0} for symbol in result.alphabet}
            return Automaton(result.alphabet, {0}, transitions, {0}, set())

        return result.complete()

    def reverse(self):
        """
            Строит автомат для языка из слов, записанных в обратном порядке.
        """

        result = Automaton(
            self.alphabet,
            self.states,
            {},
            self.final_states,
            self.start_states,
        )

        for (source, symbol), targets in self.transitions.items():
            for target in targets:
                result.add_transition(target, symbol, source)

        return result

    def complement(self):
        """
            Строит дополнение языка относительно алфавита автомата.
        """

        result = self.determinize().complete()
        result.final_states = result.states - result.final_states
        return result

    def to_dot(self):
        """
            Описание графа в формате Graphviz DOT.
        """

        lines = [
            'digraph Automaton {',
            '    rankdir=LR;',
            '    start [shape=point];',
        ]

        for state in sorted(self.states):
            shape = 'circle'

            if state in self.final_states:
                shape = 'doublecircle'

            lines.append(f'    "{state}" [shape={shape}];')

        for state in sorted(self.start_states):
            lines.append(f'    start -> "{state}";')

        for (source, symbol), targets in self.transitions.items():
            label = '1' if symbol is None else symbol
            label = json.dumps(label, ensure_ascii=False)

            for target in sorted(targets):
                lines.append(f'    "{source}" -> "{target}" [label={label}];')

        lines.append('}')
        return '\n'.join(lines)

    def draw(self, path='automaton.png'):
        """
            Сохраняет рисунок и открывает его. Нужна программа Graphviz.
        """

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image_format = path.suffix[1:]

        if image_format == 'dot':
            path.write_text(self.to_dot(), encoding='utf-8')
            return path

        subprocess.run(
            ['dot', f'-T{image_format}', '-o', str(path)],
            input=self.to_dot(),
            text=True,
            encoding='utf-8',
            check=True,
        )

        return path
