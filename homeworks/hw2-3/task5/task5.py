from pathlib import Path

from language import Automaton


IMAGE = Path(__file__).resolve().parent.parent / 'images' / 'task5' / 'counterexample.png'


def build_automaton():
    automaton = Automaton({'a', 'b'}, {0}, {}, {0}, {0})
    automaton.add_transition(0, 'a', 0)
    return automaton


def main():
    path = build_automaton().draw(IMAGE)
    print(f'Неполный ДКА для задачи 5: {path}')


if __name__ == '__main__':
    main()
