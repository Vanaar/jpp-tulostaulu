from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from config import Config
import datetime
import time


def debug_message(message, level=1):
    if Config.DEBUG and level >= Config.DEBUG_LEVEL:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

def vuoropari_int_to_str(vuoropari_nro):
    vuoropari_dict = {
        1: "1. aloittava",
        2: "1. lopettava",
        3: "2. aloittava",
        4: "2. lopettava",
        5: "3. aloittava",
        6: "3. lopettava",
        7: "4. aloittava",
        8: "4. lopettava",
        9: "S. aloittava",
        10: "S. lopettava",
        11: "K. aloittava",
        12: "K. lopettava",
        13: "K. jatkoparit",
        14: "Ottelu päättynyt"
    }
    return vuoropari_dict.get(vuoropari_nro, "ERROR: Vuoropari")

def jakso_into_to_str(jakso_nro):
    jakso_dict = {
        1: "1. jakso",
        2: "2. jakso",
        3: "Supervuoro",
        4: "Kotiutuskisa"
    }
    return jakso_dict.get(jakso_nro, "ERROR: Jakso")

def parsi_x_palot(palot: int):
    palot_txt = ""
    for i in range(0, palot):
        palot_txt += "X"
        if (i + 1) % 4 == 0:
            palot_txt += "<br/>"
    
    return palot_txt

def lataa_www_sivu(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    
    if hasattr(Config, 'CHROMIUM_CUSTOM_CONFIG') and Config.CHROMIUM_CUSTOM_CONFIG:
        service = Service(executable_path=Config.CHROMIUM_PATH)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    
    driver.get(url)
    time.sleep(Config.PAGE_LOAD_WAIT)
    page_content = driver.page_source
    driver.quit()
    
    return page_content


    
    