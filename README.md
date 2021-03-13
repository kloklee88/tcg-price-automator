# TCG Price Automator
## Overview
The TCG Price Automator does the following:
(1) Takes inventory of Yugioh cards and determines the Realnumber<sup>TM</sup> price by using data from the TCG Player online store.
(2) IN PROGRESS - connects to TCG player and upload prices

### Running on your own computer
No Python installation is necessary, you just need to ensure that you have the "dist" folder on your system. The output CSV will be spit out in the same folder as the tcg_price_automator.exe. The starting inventory CSV can be anywhere on the system as specified in the file select field.

Inside the dist folder, double click the tcg_price_automator.exe and let the script do the rest!!

> Note: You may need to install a different chromedriver.exe that matches your current version of Chrome [here](https://chromedriver.chromium.org/downloads). Make sure to place this in dist folder!

## Developer Info
Built in Python using the following workflow:

![alt text](https://github.com/kloklee88/tcg-price-automator/blob/master/tcg-workflow.PNG?raw=true)

Latest Lucidcharts here:
https://app.lucidchart.com/lucidchart/ae0400e0-e3b3-4057-98f3-f24a8d2cafea/edit?page=0_0#

### Installation (ONLY REQUIRED IF YOU WANT TO WORK ON PROJECT)
Install latest version of [Python](https://www.python.org/downloads/) 

Navigate to the folder of the apple_product_scraper in command line/terminal

```sh
$ cd "C:\Users\folder-path-to\tcg-price-automator"
```

Install dependencies from requirement.txt

```sh
$ pip install -r requirements.txt
```

Run the following command to execute script

```sh
$ py tcg_price_automator.py
```

> Note: You may need to install a different chromedriver.exe that matches your current version of Chrome [here](https://chromedriver.chromium.org/downloads). Make sure to place this in the same folder as apple_product_scraper!


