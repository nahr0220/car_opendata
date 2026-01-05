import random


def build_ladder(n, height, rng):
    rows = []
    for _ in range(height):
        row = [False] * (n - 1)
        i = 0
        while i < n - 1:
            if rng.random() < 0.4:
                row[i] = True
                i += 2
            else:
                i += 1
        rows.append(row)
    return rows


def simulate_ladder(n, rows):
    positions = list(range(n))
    for row in rows:
        i = 0
        while i < n - 1:
            if row[i]:
                positions[i], positions[i + 1] = positions[i + 1], positions[i]
                i += 2
            else:
                i += 1

    final_col_for_player = [0] * n
    for col, player_idx in enumerate(positions):
        final_col_for_player[player_idx] = col
    return final_col_for_player


def draw_ladder(players, rewards, rows):
    n = len(players)
    max_len = max(
        max(len(p) for p in players),
        max(len(r) for r in rewards),
        len("참가자"),
        len("결과"),
    )
    col_w = max(4, max_len + 2)
    mid = col_w // 2
    gap = 3

    def center_text(text):
        return f"{text:^{col_w}}"

    header = (" " * 2) + "   ".join(center_text(p) for p in players)
    print("\n사다리 결과:")
    print(header)

    for row in rows:
        line_parts = []
        for col in range(n):
            part = [" "] * col_w
            part[mid] = "|"
            line_parts.append("".join(part))
            if col < n - 1:
                line_parts.append("-" * gap if row[col] else " " * gap)
        print("  " + "".join(line_parts))

    footer = (" " * 2) + "   ".join(center_text(r) for r in rewards)
    print(footer + "\n")


def print_pairs(pairs):
    left_w = max(len(p) for p, _ in pairs + [("참가자", "")])
    right_w = max(len(r) for _, r in pairs + [("", "결과")])

    line = "+" + "-" * (left_w + 2) + "+" + "-" * (right_w + 2) + "+"
    print(line)
    print(f"| {'참가자'.ljust(left_w)} | {'결과'.ljust(right_w)} |")
    print(line)
    for p, r in pairs:
        print(f"| {p.ljust(left_w)} | {r.ljust(right_w)} |")
    print(line)


def main():
    players = [
        p.strip()
        for p in input("참가자(쉼표로 구분): ").split(",")
        if p.strip()
    ]
    rewards = [
        r.strip()
        for r in input("결과(쉼표로 구분): ").split(",")
        if r.strip()
    ]

    if len(players) != len(rewards):
        print("참가자 수와 결과 수가 같아야 해요.")
        return

    rng = random.Random()
    height = max(6, len(players) * 2)
    rows = build_ladder(len(players), height, rng)
    final_col_for_player = simulate_ladder(len(players), rows)

    pairs = [
        (players[i], rewards[final_col_for_player[i]])
        for i in range(len(players))
    ]

    draw_ladder(players, rewards, rows)
    print_pairs(pairs)


if __name__ == "__main__":
    main()
