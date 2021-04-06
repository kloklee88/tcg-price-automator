# tcg_price_automor.py - Gets the "real-est" price for inventory of TCG cards and lists them appropriately

import time
import csv
import traceback
import requests
import sys
import webbrowser
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from datetime import timedelta
from tkinter import *
from tkinter import ttk, filedialog
from ttkthemes import ThemedTk, ThemedStyle
from PIL import Image, ImageTk
import getpass
import logging

logging.basicConfig(level=logging.INFO, filename="logfile", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

class Card:
    def __init__(self, name, number, edition, condition, quantity, current_price, real_price, money_change, percent_change, link_option, unique_link, notes):
        self.name = name
        self.number = number
        self.edition = edition
        self.condition = condition
        self.quantity = quantity
        self.current_price = current_price
        self.real_price = real_price
        self.money_change = money_change
        self.percent_change = percent_change
        self.link_option = link_option
        self.unique_link = unique_link
        self.notes = notes


def read_csv(filepath):
    # Read records into CSV
    logging.info(f'Reading CSV from {filepath}')
    records = []
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skips the header
        for row in reader:
            records.append(Card(row[0], row[1], row[2],
                                row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11]))
    return records


def write_csv(csv_name, cards):
    # Store records into CSV file
    with open(csv_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Card Name', 'Setcode', 'Edition', 'Condition', 'Quantity',
                         'Current Price', 'Real-est\u2122 Price', '$ Change', '% Change', 'Link Option', 'Unique Link', 'Notes'])
        for card in cards:
            writer.writerow([card.name, card.number, card.edition,
                             card.condition, card.quantity, card.current_price, card.real_price, card.money_change, card.percent_change, card.link_option, card.unique_link, card.notes])


def determine_real_price(driver, name, condition, edition):
    filter_by_condition(driver, condition)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'product-listing'))
    )
    product_listings = driver.find_elements_by_class_name('product-listing')
    #logging.info(product_listings)
    running_price = 0
    running_quantity = 0
    running_price_1st = 0
    running_quantity_1st = 0
    running_price_unlimited = 0
    running_quantity_unlimited = 0
    # If less than unique individual seller, stop processing
    if len(product_listings) < 8:
        return -8
    for product in product_listings:
        condition_edition = product.find_element_by_class_name(
            'product-listing__condition').text
        edition_parsed = filter_by_edition(condition_edition)
        #if edition_parsed == edition:
            # TODO: finish filtering by edition
        price = float(product.find_element_by_class_name(
            'product-listing__price').text.replace('$', ''))
        shipping = float(product.find_element_by_class_name('product-listing__shipping').text.replace(
            'Free Shipping on Orders Over $5', '').replace('+ Shipping:', '').replace('Included', '0').replace('$', ''))
        total_price = price + shipping
        quantity = int(product.find_element_by_id(
            'quantityAvailable').get_attribute('value'))
        # logging.info(price)
        # logging.info(shipping)
        # logging.info(total_price)
        # logging.info(quantity)
        running_price += total_price*quantity
        running_quantity += quantity
        if '1st Edition' in condition_edition:
            running_price_1st += total_price*quantity
            running_quantity_1st += quantity
        elif 'Unlimited' in condition_edition:
            running_price_unlimited += total_price*quantity
            running_quantity_unlimited += quantity
    logging.info(f'Normal -> Price={running_price}, quantity={running_quantity}')
    logging.info(f'1st -> Price={running_price_1st}, quantity={running_quantity_1st}')
    logging.info(f'Unlimited -> Price={running_price_unlimited}, quantity={running_quantity_unlimited}')
    # If total quantity between all sellers is below 15, stop processing
    if running_quantity < 12:
        return -12
    real_price = round(running_price/running_quantity, 2)
    if running_quantity_1st != 0:
        real_price_1st = round(running_price_1st/running_quantity_1st, 2)
        logging.info(f'Real Price 1st: {real_price_1st}')
    if running_quantity_unlimited != 0:
        real_price_unlimited = round(running_price_unlimited/running_quantity_unlimited, 2)
        logging.info(f'Real Price Unlimited: {real_price_unlimited}')
    logging.info(f'Real Price: {real_price}')
    return real_price


def filter_by_edition(edition):
    if '1st Edition' in edition:
        edition_parsed = '1st Edition'
    elif 'Unlimited' in edition:
        edition_parsed = 'Unlimted'
    return edition_parsed


def filter_by_condition(driver, condition):
    if condition == 'Near Mint':
        i = 2
    elif condition == 'Lightly Played':
        i = 3
    elif condition == 'Moderately Played':
        i = 4
    elif condition == 'Heavily PLayed':
        i = 5
    elif condition == 'Damaged':
        i = 6
    elif condition == 'Unopened':
        i = 7
    driver.find_element_by_xpath(
        f'//*[@id="detailsFilters"]/div/div/ul[4]/li[{i}]/a')


def determine_money_change(original, new):
    return round(new - original, 2)


def determine_percent_change(original, new):
    return round((new-original)/original, 2)

def automate_price(filepath, use_new_records, progress_bar, progress_percent):
    logging.info('Starting price automation script')
    start_time = datetime.now()
    progress_value = 0
    try:
        listing = []
        inventory = read_csv(filepath)
        for i,card in enumerate(inventory):
            # Keep track of progress bar
            progress_value = i/len(inventory)*100
            progress_bar['value'] = progress_value
            progress_percent['text'] = f'{round(progress_value,2)}%'
            logging.info(f'Progress value: {progress_value}')
            # Only process if use_new_records is false OR if new record and the card name is empty
            logging.info(f'Only using new records: {use_new_records}')
            if (use_new_records and not card.name) or not use_new_records:
                # Use either the unique URL from CSV or construct it for first time
                url = None
                notes = None
                if not card.unique_link:
                    url = 'https://www.tcgplayer.com/search/yugioh/product?Number=' + card.number
                else:
                    url = card.unique_link
                logging.info(f'URL searched: {url}')
                # Scrape TCG Player site first page listing to determine real-est price
                logging.info(f'Determining real-est price for card: {card.number}')
                # Using Selenium to select dynamic content
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                unique_url = None
                updated_card_name = None
                item_num = 0
                if not card.unique_link:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'search-result__product'))
                    )
                    item_num = len(driver.find_elements_by_class_name('search-result__product'))
                    logging.info(f'Number of items on search page: {item_num}')
                if item_num > 1 and not card.unique_link:
                    real_price = 0
                    notes = 'Multiple links when searching. Requires user selection'
                else:
                    # Click on first element of search results, assuming that there is only ONE item in list
                    if not card.unique_link:
                        driver.find_elements_by_class_name('search-result__product')[0].click()
                    unique_url = driver.current_url
                    if not card.name:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'product-details__name'))
                        )
                        updated_card_name = driver.find_elements_by_class_name('product-details__name')[1].text
                        #logging.info(driver.find_elements_by_class_name('product-details__name')[0])
                        logging.info(f'Getting card name: {updated_card_name}')
                        card.name = updated_card_name
                    if not card.condition:
                        logging.info(f'Filling in Near Mint')
                        card.condition = 'Near Mint'
                    if not card.edition:
                        logging.info(f'Filling in 1st Edition')
                        card.edition = '1st Edition'
                    real_price = determine_real_price(driver, card.name, card.condition, card.edition)
                logging.info(f'Unique URL: {unique_url}')
                if real_price == -12:
                    real_price = 0
                    notes = 'Total quantity less than 12'
                elif real_price == -8:
                    real_price = 0
                    notes = 'Less than 8 unique sellers'
                elif real_price < 1.03 and not notes:
                    real_price = 1.03
                    notes = 'Price floor was applied for this card'
                driver.close()
                # Positive value means price increased, negative means price decreased. Only output if current price exist
                money_change = 0
                percent_change = 0
                if card.current_price:
                    money_change = determine_money_change(
                        float(card.current_price), real_price)
                    percent_change = determine_percent_change(
                        float(card.current_price), real_price)
                listing.append(Card(card.name, card.number, card.edition,
                                    card.condition, card.quantity, card.current_price, real_price, money_change, percent_change, url, unique_url, notes))
            message = 'Inventory prices have been updated!\n'
    except Exception as e:
        logging.exception("ERROR! did not complete scraping")
        message = 'ERROR! Did not fully complete determining price\n'
    finally:
        completion_time = datetime.now() - start_time
        logging.info(f'Time to complete (seconds): {completion_time.seconds}')
        write_csv('output.csv', listing)
        if driver:
            driver.quit()
        progress_value = 100
        logging.info('Finished price automation script')
        return message

def upload_tcg(filepath):
    logging.info('Starting uploading to TCG Player')
    start_time = datetime.now()
    url = 'https://store.tcgplayer.com/login?returnUrl=www.tcgplayer.com/'
    driver = webdriver.Chrome()
    driver.get(url)
    # Sign in
    #email = driver.find_elements_by_id('Email')
    #password = driver.find_elements_by_id('Password')
    #email.send_keys('username') 
    #password.send_keys('password')
    # Make selenium user pause here
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'Email'))
    )
    WebDriverWait(driver, 10).until(lambda driver: driver.find_elements_by_class_name('test'))
    try:
        listing = []
        inventory = read_csv(filepath)
        #for i,card in enumerate(inventory):
        #    logging.info('TEST')
        message = 'Listings have been uploaded to TCG!'
    except Exception as e:
        logging.exception("ERROR! did not complete upload")
        message = 'ERROR! Did not fully complete uploading to TCG\n'
    finally:
        completion_time = datetime.now() - start_time
        logging.info(f'Time to complete upload (seconds): {completion_time.seconds}')
        #progress_value = 100
        logging.info('Finished upload automation script')
        return message


###################
# GUI 
###################
class Window(Frame):
    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)         
        self.master = master
        self.init_window()

    def init_window(self, side=LEFT, anchor=W):
        self.master.title('TCG Price Automator')
        photo = PhotoImage(file ='upstart_goblin.png')
        self.master.iconphoto(False, photo)
        self.pack(fill=BOTH, expand=1)

        self.content = ttk.Frame(self, padding=(5,5,5,5))
        self.content.pack(fill=BOTH, expand=1)

        #pic = Image.open("background_dragon.png")
        #pic = pic.resize((400,350), Image.ANTIALIAS)
        #bg_image = ImageTk.PhotoImage(pic)
        #background_label = ttk.Label(self.content, image=bg_image)
        #background_label.place(x=0,y=0, relwidth=1, relheight=1)
        #background_label.image = bg_image

        self.filepath = StringVar(value='inventory-new.csv')
        self.response = StringVar()
        self.determine_price = IntVar(value=1)
        self.upload_tcg = IntVar(value=0)
        self.use_new_records = IntVar(value=0)

        self.choose_file_frame = ttk.Frame(self.content)
        self.choose_file_frame.place(relx=0.5, rely=0.1, anchor=CENTER)
        self.choose_file_entry = ttk.Entry(self.choose_file_frame, textvariable=self.filepath, width=30)
        self.choose_file_entry.grid(row=0,column=0,sticky=W)
        ttk.Button(self.choose_file_frame, text='Choose CSV File', command=self.choose_file).grid(row=0,column=1,sticky=W)

        ttk.Label(self.content, text='').grid(row=1,column=0,sticky=W)
        self.labelframe = ttk.LabelFrame(self.content, text='Options')
        self.labelframe.place(relx=0.5, rely=0.3, anchor=CENTER)
        ttk.Checkbutton(self.labelframe, text='Determine Price', variable=self.determine_price).grid(row=1,column=0,sticky=W)
        ttk.Checkbutton(self.labelframe, text='Upload to TCG', variable=self.upload_tcg).grid(row=2,column=0,sticky=W)
        ttk.Checkbutton(self.labelframe, text='Use only new records', variable=self.use_new_records).grid(row=3,column=0,sticky=W)
        
        self.progress = ttk.Progressbar(self.content, length=350, mode='determinate')
        self.progress.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.progress_percent = ttk.Label(self.content, text='')
        self.progress_percent.place(relx=0.5, rely=0.575, anchor=CENTER)

        ttk.Label(self.content, textvariable=self.response).place(relx=0.5, rely=0.7, anchor=CENTER)

        ttk.Button(self.content, text='Run',command=self.process, width=15).place(relx=0.5, rely=0.85, anchor=CENTER)
        #tk.Button(self.content, text='Exit',command=self.client_exit, width=15).place(relx=0.5, rely=0.95, anchor=CENTER)
    
    def choose_file(self):
        filename = filedialog.askopenfilename(filetypes = (("CSV", "*.csv"), ("All files", "*")))
        logging.info(filename)
        self.choose_file_entry.delete(0, END)
        self.choose_file_entry.insert(0, filename)

    def client_exit(self):
        exit()

    def run(self):
        result = ''
        self.response.set(result)
        if not self.choose_file_entry.get():
            logging.info('Inventory entry is empty')
            self.response.set('Inventory CSV is empty! Please choose a file!!')
            return
        if self.determine_price.get(): 
            result += automate_price(self.choose_file_entry.get(), self.use_new_records.get(), self.progress, self.progress_percent) # Pass CSV filepath
        if self.upload_tcg.get() and 'ERROR' not in result:
            result += upload_tcg('output.csv')
        self.progress_percent['text']='100%'
        self.progress['value']=100
        self.response.set(result)

    def process(self):
        control_thread = threading.Thread(target=self.run, daemon=True)
        control_thread.start()
        

root = Tk()
root.geometry("400x350")
root.style = ThemedStyle()
logging.info(f'Available themes: {root.style.theme_names()}')
root.style.theme_use("scidblue")
app = Window(root)
root.mainloop()