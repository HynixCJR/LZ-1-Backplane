import asyncio
import os
from playwright.async_api import async_playwright

async def convert_scribd_html_to_pdf(html_path: str, output_pdf_path: str):
    # Ensure the path is absolute and format it as a file URI
    abs_html_path = f"file://{os.path.abspath(html_path)}"
    
    async with async_playwright() as p:
        # Launch Chromium with web security disabled to allow local file to fetch external fonts/images
        browser = await p.chromium.launch(
            headless=True, 
            args=[
                '--disable-web-security',
                '--allow-file-access-from-files'
            ]
        )
        page = await browser.new_page()
        
        print("Loading HTML file...")
        await page.goto(abs_html_path, wait_until="domcontentloaded")

        print("Triggering page loads and setting up watchdog for dynamic content...")
        await page.evaluate("""
            // 1. Define a watchdog function that fixes images and links whenever they appear
            window.processDynamicContent = () => {
                // Fix images: Swap 'orig' to 'src' and fix HTTP protocols
                document.querySelectorAll('img[orig]:not([data-fixed])').forEach(img => {
                    let origUrl = img.getAttribute('orig');
                    if (origUrl) {
                        // Ensure it uses HTTPS to prevent mixed-content blocking
                        origUrl = origUrl.replace(/http:\\/\\/html\\.scribd\\.com/gi, 'https://html.scribdassets.com');
                        img.src = origUrl;
                    }
                    img.setAttribute('data-fixed', 'true');
                    
                    // Force the images to display immediately
                    img.style.display = 'block';
                    img.style.opacity = '1';
                    img.style.visibility = 'visible';
                });
                
                // Remove blur applied to hidden pages
                document.querySelectorAll('.blurred_page').forEach(el => {
                    el.classList.remove('blurred_page');
                });

                // Decode base64 links into standard HTML 'href' tags for the PDF
                document.querySelectorAll('a[orig]:not([data-fixed])').forEach(a => {
                    try {
                        let decoded = window.atob(a.getAttribute('orig'));
                        
                        // Strip potential javascript/file prefixes
                        decoded = decoded.replace(/^j[\\W]*a[\\W]*v[\\W]*a[\\W]*s[\\W]*c[\\W]*r[\\W]*i[\\W]*p[\\W]*t[\\W]*:|^f[\\W]*i[\\W]*l[\\W]*e[\\W]*:/gi, "");
                        
                        if (decoded.startsWith('page')) {
                            // Internal link to another page (e.g., #page27)
                            a.href = '#' + decoded;
                        } else {
                            // External web link
                            if (!decoded.match(/^(http|https|ftp):/i)) {
                                decoded = 'https://' + decoded;
                            }
                            a.href = decoded;
                        }
                    } catch (e) {
                        console.error("Failed to decode link:", e);
                    }
                    a.setAttribute('data-fixed', 'true');
                });
            };

            // 2. Set up the MutationObserver to watch the DOM continuously for dynamically loaded pages
            const observer = new MutationObserver(window.processDynamicContent);
            observer.observe(document.body, { childList: true, subtree: true });
            
            // 3. Run immediately for existing content (Pages 1-3)
            window.processDynamicContent();

            // 4. Force Scribd to load all deferred pages (Triggers downloads for Pages 4+)
            if (window.docManager) {
                const count = window.docManager.pageCount();
                for (let i = 1; i <= count; i++) {
                    const p = window.docManager.pages[i];
                    if (p && !p.loadHasStarted) {
                        p.load(); // This fires off background requests
                    }
                }
            }
        """)

        print("Waiting for Scribd to download and insert all missing pages...")
        # Wait until Scribd's internal engine confirms every single page is fully built in the DOM
        await page.wait_for_function("""() => {
            if (!window.docManager) return true;
            const count = window.docManager.pageCount();
            for (let i = 1; i <= count; i++) {
                const p = window.docManager.pages[i];
                // If a page hasn't finished loading its inner element, keep waiting
                if (p && (!p.innerPageElem || p.currentlyLoading)) {
                    return false;
                }
            }
            return true;
        }""", timeout=90000)

        print("Waiting for images and fonts to finish downloading...")
        # Wait until there is no active network traffic downloading images/fonts
        await page.wait_for_load_state("networkidle", timeout=90000)
        
        # One final manual delay to ensure the browser has rendered everything on the canvas
        await page.wait_for_timeout(3000)

        print("Injecting CSS to hide the webpage UI and format for PDF...")
        custom_css = """
            @page {
                margin: 0;
            }
            body, html {
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
            }
            /* Hide UI toolbars, buttons, overlays, and footers */
            .toolbar_drop, .mobile_overlay, .global_header, 
            .banner, .footer, #fb-root, .header {
                display: none !important;
            }
            /* Override virtual scroller hiding logic */
            .auto__embeds_new_show, .document_scroller, .document_container, .outer_page_container {
                height: auto !important;
                overflow: visible !important;
                position: static !important;
            }
            .outer_page {
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                position: relative !important;
                page-break-after: always !important;
                break-after: page !important;
                margin: 0 !important;
                box-shadow: none !important;
                border: none !important;
            }
            /* CRITICAL: Force images to be fully opaque and visible */
            .image_layer .absimg, img.absimg {
                display: block !important;
                opacity: 1 !important;
                visibility: visible !important;
            }
            /* Keep links clickable above text/images */
            .link_layer a {
                z-index: 100 !important;
            }
        """
        await page.add_style_tag(content=custom_css)

        # Extract the exact width and height of the first page to size the PDF perfectly
        dimensions = await page.evaluate("""() => {
            const page = document.querySelector('.outer_page');
            return {
                width: page ? (page.style.width || page.offsetWidth + 'px') : '902px',
                height: page ? (page.style.height || page.offsetHeight + 'px') : '1274px'
            };
        }""")

        print(f"Generating PDF with dimensions: {dimensions['width']} x {dimensions['height']}...")
        await page.pdf(
            path=output_pdf_path,
            width=dimensions['width'],
            height=dimensions['height'],
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
        )
        
        await browser.close()
        print(f"Success! Saved PDF to: {output_pdf_path}")

# --- Execution ---
if __name__ == "__main__":
    # Change these paths to match where your files are located
    INPUT_HTML = "rtl9210b.htm" 
    OUTPUT_PDF = "rtl9210b_with_links_with_images.pdf"
    
    asyncio.run(convert_scribd_html_to_pdf(INPUT_HTML, OUTPUT_PDF))