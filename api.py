from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from playwright.sync_api import sync_playwright
import re

app = FastAPI()

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
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            # Extract file name
            name = page.query_selector(".file-name") or page.query_selector(".filename")
            file_name = name.inner_text().strip() if name else "Unknown"

            # Extract file size
            size_elem = page.query_selector(".file-size") or page.query_selector(".size")
            file_size = size_elem.inner_text().strip() if size_elem else "Unknown"

            # Extract preview/watch URL and download link
            surl_match = re.search(r"surl=([a-zA-Z0-9_-]+)", url)
            surl = surl_match.group(1) if surl_match else None

            preview_url = f"https://www.terabox.com/sharing/link?surl={surl}"
            watch_url = f"https://www.terabox.com/streaming/link?surl={surl}"
            download_page = f"https://www.terabox.com/share/init?surl={surl}"

            browser.close()

            return {
                "status": True,
                "message": "Real metadata extracted successfully",
                "preview_url": preview_url,
                "watch_url": watch_url,
                "download_page": download_page,
                "file_info": {
                    "name": file_name,
                    "size": file_size,
                    "type": "Video or Unknown"
                }
            }

    except Exception as e:
        return JSONResponse({"status": False, "message": f"Error: {str(e)}"}, status_code=500)
