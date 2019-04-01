import requests
import pandas as pd
import quandl
import numpy as np
import re
import psycopg2
import psycopg2.extras
from datetime import datetime
from utils.logger import setup_logger
import sys

__all__ = 'Quandl Stock'
logger = setup_logger(__all__)

result = pd.DataFrame()
quandl.ApiConfig.api_key = "nNXFy-SJNtuz6mvifMe3"

def check_availability(date):
    """ 
    Send single request to API to see if the latest data is available 
    
    Args:
        date (str): Date in YYYY-MM-DD format. Must be within the latest 10 days

    Returns:
        None
    """
    
    logger.info("Checking if data is available")

    data = get_stock(num = 1, nrow = 10)
    date_list = data.index.tolist()

    if datetime.strptime(date, '%Y-%m-%d') not in date_list:
        logger.info("Data for {} is not available yet. Please try again later".format(date))
        sys.exit(0)

    return None

def get_list():
    
    """
    Get a full list of stock code with those with option at the front

    Args:
        None

    Returns:
        stockList (List[str]): List of stock codes

    Example:
        stock_list = get_list()

    Data preview:
        [1, 2, 3, 4, 5, 6, 11,..]
    """

    # Define list of sequence for stock
    stockList = [1,2,3,4,5,6,11,12,16,17,19,23,27,66,135,151,175,267,293,330,358,386,388,390,489,494,688,700,728,762,823,857,883,902,914,939,941,992,998,1044,1088,1109,1113,1171,1186,1211,1288,1299,1336,1339,1359,1398,1800,1816,1880,1898,1919,1928,1988,2018,2038,2282,2318,2319,2328,2333,2388,2600,2601,2628,2777,2800,2822,2823,2827,2828,2888,2899,3323,3328,3800,3888,3968,3988,6030]
    stockListAll = list(range(1,4000)) + list(range(4601,4609)) + list(range(6030,6031)) + list(range(6099,6900))
    stockListNotOption = [x for x in stockListAll if x not in stockList]
    stockList.extend(stockListNotOption)

    return(stockList)

def get_stock(num, nrow = 10):

    """
    Call Quandl API to get the historical data for the stock number

    Args:
        num (num): Stock num 
        nrow (num): No of rows specified in the API calls. Default 10

    Returns:
        data (Dataframe): Dataframe returned from Quandl API

    Example:
        data = get_stock(num = 1, nrow = 10)

    Data preview:
                    NominalPrice NetChange Change    Bid    Ask   PEx   High    Low  PreviousClose  ShareVolume000  Turnover000 LotSize   code
        Date
        2019-03-19         80.45      None   None  80.40  80.45  None  81.15  80.20          80.95          7374.0     593781.0    None  00001
        2019-03-20         82.50      None   None  82.50  82.55  None  83.30  80.30          80.45         12420.0    1018144.0    None  00001
        2019-03-21         81.60      None   None  81.60  81.75  None  83.50  81.60          82.50         12224.0    1009254.0    None  00001
        2019-03-22         83.80      None   None  83.75  83.80  None  84.65  82.85          81.60         13478.0    1124179.0    None  00001
    """

    code        = str(num).zfill(5)
    code_str    = "HKEX/{}".format(code)

    try:
        data = quandl.get(code_str, rows = nrow)
        data['code'] = code

        col_name = data.columns.tolist()
        clean_col_name = [re.sub(r'\W+','', x) for x in col_name]
        col_dict = dict(zip(col_name, clean_col_name))

        data.rename(columns=col_dict, inplace=True)
        logger.info("Finished getting code - {}".format(code))

        return(data)

    except Exception as e:
        logger.info("No record - {}".format(code))
        print(e)
        pass

def get_all_stock(date = "", nrow = 10):

    """
    Call Quandl API to get the historical data for the stock number

    Args:
        date (str): Date in YYYY-MM-DD format if provided
        nrow (num): No of rows specified in the API calls. Default 10. None for getting all data

    Returns:
        result (Dataframe): Dataframe of the historical data of all stocks, in a particular date or all available data

    Example:
        data = get_all_stock(date = '2019-04-01', nrow = None)

    Data preview:
              date     ask     bid    open    high     low   close      volume      turnover   code
        2019-03-19   80.45   80.40   80.95   81.15   80.20   80.45   7374000.0  5.937810e+08  00001
        2019-03-20   82.55   82.50   80.45   83.30   80.30   82.50  12420000.0  1.018144e+09  00001
        2019-03-21   81.75   81.60   82.50   83.50   81.60   81.60  12224000.0  1.009254e+09  00001
    """

    stock_list = get_list()
    stock_list = stock_list[0:10]

    result = pd.DataFrame()

    for stock in stock_list:
        try:
            data   = get_stock(stock, nrow)
            result = pd.concat([result, data], sort=True)

        except Exception as e:
            print("No record")
            print(e)
            pass

    result = result.reset_index()
    
    # Rename column
    old_col = result.columns.values.tolist()
    new_col = ['date', 'ask', 'bid', 'change', 'high', 'lot_size', 'low', 'net_change', 'close', 'pe', 'open', 'volume', 'turnover', 'code']
    rename_col_dict = dict(zip(old_col, new_col))
    result = result.rename(columns = rename_col_dict)

    # Select the column we needed
    result = result[['date', 'ask', 'bid', 'open', 'high', 'low', 'close', 'volume', 'turnover', 'code']]

    result['volume'] = result['volume'] * 1000
    result['turnover'] = result['turnover'] * 1000

    result = result.dropna()

    if(date != ""):
        result = result.loc[result.date == date]

    return(result)

def insert_to_db(df):

    connstion_string = "dbname='stock' user='postgres' host='" + 'localhost' + "' password='P@ssw0rDB'"
    df_columns = df.columns.values.tolist()
    
    # create (col1,col2,...)
    columns = ",".join(df_columns)

    # create VALUES('%s', '%s",...) one '%s' per column
    values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

    #create INSERT INTO table (columns) VALUES('%s',...)
    insert_stmt = "INSERT INTO {} ({}) {}".format('stock', columns, values)
    try:
        conn = psycopg2.connect(connstion_string)

        cur = conn.cursor()
        psycopg2.extras.execute_batch(cur, insert_stmt, df.values)
        conn.commit()
        conn.close()

        logger.info("Finished insert into stock")

    except:
        logger.warning("No database available")
    

def main():

    ######
    # Parse program arguments
    ######

    df_input = '%Y-%m-%d'

    arg = {
        '-d': '',
        '-i': '3',
        '-ip': 'localhost'
    }

    for i in range(len(sys.argv)):
        if sys.argv[i] in arg:
            arg[sys.argv[i]] = sys.argv[i+1]

    if arg['-d'] == 'All':
        date = 'All'
    else:
        date = datetime.now().strftime(df_input) if arg['-d'] == '' else datetime.strptime(arg['-d'], df_input).date().strftime(df_input)
        check_availability(date)

    ######
    # Check Availability
    ######
    

    ######
    # Get data
    ######
    
    logger.info('Getting data for date - {}'.format(date))

    if (date == 'All'):
        # Get all data if arg[-d] == All
        res = get_all_stock(date = '', nrow=None)
    else:
        res = get_all_stock(date = date)
    
    if len(res) > 0:
        insert_to_db(res)
        logger.info("Insert into database - Testing")    

    print(res)
    logger.info("Finished downloading data - {}".format(date))

if __name__ == "__main__":
    main()