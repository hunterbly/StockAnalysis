import requests
import pandas as pd
import quandl
import numpy as np
import re
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging
import sys

result = pd.DataFrame()
quandl.ApiConfig.api_key = "nNXFy-SJNtuz6mvifMe3"

def get_list()
    # Define list of sequence for stock
    stockList = [1,2,3,4,5,6,11,12,16,17,19,23,27,66,135,151,175,267,293,330,358,386,388,390,489,494,688,700,728,762,823,857,883,902,914,939,941,992,998,1044,1088,1109,1113,1171,1186,1211,1288,1299,1336,1339,1359,1398,1800,1816,1880,1898,1919,1928,1988,2018,2038,2282,2318,2319,2328,2333,2388,2600,2601,2628,2777,2800,2822,2823,2827,2828,2888,2899,3323,3328,3800,3888,3968,3988,6030]
    stockListAll = list(range(1,4000)) + list(range(4601,4609)) + list(range(6030,6031)) + list(range(6099,6900))
    stockListNotOption = [x for x in stockListAll if x not in stockList]
    stockList.extend(stockListNotOption)

    return(stockList)

def get_stock(num, nrow = 10):
    
    code        = str(num).zfill(5)
    code_str    = "HKEX/{}".format(code)

    try:
        data = quandl.get(code_str, rows = nrows)
        data['code'] = code

        col_name = data.columns.tolist()
        clean_col_name = [re.sub(r'\W+','', x) for x in col_name]
        col_dict = dict(zip(col_name, clean_col_name))

        data.rename(columns=col_dict, inplace=True)

        return(data)

    except Exception as e:
        print("No record")
        print(e)
        pass
    
def main():
    
    stock_list = get_list()
    stock_list = stock_list[1:10]


    for stock in stock_list:
        print(stock)

if __name__ == "__main__":
    main()