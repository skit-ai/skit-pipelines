from typing import Dict, List, Any
import json
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import skit_pipelines.constants as const


def simulate_selenium_connection(username, password) -> List[Dict[str, Any]]:
    s=Service(ChromeDriverManager().install())

    options = ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')

    driver = webdriver.Chrome(service=s, options=options)
    driver.maximize_window()
    driver.implicitly_wait(20)
    driver.get(f'https://{const.KUBEFLOW_GATEWAY_ENDPOINT}')
    wait = WebDriverWait(driver, 20)
    wait.until(EC.element_to_be_clickable((By.XPATH, const.USERNAME_XPATH))).send_keys(username)
    wait.until(EC.element_to_be_clickable((By.XPATH, const.PASSWORD_XPATH))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.XPATH, const.SUBMIT_XPATH))).click()

    cookies_resp = driver.get_cookies()
    driver.quit()
    return cookies_resp


def construct_cookie_dict(response: List[Dict[str, Any]]) -> Dict[str, str]:
    for cookie in response:
        if cookie.get(const.DOMAIN) == const.KUBEFLOW_GATEWAY_ENDPOINT and \
            cookie.get(const.NAME) in const.COOKIE_DICT.keys():
                const.COOKIE_DICT[cookie.get(const.NAME)] = cookie.get(const.VALUE)
    return const.COOKIE_DICT


def save_cookies(cookies: Dict[str, str], COOKIES_PATH: str = const.COOKIES_PATH) -> None:
    with open(COOKIES_PATH, 'w') as f:
        json.dump(cookies, f, indent=2)
        
    
def load_cookies(COOKIES_PATH: str = const.COOKIES_PATH) -> Dict[str, str]:
    with open(COOKIES_PATH, "r") as f:
        cookies = json.load(f)
    return cookies


def fetch_latest_cookies(cookie_save_path: str = const.COOKIES_PATH) -> Dict[str, str]:
    logger.error("Fetching latest cookies...")
    cookies_resp = simulate_selenium_connection(const.KF_USERNAME, const.KF_PASSWORD)
    cookies = construct_cookie_dict(cookies_resp)
    save_cookies(cookies, cookie_save_path)
    logger.info("Fetched latest cookies successfully!")
    return cookies
    
