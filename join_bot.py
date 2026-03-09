from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import config


def _create_driver():
    """Create browser driver (Chrome or Firefox) with options that work on Linux."""
    if config.BROWSER == "firefox":
        opts = webdriver.FirefoxOptions()
        if config.HEADLESS:
            opts.add_argument("--headless")
        return webdriver.Firefox(options=opts)
    # Chrome with options that fix "Chrome instance exited" on Linux
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    if config.HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def join_game(game_id, nickname=None):
    driver = _create_driver()
    driver.get(config.URL)

    wait = WebDriverWait(driver, 20)

    game_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, config.GAME_ID_INPUT))
    )
    game_input.send_keys(game_id)

    join_button = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, config.JOIN_BUTTON))
    )
    join_button.click()

    # Some games ask for a nickname after entering the join code.
    # If the nickname field doesn't appear, continue without failing.
    try:
        nickname_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, config.NICKNAME_INPUT))
        )
        nick = (nickname or config.DEFAULT_NICKNAME).strip()
        nickname_input.clear()
        nickname_input.send_keys(nick)
        nickname_input.send_keys(Keys.ENTER)
    except TimeoutException:
        pass

    return driver