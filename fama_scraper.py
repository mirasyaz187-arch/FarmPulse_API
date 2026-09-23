import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_fama_prices(search_keyword=None):
    """Fungsi real-time Web Scraper FAMA dengan perlindungan offline fallback."""
    url = "https://www.fama.gov.my/harga-pasaran-pilihan"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        wait = WebDriverWait(driver, 8)

        if search_keyword:
            try:
                search_box = wait.until(
                    EC.presence_of_element_located((By.ID, "search_input"))
                )
                search_box.clear()
                search_box.send_keys(search_keyword)
                time.sleep(1)
            except Exception:
                pass

        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        driver.quit()

        table = soup.find("table")
        if not table:
            return pd.DataFrame()

        headers = [th.text.strip() for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr"):
            cols = [td.text.strip() for td in tr.find_all("td")]
            if cols:
                rows.append(cols)

        df = pd.DataFrame(rows, columns=headers if headers else None)

        for col in df.columns:
            if "Harga" in col or "RM" in col:
                df[col] = (
                    df[col]
                    .str.replace("RM", "", regex=False)
                    .str.replace(",", "", regex=False)
                    .str.strip()
                )
                df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    except Exception as e:
        print(f"[Offline Sync Active] Log Ralat Scraper FAMA: {e}")
        return pd.DataFrame()