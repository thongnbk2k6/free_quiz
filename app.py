import builtins
import os
import queue
import threading

from flask import Flask, render_template, request, jsonify

from answer_loader import load_answers
from convert_raw import parse_raw_text, write_csv
import config

app = Flask(__name__)

# --------------- shared state ---------------
log_queue = queue.Queue()
bot_running = False
driver_ref = None
_original_print = builtins.print


def _capturing_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    if msg.strip():
        log_queue.put(msg)
    _original_print(*args, **kwargs)


# --------------- pages ---------------
@app.route("/")
def index():
    return render_template("index.html")


# --------------- bot control ---------------
@app.route("/api/start", methods=["POST"])
def start_bot():
    global bot_running, driver_ref
    if bot_running:
        return jsonify({"error": "Bot is already running"}), 400

    data = request.json
    game_id = data.get("game_id", "").strip()
    nickname = data.get("nickname", "").strip() or None
    read_only = data.get("mode") == "readonly"

    if not game_id:
        return jsonify({"error": "Game ID is required"}), 400

    def run_bot():
        global bot_running, driver_ref
        bot_running = True
        builtins.print = _capturing_print
        try:
            from join_bot import join_game
            from quiz_bot import play_quiz

            qa_database = {}
            if not read_only:
                qa_database = load_answers(config.ANSWERS_CSV)
                print(f"Loaded {len(qa_database)} Q&A pairs from CSV.")

            print(f"Joining game {game_id}...")
            driver = join_game(game_id, nickname=nickname)
            driver_ref = driver
            print("Joined! Waiting for questions...")

            answered = play_quiz(driver, qa_database, read_only=read_only)
            label = "Read" if read_only else "Answered"
            print(f"Done. {label} {answered} question(s).")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            bot_running = False
            builtins.print = _original_print
            if driver_ref:
                try:
                    driver_ref.quit()
                except Exception:
                    pass
                driver_ref = None

    threading.Thread(target=run_bot, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/api/stop", methods=["POST"])
def stop_bot():
    global bot_running, driver_ref
    if driver_ref:
        try:
            driver_ref.quit()
        except Exception:
            pass
        driver_ref = None
    bot_running = False
    log_queue.put("Bot stopped by user.")
    return jsonify({"status": "stopped"})


@app.route("/api/status")
def bot_status():
    return jsonify({"running": bot_running})


@app.route("/api/logs")
def get_logs():
    messages = []
    while not log_queue.empty():
        try:
            messages.append(log_queue.get_nowait())
        except queue.Empty:
            break
    return jsonify({"logs": messages})


# --------------- answer management ---------------
@app.route("/api/answers", methods=["GET"])
def get_answers():
    try:
        qa = load_answers(config.ANSWERS_CSV)
        pairs = [{"question": q, "answer": a} for q, a in qa.items()]
    except Exception:
        pairs = []
    return jsonify({"answers": pairs})


@app.route("/api/answers", methods=["POST"])
def save_answers():
    data = request.json
    answers = data.get("answers", [])
    pairs = [(a["question"], a["answer"]) for a in answers]
    write_csv(pairs, config.ANSWERS_CSV)
    return jsonify({"status": "saved", "count": len(pairs)})


@app.route("/api/convert", methods=["POST"])
def convert_raw():
    data = request.json
    raw_text = data.get("raw_text", "")
    pairs = parse_raw_text(raw_text)
    return jsonify({"pairs": [{"question": q, "answer": a} for q, a in pairs]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
