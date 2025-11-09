from __future__ import annotations
import json, time
from dataclasses import dataclass
from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE = "https://books.toscrape.com/"

class Book(BaseModel):
    title: str
    price: float = Field(..., ge=0)
    rating: int = Field(..., ge=0, le=5)
    url: str

def rating_to_int(r: str) -> int:
    map_ = {"One":1,"Two":2,"Three":3,"Four":4,"Five":5}
    return map_.get(r.strip(), 0)

def scrape_page(driver, url: str) -> list[Book]:
    driver.get(url)
    time.sleep(0.5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"].strip()
        price_text = article.select_one(".price_color").get_text().replace("£","")
        rating = rating_to_int(next((c for c in article["class"] if c in ["One","Two","Three","Four","Five"]), ""))
        rel = article.h3.a["href"]
        url_abs = (BASE + rel).replace("../../../", BASE)
        try:
            book = Book(title=title, price=float(price_text), rating=rating, url=url_abs)
            out.append(book)
        except ValidationError:
            continue
    return out

def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    with webdriver.Chrome(options=opts) as driver:
        all_books = []
        for page in [BASE, BASE + "catalogue/page-2.html"]:
            all_books.extend(scrape_page(driver, page))

    Path("output").mkdir(exist_ok=True)
    with open("output/books.jsonl", "w", encoding="utf-8") as f:
        for b in all_books:
            f.write(json.dumps(b.model_dump(), ensure_ascii=False) + "\n")
    print(f"Saved {len(all_books)} items to output/books.jsonl")

if __name__ == "__main__":
    main()
