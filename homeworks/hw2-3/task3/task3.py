from pathlib import Path

from language import Automaton


IMAGE = Path(__file__).resolve().parent.parent / 'images' / 'task3' / 'counterexample.png'


def build_automaton():
    automaton = Automaton({'a', 'b'}, {1, 2, 3, 4}, {}, {1}, {4})

    for source, target in ((1, 2), (2, 3), (3, 4), (4, 2)):
        automaton.add_transition(source, None, target)

    return automaton


def main():
    path = build_automaton().draw(IMAGE)
    print(f'Контрпример для задачи 3: {path}')


if __name__ == '__main__':
    main()
