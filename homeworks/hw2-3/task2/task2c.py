from pathlib import Path

from language import Automaton


ALPHABET = {'a', 'b', 'c'}
IMAGES = Path(__file__).resolve().parent.parent / 'images' / 'task2' / 'c'


def build_nfa():
    nfa = Automaton(ALPHABET, range(5), {}, {0}, {4})

    # Запоминаем букву и завершаем слово при её повторном появлении.
    for symbol, state in (('a', 1), ('b', 2), ('c', 3)):
        nfa.add_transition(0, symbol, 0)
        nfa.add_transition(0, symbol, state)

        for current in sorted(ALPHABET):
            nfa.add_transition(state, current, state)

        nfa.add_transition(state, symbol, 4)

    return nfa


def main():
    nfa = build_nfa()
    dfa = nfa.determinize()
    pmdfa = nfa.minimize()

    for name, filename, automaton in (
        ('НКА', 'nfa.png', nfa),
        ('ДКА', 'dfa.png', dfa),
        ('ПМДКА', 'pmdfa.png', pmdfa),
    ):
        path = automaton.draw(IMAGES / filename)
        print(f'{name}: число состояний — {len(automaton.states)}; схема — {path}')


if __name__ == '__main__':
    main()
