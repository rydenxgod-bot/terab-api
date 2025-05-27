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
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context()
            page = context.new_page()

            # Navigate to page
            page.goto(url, timeout=60000)

            # Wait for the filename to load (up to 15 seconds)
            try:
                page.wait_for_selector(".file-name, .filename", timeout=15000)
            except:
                pass  # Continue even if file name isn't found

            # Extract file name
            try:
                file_name = page.eval_on_selector(".file-name, .filename", "el => el.textContent.trim()")
            except:
                file_name = "Unknown"

            # Extract file size
            try:
                file_size = page.eval_on_selector(".file-size, .size", "el => el.textContent.trim()")
            except:
                file_size = "Unknown"

            # Extract real URLs using surl fallback
            surl_match = re.search(r"surl=([a-zA-Z0-9_-]+)", url)
            surl = surl_match.group(1) if surl_match else None

            if not surl:
                # Try to extract from redirected canonical link
                try:
                    canonical = page.eval_on_selector('link[rel="canonical"]', "el => el.href")
                    surl_match = re.search(r"surl=([a-zA-Z0-9_-]+)", canonical)
                    surl = surl_match.group(1) if surl_match else None
                except:
                    surl = None

            preview_url = f"https://www.terabox.com/sharing/link?surl={surl}" if surl else url
            watch_url = f"https://www.terabox.com/streaming/link?surl={surl}" if surl else url
            download_page = f"https://www.terabox.com/share/init?surl={surl}" if surl else url

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
        return JSONResponse({
            "status": True,
            "message": "Partial success. File details might be missing but URLs are returned.",
            "preview_url": url,
            "watch_url": url,
            "download_page": url,
            "file_info": {
                "name": "Unknown",
                "size": "Unknown",
                "type": "Video or Unknown"
            },
            "error_detail": str(e)
        }, status_code=200)
