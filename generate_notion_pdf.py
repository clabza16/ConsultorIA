import asyncio
from playwright.async_api import async_playwright
import os

async def generate_pdf():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Get absolute path to the HTML file
        html_path = os.path.abspath("clases_notion_combinadas.html")
        file_url = f"file:///{html_path}".replace("\\", "/")
        
        print(f"Abriendo {file_url}...")
        await page.goto(file_url)
        
        # Give some time for resources to load
        await page.wait_for_timeout(2000)
        
        # Generate PDF
        pdf_path = "Guia_Teorica_ConsultorIA_Notion_1_2.pdf"
        await page.pdf(
            path=pdf_path,
            format="A4",
            print_background=True,
            margin={"top": "20px", "right": "20px", "bottom": "20px", "left": "20px"}
        )
        
        print(f"PDF generado exitosamente: {pdf_path}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(generate_pdf())
