import zipfile
from pathlib import Path

from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP                   # Should use request
from RPA.Tables import Tables, Table        # should use built-in tools
from RPA.PDF import PDF

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    browser.configure(
        slowmo=100,
    )

    orders = get_orders()

    open_robot_order_website()

    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        screenshot = screenshot_robot(order['Order number'])
        pdf_file = store_receipt_as_pdf(order['Order number'])
        embed_screenshot_to_receipt(screenshot, pdf_file)
        proceed_to_next_order()
    
    archive_receipts()

def open_robot_order_website():
    url="https://robotsparebinindustries.com/#/robot-order"
    browser.goto(url)

def get_orders() -> Table:
    url = 'https://robotsparebinindustries.com/orders.csv'
    HTTP().download(url=url, overwrite=True)
    tables = Tables()
    orders = tables.read_table_from_csv(path='orders.csv')
    return orders

def close_annoying_modal():
    page = browser.page()
    page.click("button:text('OK')")

def fill_the_form(order):
    page = browser.page()
    page.select_option('#head', order['Head'])
    page.click('#id-body-' +  order['Body'])
    page.locator("xpath=//label[contains(.,'3. Legs:')]/../input").fill(order['Legs'])
    page.fill('#address', order['Address'])
    page.click("button:text('Order')")
    while check_alert():
        page.click("button:text('Order')")

def check_alert():
    page = browser.page()
    error = page.query_selector('.alert-danger')
    if error and error.is_visible:
        return True
    return False

def store_receipt_as_pdf(order_number):
    output = f"output/pdfs/receipt{order_number}.pdf"
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, output)
    return output

def screenshot_robot(order_number):
    output = f"output/screenshots-{order_number}.png"
    page = browser.page()
    robot_image = page.query_selector('#robot-preview-image') # TODO: probably should wait for all parts being loaded and visible
    robot_image.screenshot(path=output)
    return output

def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_files_to_pdf([pdf_file, screenshot], target_document=pdf_file)

def proceed_to_next_order():
    page = browser.page()
    page.click("button:text('Order another robot')")

def archive_receipts():
    p = Path('output/pdfs/')
    
    zip_file = zipfile.ZipFile('output/robot_orders.zip', 'w', zipfile.ZIP_DEFLATED) # TODO: use with
    for file in p.glob('*.pdf'):
        zip_file.write(file)
    zip_file.close()