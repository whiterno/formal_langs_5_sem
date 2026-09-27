from pathlib import Path

from language import Automaton


ALPHABET = {'a', 'b'}
IMAGES = Path(__file__).resolve().parent.parent / 'images' / 'task2' / 'b'


def build_nfa():
    nfa = Automaton(ALPHABET, range(8), {}, {0}, {3, 7})

    # Для проверки условия 'или' создаем 2 ε-перехода
    nfa.add_transition(0, None, 1)
    nfa.add_transition(0, None, 4)

    for source, symbol, target in (
        (1, 'a', 2), (1, 'b', 1),
        (2, 'a', 3), (2, 'b', 2),
        (3, 'a', 3), (3, 'b', 3),
        (4, 'a', 4), (4, 'b', 5),
        (5, 'a', 5), (5, 'b', 6),
        (6, 'a', 6), (6, 'b', 7),
        (7, 'a', 7), (7, 'b', 7),
    ):
        nfa.add_transition(source, symbol, target)

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
