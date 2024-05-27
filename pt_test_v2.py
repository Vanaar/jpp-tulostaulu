import time
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from app.functions import parsi_x_palot

url = f"https://v2.pesistulokset.fi/ottelut/85067"

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.get(url)
time.sleep(1)
page_content = driver.page_source
driver.quit()

soup = BeautifulSoup(page_content, "html.parser")

print(soup)