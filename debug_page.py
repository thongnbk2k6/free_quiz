from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()

driver.get("https://wayground.com/join")

# đợi trang load và JS render
time.sleep(5)

print("=== INPUT ELEMENTS ===")
inputs = driver.find_elements(By.TAG_NAME, "input")

for i in inputs:
    print(i.get_attribute("outerHTML"))
    print("------")

print("\n=== BUTTON ELEMENTS ===")
buttons = driver.find_elements(By.TAG_NAME, "button")

for b in buttons:
    print("TEXT:", b.text)
    print("HTML:", b.get_attribute("outerHTML"))
    print("------")

input("Press Enter to close...")

driver.quit()