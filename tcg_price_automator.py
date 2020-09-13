# tcg_price_automor.py - Gets the "real-est" price for inventory of TCG cards and lists them appropriately

import time
import csv
import traceback
import requests
import sys
import webbrowser
from selenium import webdriver
from datetime import datetime
from datetime import timedelta
from tkinter import *
from tkinter import ttk, filedialog


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
    print(f'Reading CSV from {filepath}')
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
    time.sleep(1)
    filter_by_condition(driver, condition)
    time.sleep(1)
    product_listings = driver.find_elements_by_class_name('product-listing')
    #print(product_listings)
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
            'Free Shipping on Orders Over $5', '').replace('+ Shipping:', '').replace('Included', '').replace('$', ''))
        total_price = price + shipping
        quantity = int(product.find_element_by_id(
            'quantityAvailable').get_attribute('value'))
        # print(price)
        # print(shipping)
        # print(total_price)
        # print(quantity)
        running_price += total_price*quantity
        running_quantity += quantity
        if '1st Edition' in condition_edition:
            running_price_1st += total_price*quantity
            running_quantity_1st += quantity
        elif 'Unlimited' in condition_edition:
            running_price_unlimited += total_price*quantity
            running_quantity_unlimited += quantity
    print(f'Normal -> Price={running_price}, quantity={running_quantity}')
    print(f'1st -> Price={running_price_1st}, quantity={running_quantity_1st}')
    print(f'Unlimited -> Price={running_price_unlimited}, quantity={running_quantity_unlimited}')
    # If total quantity between all sellers is below 15, stop processing
    if running_quantity < 15:
        return -15
    real_price = round(running_price/running_quantity, 2)
    if running_quantity_1st != 0:
        real_price_1st = round(running_price_1st/running_quantity_1st, 2)
        print(f'Real Price 1st: {real_price_1st}')
    if running_quantity_unlimited != 0:
        real_price_unlimited = round(running_price_unlimited/running_quantity_unlimited, 2)
        print(f'Real Price Unlimited: {real_price_unlimited}')
    print(f'Real Price: {real_price}')
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


def automate_price(filepath):
    print('Starting price automation script')
    start_time = datetime.now()
    try:
        listing = []
        inventory_new = []
        inventory = read_csv(filepath)
        for card in inventory:
            # Use either the unique URL from CSV or construct it for first time
            url = None
            notes = None
            if not card.unique_link:
                url = 'https://shop.tcgplayer.com/yugioh/product/show?advancedSearch=true&Number=' + card.number
            else:
                url = card.unique_link
            print(f'URL searched: {url}')
            # Scrape TCG Player site first page listing to determine real-est price
            print(f'Determining real-est price for card: {card.name} / {card.number}')
            # Using Selenium to select dynamic content
            driver = webdriver.Chrome()
            driver.get(url)
            unique_url = None
            item_num = len(driver.find_elements_by_class_name('product__image'))
            print(f'Number of items on search page: {item_num}')
            if item_num > 1:
                real_price = 0
                notes = 'Multiple links when searching. Requires user selection'
            else:
                # Click on first element of search results, assuming that there is only ONE item in list
                driver.find_elements_by_class_name('product__image')[0].click()
                unique_url = driver.current_url
                real_price = determine_real_price(driver, card.name, card.condition, card.edition)
            print(f'Unique URL: {unique_url}')
            if real_price == -15:
                real_price = 0
                notes = 'Total quantity less than 15'
            elif real_price == -8:
                real_price = 0
                notes = 'Less than 8 unique sellers'
            elif real_price < 1.03:
                real_price = 1.03
                notes = 'Price floor was applied for this card'
            # Positive value means price increased, negative means price decreased
            money_change = determine_money_change(
                float(card.current_price), real_price)
            percent_change = determine_percent_change(
                float(card.current_price), real_price)
            listing.append(Card(card.name, card.number, card.edition,
                                card.condition, card.quantity, card.current_price, real_price, money_change, percent_change, url, unique_url, notes))
    except Exception as e:
        print("ERROR! did not complete scraping")
        print(e)
        traceback.print_exc()
    finally:
        completion_time = datetime.now() - start_time
        print(f'Time to complete (seconds): {completion_time.seconds}')
        write_csv('listing.csv', listing)
        write_csv('inventory-new.csv', inventory_new)
        print('Finished price automation script')
        return True

def upload_tcg():
    print('Uploading to TCG Player...')
    # TODO: Need to get the quantity update from TCG API
    #inventory_new.append(Card(card.name, card.number, card.edition,
    #                          card.condition, card.quantity, real_price, 0, 0, 0, url, unique_url, notes))
    return True


###################
# GUI 
###################
class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)                 
        self.master = master
        self.init_window()

    def init_window(self, side=LEFT, anchor=W):
        self.master.title("TCG Price Automator")
        self.pack(fill=BOTH, expand=1)
        self.filepath = StringVar(value='')
        self.response = StringVar()
        self.determine_price = IntVar(value=1)
        self.upload_tcg = IntVar(value=1)
        ttk.Label(self, text="Inventory CSV:").grid(row=0,column=0,sticky=W)
        self.choose_file_entry = ttk.Entry(self, textvariable=self.filepath, width=30)
        self.choose_file_entry.grid(row=0,column=1,sticky=W)
        ttk.Button(self, text="Choose File", command=self.choose_file).grid(row=0,column=2,sticky=W)

        ttk.Label(self, text="Options:").grid(row=1,column=0,sticky=W)
        ttk.Checkbutton(self, text='Determine Price', variable=self.determine_price).grid(row=2,column=0,sticky=W)
        ttk.Checkbutton(self, text='Upload to TCG', variable=self.upload_tcg).grid(row=3,column=0,sticky=W)

        ttk.Label(self, textvariable=self.response).place(relx=0.5, rely=0.6, anchor=CENTER)

        ttk.Button(self, text="Run",command=self.run, width=15).place(relx=0.5, rely=0.7, anchor=CENTER)
        ttk.Button(self, text="Exit",command=self.client_exit, width=15).place(relx=0.5, rely=0.8, anchor=CENTER)
    
    def choose_file(self):
        filename = filedialog.askopenfilename(filetypes = (("CSV", "*.csv"), ("All files", "*")))
        print(filename)
        self.choose_file_entry.delete(0, END)
        self.choose_file_entry.insert(0, filename)

    def client_exit(self):
        exit()

    def run(self):
        result = ''
        if not self.choose_file_entry.get():
            print('Inventory entry is empty')
            self.response.set('Inventory CSV is empty! Please choose a file!!')
            return
        if self.determine_price.get():
            completed_price = automate_price(self.choose_file_entry.get()) # Pass CSV filepath
            if completed_price == True:
                result += 'Inventory prices have been updated!\n'
        if self.upload_tcg.get():
            completed_upload = upload_tcg()
            if completed_upload == True:
                result += 'Listings have been uploaded to TCG!'
        self.response.set(result)
        

root = Tk()
root.geometry("400x250")
root.style = ttk.Style()
root.style.theme_use("vista")
app = Window(root)
root.mainloop() 