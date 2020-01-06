# TransferMarketCrawler

crawl data from www.transfermarkt.com: foreigners and natives of first-tier leagues of 66 countries in 10 seasons(2009-2018)

## Prerequisites
+ python 3

## Install
+ `pip install requests`
+ `pip install beautifulsoup4`

## Details
The data includes:
+ league info
+ number of natives
+ list of all foreigners

The data will store as 'data_by_country.json',and save data every time a country is acquired,you can continue crawling after getting part of data
