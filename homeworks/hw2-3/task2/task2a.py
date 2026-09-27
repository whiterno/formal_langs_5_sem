from pathlib import Path

from language import Automaton


REGEX = 'a(a(ab)*a(ab)*|b)*'
ALPHABET = {'a', 'b'}
IMAGES = Path(__file__).resolve().parent.parent / 'images' / 'task2' / 'a'


def main():
    nfa = Automaton.from_regex(REGEX, ALPHABET)
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
