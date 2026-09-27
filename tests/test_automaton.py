import itertools
import re
import tempfile
import unittest
from pathlib import Path

from language import Automaton


def make_words(alphabet, max_length):
    words = []

    for length in range(max_length + 1):
        for letters in itertools.product(alphabet, repeat=length):
            words.append(''.join(letters))

    return words


class AutomatonTests(unittest.TestCase):
    def test_transformations(self):
        expressions = [
            'a',
            'ab',
            'a|b',
            '(a|b)*abb',
            '(a*b*)*',
            'a*(ba|ab)*',
        ]

        for expression in expressions:
            automaton = Automaton.from_regex(expression, 'ab')
            complement = automaton.complement()
            reversed_automaton = automaton.reverse()

            variants = [
                automaton,
                automaton.determinize(),
                automaton.determinize().complete(),
                automaton.complete(),
                automaton.minimize(),
                complement.complement().minimize(),
                reversed_automaton.reverse().minimize(),
            ]

            for word in make_words('ab', 5):
                expected = re.fullmatch(expression, word) is not None

                for variant in variants:
                    self.assertEqual(variant.accepts(word), expected)

                self.assertEqual(complement.accepts(word), not expected)
                self.assertEqual(reversed_automaton.accepts(word[::-1]), expected)

            self.assertTrue(variants[2].is_complete())
            self.assertTrue(variants[3].is_complete())
            self.assertTrue(variants[4].is_complete())
            self.assertTrue(complement.is_complete())

    def test_special_languages(self):
        examples = [
            ('0', set()),
            ('1', {''}),
            ('', {''}),
            ('0*', {''}),
            ('1+ab', {'', 'ab'}),
        ]

        for expression, accepted_words in examples:
            automaton = Automaton.from_regex(expression, 'ab')
            complement = automaton.complement()
            reversed_automaton = automaton.reverse()
            variants = [automaton, automaton.minimize()]

            for variant in variants:
                for word in make_words('ab', 3):
                    self.assertEqual(
                        variant.accepts(word),
                        word in accepted_words,
                    )

            for word in make_words('ab', 3):
                self.assertEqual(complement.accepts(word), word not in accepted_words)
                self.assertEqual(reversed_automaton.accepts(word[::-1]), word in accepted_words)

    def test_minimum_sizes(self):
        examples = [('0', 1), ('(a+b)*', 1), ('(a+b)*abb', 4), ('a', 3)]

        for expression, expected_size in examples:
            automaton = Automaton.from_regex(expression, 'ab').minimize()

            self.assertEqual(len(automaton.states), expected_size)

    def test_brzozowski_minimization(self):
        examples = [Automaton.from_regex(expression, 'ab') for expression in ('0', '1', 'a', '(a+b)*abb', 'a*b*')]
        examples.append(Automaton({'a', 'b'}, {0, 1, 2, 99}, {(0, None): {1}, (1, 'a'): {2}, (1, 'b'): {1}}, {0}, {2}))

        for original in examples:
            minimal = original.minimize_brzozowski()
            self.assertTrue(minimal.is_deterministic())
            self.assertTrue(minimal.is_complete())

            start = (frozenset(original.epsilon_closure(original.start_states)), next(iter(minimal.start_states)))
            pairs = [start]
            visited = set()

            while pairs:
                pair = pairs.pop()

                if pair in visited:
                    continue

                visited.add(pair)
                subset, state = pair
                self.assertEqual(bool(set(subset) & original.final_states), state in minimal.final_states)

                for symbol in original.alphabet:
                    target_subset = frozenset(original.epsilon_closure(original.move(subset, symbol)))
                    target_state = next(iter(minimal.transitions[state, symbol]))
                    pairs.append((target_subset, target_state))

            reachable = set(minimal.start_states)
            pending = list(reachable)

            while pending:
                state = pending.pop()

                for symbol in minimal.alphabet:
                    for target in minimal.transitions.get((state, symbol), set()):
                        if target not in reachable:
                            reachable.add(target)
                            pending.append(target)

            self.assertEqual(reachable, minimal.states)

            for left, right in itertools.combinations(minimal.states, 2):
                pending = [(left, right)]
                visited = set()
                distinguishable = False

                while pending:
                    pair = pending.pop()

                    if pair in visited:
                        continue

                    visited.add(pair)
                    first, second = pair

                    if (first in minimal.final_states) != (second in minimal.final_states):
                        distinguishable = True
                        break

                    for symbol in minimal.alphabet:
                        next_first = next(iter(minimal.transitions.get((first, symbol), set())), None)
                        next_second = next(iter(minimal.transitions.get((second, symbol), set())), None)
                        pending.append((next_first, next_second))

                self.assertTrue(distinguishable, f'Эквивалентные состояния: {left}, {right}')

    def test_escaped_symbols(self):
        automaton = Automaton.from_regex(r'\+\1\0\*')

        self.assertTrue(automaton.accepts('+10*'))
        self.assertFalse(automaton.accepts(''))
        self.assertFalse(automaton.accepts('+10'))

        for symbol in '+|*()10\\ ':
            with self.subTest(symbol=symbol):
                literal = Automaton.from_regex('\\' + symbol)
                self.assertTrue(literal.accepts(symbol))
                self.assertFalse(literal.accepts(''))

    def test_regex_precedence(self):
        examples = [
            ('a+b*', {'', 'a', 'b', 'bb'}),
            ('ab+c', {'ab', 'c'}),
        ]

        for expression, accepted in examples:
            automaton = Automaton.from_regex(expression)

            for word in make_words('abc', 2):
                with self.subTest(expression=expression, word=word):
                    self.assertEqual(automaton.accepts(word), word in accepted)

    def test_former_special_symbols_are_letters(self):
        automaton = Automaton.from_regex('ε∅')

        self.assertTrue(automaton.accepts('ε∅'))
        self.assertFalse(automaton.accepts(''))

    def test_epsilon_cycle(self):
        automaton = Automaton(
            alphabet={'a', 'b'},
            states={0, 1, 2, 99},
            transitions={
                (0, None): {1},
                (1, None): {0},
                (1, 'a'): {2},
            },
            start_states={0, 1},
            final_states={2},
        )

        minimal = automaton.minimize()
        completed = automaton.complete()
        reversed_automaton = automaton.reverse()

        self.assertEqual(automaton.epsilon_closure({0}), {0, 1})
        self.assertEqual(automaton.move({0, 1}, 'a'), {2})
        self.assertEqual(automaton.move({0, 1}, 'b'), set())
        self.assertFalse(automaton.is_deterministic())
        self.assertTrue(minimal.accepts('a'))
        self.assertFalse(automaton.accepts(''))
        self.assertEqual(len(minimal.states), 3)
        self.assertTrue(completed.is_complete())

        for word in make_words('ab', 3):
            self.assertEqual(completed.accepts(word), automaton.accepts(word))
            self.assertEqual(reversed_automaton.accepts(word[::-1]), automaton.accepts(word))

    def test_empty_automaton(self):
        automaton = Automaton(set(), set(), {}, set(), set())
        minimal = automaton.minimize()
        complement = automaton.complement()

        self.assertFalse(minimal.accepts(''))
        self.assertTrue(minimal.is_complete())
        self.assertTrue(complement.accepts(''))
        self.assertTrue(complement.is_complete())

    def test_copy_and_add_transition(self):
        original = Automaton({'a'}, {0, 1}, {(0, 'a'): {1}}, {0}, {1})
        copied = original.copy()
        copied.add_transition(1, None, 2)
        copied.add_transition(2, 'b', 3)
        copied.final_states.add(3)

        self.assertEqual(original.states, {0, 1})
        self.assertEqual(original.alphabet, {'a'})
        self.assertEqual(original.transitions, {(0, 'a'): {1}})
        self.assertTrue(copied.accepts('ab'))
        self.assertFalse(original.accepts('ab'))

    def test_complete_dfa(self):
        automaton = Automaton({'a', 'b'}, {0, 1}, {(0, 'a'): {1}}, {0}, {1})

        self.assertTrue(automaton.is_deterministic())
        self.assertFalse(automaton.is_complete())

        completed = automaton.complete()

        self.assertTrue(completed.is_complete())
        self.assertFalse(automaton.is_complete())
        self.assertEqual(len(completed.complete().states), len(completed.states))

        for word in make_words('ab', 3):
            self.assertEqual(completed.accepts(word), automaton.accepts(word))

    def test_branching_nfa(self):
        automaton = Automaton(
            alphabet={'a', 'b'},
            states={0, 1, 2},
            transitions={(0, 'a'): {1, 2}, (2, 'b'): {1}},
            start_states={0},
            final_states={1},
        )

        self.assertFalse(automaton.is_deterministic())

        completed = automaton.complete()
        self.assertTrue(completed.is_complete())

        for word in make_words('ab', 3):
            self.assertEqual(completed.accepts(word), automaton.accepts(word))

    def test_dot_output(self):
        automaton = Automaton(
            alphabet={'a'},
            states={0, 1},
            transitions={(0, None): {1}, (1, 'a'): {1}},
            start_states={0},
            final_states={1},
        )
        dot = automaton.to_dot()

        self.assertIn('"1" [shape=doublecircle]', dot)
        self.assertIn('label="1"', dot)
        self.assertIn('label="a"', dot)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested' / 'automaton.dot'
            self.assertEqual(automaton.draw(path), path)
            self.assertEqual(path.read_text(encoding='utf-8'), dot)


if __name__ == '__main__':
    unittest.main()
