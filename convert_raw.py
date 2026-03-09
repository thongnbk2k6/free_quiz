"""
Paste raw Q&A text from the website, then press Enter on an empty line to finish.
Outputs data/answer.csv in the correct format.
"""
import csv
import os


def parse_raw_text(raw):
    lines = raw.splitlines()
    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # A question line ends with '?'
        if line.endswith("?"):
            question = line
            # Find the next non-empty line as the answer
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                answer = lines[i].strip()
                pairs.append((question, answer))
        i += 1
    return pairs


def write_csv(pairs, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["question", "answer"])
        for q, a in pairs:
            writer.writerow([q, a])


def main():
    print("Paste raw Q&A text below (press Enter twice on an empty line to finish):\n")
    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "":
            empty_count += 1
            if empty_count >= 3:
                break
        else:
            empty_count = 0
        lines.append(line)

    raw = "\n".join(lines)
    pairs = parse_raw_text(raw)

    if not pairs:
        print("No Q&A pairs found in input.")
        return

    out_path = "data/answer.csv"
    write_csv(pairs, out_path)
    print(f"\nWrote {len(pairs)} Q&A pairs to {out_path}:")
    for q, a in pairs:
        print(f"  Q: {q}")
        print(f"  A: {a}\n")


if __name__ == "__main__":
    main()
