# utils/preprocess.py
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup


def get_preprocessed_text(url: str) -> str:
    """
    주어진 URL에서 HTML 파일을 읽어들인 후 텍스트를 전처리하여 반환합니다.

    Parameters:
    url (str): HTML 파일을 가져올 URL

    Returns:
    str: 전처리된 텍스트
    """

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    time_to_live = 3
    while True:
        try:
            driver.get(url)
            wait = WebDriverWait(driver, timeout=5)
            wait.until(lambda d: d.find_element(By.TAG_NAME, 'article'))
            break
        except:
            time_to_live -= 1
            if time_to_live > 0:
                continue
            else:
                return ""
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    article = soup.article

    preprocessed_text = ""
    tags = ['h1', 'h2', 'h3', 'p']
    for tag in article.find_all(tags):
        if tag.name == 'h1':
            preprocessed_text += 'Title: '
        elif tag.name == 'h2':
            preprocessed_text += 'Subtitle: '
        preprocessed_text += tag.get_text() + '\n'

    return preprocessed_text
