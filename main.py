from answer_loader import load_answers
from join_bot import join_game
from quiz_bot import play_quiz
import config

print("Select mode:")
print("  1) Read-only  — just show questions & choices in terminal")
print("  2) Auto-answer — read questions, look up CSV, click correct answer")
mode = input("Enter 1 or 2 [default: 2]: ").strip()
read_only = mode == "1"

qa_database = {}
if not read_only:
    qa_database = load_answers(config.ANSWERS_CSV)
    print(f"Loaded {len(qa_database)} Q&A pairs from CSV.")

game_id = input("Enter Game ID: ")
nickname = input("Enter Nickname (blank = default): ").strip() or None

driver = join_game(game_id, nickname=nickname)

print("Joined. Waiting for questions...")
try:
    answered = play_quiz(driver, qa_database, read_only=read_only)
    label = "Read" if read_only else "Answered"
    print(f"\nDone. {label} {answered} question(s).")
finally:
    input("Press Enter to close the browser and exit.")
    try:
        driver.quit()
    except Exception:
        pass