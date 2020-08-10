# tcg_price_automor.py - Gets the "real-est" price for inventory of TCG cards and lists them appropriately

import time
import csv
import traceback
import requests
import sys
import webbrowser
from selenium import webdriver
# from tkinter import *
# from tkinter import font as tkFont
# from datetime import datetime
# from datetime import timedelta


class Card:
    def __init__(self, name, number, edition, condition, current_price, real_price, money_change, percent_change):
        self.name = name
        self.number = number
        self.edition = edition
        self.condition = condition
        self.current_price = current_price
        self.real_price = real_price
        self.money_change = money_change
        self.percent_change = percent_change


def read_csv():
    # Read records into CSV
    records = []
    with open('inventory.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skips the header
        for row in reader:
            records.append(Card(row[0], row[1], row[2],
                                row[3], row[4], row[5], row[6], row[7]))
    return records


def write_csv(cards):
    # Store records into CSV file
    with open('listing.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Card Name', 'Setcode', 'Edition', 'Condition',
                         'Current Price', 'Real-est\u2122 Price', '$ Change', '% Change'])
        for card in cards:
            writer.writerow([card.name, card.number, card.edition,
                             card.condition, card.current_price, card.real_price, card.money_change, card.percent_change])


def determine_real_price(name, number, condition, edition):
    # Scrape TCG Player site first page listing to determine real-est price
    print(f'Determining real-est price for card: {name} / {number}')
    # Using Selenium to select dynamic content
    url = 'https://shop.tcgplayer.com/yugioh/product/show?advancedSearch=true&Number='
    driver = webdriver.Chrome()
    driver.get(url + number)
    # Click on first element of search results, assuming that there is only ONE item in list
    driver.find_elements_by_class_name('product__image')[0].click()
    time.sleep(1)
    filter_by_condition(driver, condition)
    time.sleep(1)
    product_listings = driver.find_elements_by_class_name('product-listing')
    print(product_listings)
    running_price = 0
    running_quantity = 0
    for product in product_listings:
        edition = product.find_element_by_class_name(
            'product-listing__condition').text
        filter_by_edition(edition)
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
    print(f'Price={running_price}, quantity={running_quantity}')
    real_price = round(running_price/running_quantity, 2)
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


def automate_price():
    print('Starting price automation script')
    listing = []
    inventory = read_csv()
    for card in inventory:
        real_price = determine_real_price(
            card.name, card.number, card.condition, card.edition)
        # Positive value means price increased, negative means price decreased
        money_change = determine_money_change(
            float(card.current_price), real_price)
        percent_change = determine_percent_change(
            float(card.current_price), real_price)
        listing.append(Card(card.name, card.number, card.edition,
                            card.condition, card.current_price, real_price, money_change, percent_change))
    write_csv(listing)
    print('Finished price automation script')
    # TODO: Update the current_price someplace


# Run program
automate_price()
