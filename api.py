from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.sync_api import sync_playwright
import math

app = FastAPI()

def format_file_size(size_bytes):
    if not size_bytes:
        return "Unknown"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

@app.get("/")
def root():
    return {"message": "Terabox Extractor API is running!"}

@app.get("/api")
def extract(url: str = Query(..., description="Terabox share link")):
    if not url.startswith("http"):
        return JSONResponse({"status": False, "message": "Invalid URL"}, status_code=400)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.goto(url, timeout=90000)
            page.wait_for_timeout(7000)

            file_name = page.eval_on_selector(".file-name, .filename", "el => el.innerText") or "Unknown"
            file_size_raw = page.eval_on_selector(".file-size, .size", "el => el.innerText") or "Unknown"
            file_size_bytes = page.eval_on_selector("meta[itemprop='contentSize']", "el => el.getAttribute('content')") or None

            size_human = format_file_size(int(file_size_bytes)) if file_size_bytes and file_size_bytes.isdigit() else file_size_raw

            # Extract real preview link if possible
            stream_button = page.query_selector("a[href*='/streaming/link?']")
            watch_url = stream_button.get_attribute("href") if stream_button else url

            # Extract real download link
            download_button = page.query_selector("a[href*='/download?']")
            download_link = download_button.get_attribute("href") if download_button else url

            browser.close()

            return {
                "status": True,
                "message": "Real metadata extracted successfully",
                "file_info": {
                    "name": file_name,
                    "size": size_human,
                    "type": "Video or File"
                },
                "watch_url": watch_url,
                "download_url": download_link
            }

    except Exception as e:
        return JSONResponse({"status": False, "message": f"Error: {str(e)}"}, status_code=500)
