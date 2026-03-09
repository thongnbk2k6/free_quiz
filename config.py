import os

URL = "https://wayground.com/join"

# "chrome" or "firefox"
BROWSER = "chrome"

# Set HEADLESS=true env var for server/Railway deployment
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"

GAME_ID_INPUT = "input[data-cy='gamecode-field']"

JOIN_BUTTON = "button[data-cy='joinGame-button']"

# Nickname page sometimes appears after joining a game.
# Keep this selector permissive to survive UI changes.
NICKNAME_INPUT = "input[data-cy='nickname-field'], input[placeholder*='name' i], input[aria-label*='name' i]"

DEFAULT_NICKNAME = "Player"

# These are placeholders; you may need to update them after inspecting the question screen.
QUESTION_SELECTOR = "div[class*='question']"
OPTION_SELECTOR = "button"

# Path to CSV with columns: question, answer
ANSWERS_CSV = "data/answer.csv"