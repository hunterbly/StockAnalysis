import itertools

import psycopg2
import psycopg2.extras
import sys
import requests
from bs4 import BeautifulSoup
import time
import datetime
from utils.logger import setup_logger
from requests.exceptions import ConnectionError

import numpy as np
import copy
import re
import pandas as pd
import os
from urllib3.exceptions import ReadTimeoutError, ConnectTimeoutError

__all__ = 'CCASS'
logger = setup_logger(__all__)

def check_web_availability(date):
    """
    Send single request to web to see if the latest data is available

    Args:
        date (DateTime): Date time object 

    Returns:
        real_date (DateTime): Real date listed on the web in python datetime format
    """

    logger.info("Checking if data is available - 00001")

    session_data = get_session_data()
    page_source = get_html(date, '00001', copy.deepcopy(session_data))
    soup = BeautifulSoup(page_source, 'html.parser')

    # Get real date
    date_on_web_str = soup.find('input', {'id':'txtShareholdingDate'}).get('value')
    date_on_web_obj = datetime.datetime.strptime(date_on_web_str, '%Y/%m/%d').date()

    check_text = soup.body.findAll(text='Market Intermediaries')

    if (not check_text):
        logger.info("Data for {} is not available yet. Please try again later.".format(date))
        sys.exit(0)

    elif(date != date_on_web_obj):
        logger.info("Data for {} is not available yet. Latest date on web is {}. Please try again later.".format(date, date_on_web_obj))
        sys.exit(0)
    else:
        pass

    real_date = date_on_web_obj

    return real_date

def check_db_records(date):
    """
    Check if there is records in the database, exit program if there is

    Args:
        date (DateTime): Date time object

    Returns:
        None
    """

    connection_string = "dbname='stock' user='db_user' host='" + 'localhost' + "' password='P@ssw0rDB'"
    count_stmt = "SELECT COUNT(1) FROM ccass WHERE date = '{}'".format(date)

    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        cur.execute(count_stmt)
        result = cur.fetchall()
        conn.close()

        logger.info('Checking CCASS records in Database for date - {}'.format(date))
    except:
        logger.warning("Something wrong with date checking in database. Probably no Database setup")
        result = np.nan

    if np.isnan(result):
        pass
    elif result[0][0] != 0:           # Return the first element (count) in the tuple
        logger.warning('CCASS Records exists in database for {}'.format(date))
        sys.exit()
    else:
        logger.warning('No CCASS record in Database for date - '.format(date))

    return None

def get_all_stock_quotes_from_hkexnews(purpose, date=datetime.date.today()):
    # Go to page in hkex for entire stock code list
    # logger.info('Getting stock quotes from HKEXnews')
    website_url = None
    if purpose == 'CCASS':
        website_url = r'http://www.hkexnews.hk/sdw/search/stocklist_c.aspx?SortBy=StockCode&ShareholdingDate={0:0>4}{1:0>2}{2:0>2}'.format(date.year, date.month, date.day)
    elif purpose == 'company_announcements':
        website_url = r'http://www.hkexnews.hk/listedco/listconews/advancedsearch/stocklist_active_main_c.htm'
    count = 0
    sleep_duration = [5, 10, 60, 120, 300, 600, 1200, 2400]
    while True:
        try:
            result = requests.get(website_url, timeout=10)
            break
        except ConnectionError:
            idx = int(count / 10)
            if idx >= len(sleep_duration):
                idx = len(sleep_duration) - 1
            time.sleep(sleep_duration[idx])
            count += 1
            pass

    soup = BeautifulSoup(result.content, 'html.parser')
    stock_codes = {}

    # Get each row in stock code table and add them to dictionary
    for row in soup.find_all('tr'):
        row_contents = row.contents

        # Specify the index location of the stock code and stock name in each row
        if purpose == 'CCASS':
            index_code = 1
            index_name = 3
        elif purpose == 'company_announcements':
            index_code = 0
            index_name = 1

        # If the location at the code is not a digit, skip it
        if not row_contents[index_code].text.strip().isdigit():
            continue

        # Add the stock code and stock name into the dictionary
        stock_codes[row_contents[index_code].text.strip()] = row_contents[index_name].text.replace("\n", "").strip()

    return stock_codes

def get_session_data():
    url = 'http://www.hkexnews.hk/sdw/search/searchsdw.aspx'

    logger.info('Getting session info')
    response = get_or_post_data('get', url)

    soup = BeautifulSoup(response.content, 'html.parser')
    session_data = {}
    for tag in soup.find_all('input'):
        if tag['id'] == '__VIEWSTATE' or tag['id'] == '__VIEWSTATEGENERATOR' or tag['id'] == '__EVENTVALIDATION':
            session_data[tag['id']] = tag['value']
    return session_data


def get_or_post_data(method, url, data=None, headers=None):
    # For handling block IP issues
    count = 0
    sleep_duration = [5,10,60,120,300,600,1200,2400]
    while True:
        try:
            if method == 'get':
                response = requests.get(url, timeout=10)
            elif method == 'post':
                response = requests.post(url, data=data, headers=headers, timeout=10)
            else:
                logger.info('Method NOT stated.')
                raise ConnectionAbortedError

            if response.status_code != requests.codes.ok or response is None:
                raise ConnectionAbortedError
            time.sleep(2)
            return response
        except:
            idx = int(count/10)
            if idx >= len(sleep_duration):
                idx = len(sleep_duration) - 1
            time.sleep(sleep_duration[idx])
            count += 1

def get_html(date, stock_code, data=None):

    url = 'http://www.hkexnews.hk/sdw/search/searchsdw.aspx'

    # Get session info if not available
    if data is None:
        data = get_session_data()

    # Fill in other data required by the POST request
    today = datetime.date.today()
    data['today'] = '{0:0>4}{1:0>2}{2:0>2}'.format(today.year, today.month, today.day)
    data['txtShareholdingDate'] = date.strftime("%Y/%m/%d")
    data['__EVENTTARGET'] = 'btnSearch'
    data['__EVENTARGUMENT'] = ''
    # data['ddlShareholdingDay'] = '{0:0>2}'.format(date.day)
    # data['ddlShareholdingMonth'] = '{0:0>2}'.format(date.month)
    # data['ddlShareholdingYear'] = '{0:0>4}'.format(date.year)
    data['sortDirection'] = 'desc'
    data['txtStockCode'] = stock_code
    data['sortBy'] = 'shareholding'
    data['txtselPartID'] = ''
    data['alertMsg'] = ''
    data['txtStockName'] = ''
    data['txtParticipantID'] = ''
    data['txtParticipantName'] = ''
    data['btnSearch.x'] = '42'
    data['btnSearch.y'] = '9'

    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
               'Referer': 'http://www.hkexnews.hk/sdw/search/searchsdw_c.aspx'}

    # Get response from website
    response = get_or_post_data('post', url, data=data, headers=headers)

    return response.content.decode('utf8')

def parse_data(page_source, stock_code, date):
    # Get page source
    logger.debug('Parsing page source')
    soup = BeautifulSoup(page_source, 'html.parser')

    # Initialize parameters
    all_organized_rows = []
    HEADER_COLS = ['Participant ID', 'Name of CCASS Participant(* for Consenting Investor Participants )', 'Shareholding']

    if 'No match record found' not in page_source:
        # Get all rows relating to CCASS shareholding
        # Only if there are CCASS shareholding in the first place
        logger.debug('Collecting CCASS shareholders info')

        ccass_participant_shareholding_table = soup.find('table', {'class':['table-scroll', 'table-sort', 'table-mobile-list']})

        try:
            ccass_participant_shareholding_rows = ccass_participant_shareholding_table.find_all('tr')
        except:
            return None
        for counter, row in enumerate(ccass_participant_shareholding_rows):
            if counter == 0:
                pass
            else:
                row = [i.get_text().strip() for i in row.find_all('td')]
                
                # Ensure rows are not empty or the header row
                if not row == ['']:
                    participant_id  = row[0].replace("Participant ID:\n", "")
                    name            = row[1].replace("Name of CCASS Participant (* for Consenting Investor Participants ):\n", "")
                    address         = row[2].replace("Address:\n", "")
                    shareholding    = row[3].replace("Shareholding:\n", "")
                    percentage      = row[4].replace("% of the total number of Issued Shares/ Warrants/ Units:\n", "")

                    # Remove special characters
                    shareholding    = int(shareholding.replace(",", "").replace("\n", "").strip())
                    percentage      = round(float(percentage.replace("%", ""))/100, 6)
                    row_to_add      = [participant_id, name, address, shareholding, percentage]
                
                    all_organized_rows.append(row_to_add)
                else:
                    logger.warning("Row data not available")

        logger.debug('Getting CCASS summary')

        holding_summary_rows = soup.find('div', {'class': 'ccass-search-summary-table'}).contents
        holding_summary_rows = [x for x in holding_summary_rows if not(isinstance(x, str))]  # Remove some line break

        # Parse each row of the summary table
        for counter, row in enumerate(holding_summary_rows):
          if(counter == 0):
            # Skip header row
            pass

          else:

            records = [x for x in row if not(isinstance(x, str))]  # Remove some line break
            row_to_add = None

            if(len(records) > 2):
              participant_id = "999999"
              name           = records[0].contents.pop(0).replace("\n", "").strip()
              address        = ""
              shareholding       = records[1].find("div", {"class": "value"}).contents.pop(0)
              #no_of_participants = records[2].find("div", {"class": "value"}).contents.pop(0)
              percentage         = records[3].find("div", {"class": "value"}).contents.pop(0)

              # Remove special characters
              shareholding    = int(shareholding.replace(",", "").replace("\n", "").strip())
              percentage      = round(float(percentage.replace("%", ""))/100, 6)

              row_to_add      = [participant_id, name, address, shareholding, percentage]

            elif(len(records) == 2):
              # for the total case
              participant_id = "999999"
              name           = "Total issued shares"
              address        = ""
              shareholding   = int(records[1].contents.pop(0).replace(",", "").replace("\n", "").strip())
              percentage     = 1

              row_to_add      = [participant_id, name, address, shareholding, percentage]

            all_organized_rows.append(row_to_add)
            

    # Organize data into pandas dataframe and convert
    # logger.info('Organizing data to required format.')
    HEADER_COLS = ['participant_code', 'participant', 'address', 'number', 'percentage']

    all_shareholding_df = pd.DataFrame(all_organized_rows, columns=HEADER_COLS)
    all_shareholding_df['code'] = stock_code
    all_shareholding_df['date'] = date
    
    all_shareholding_df.drop(['participant', 'address'], axis=1, inplace=True)

    return all_shareholding_df

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

    

    date_input_obj = datetime.datetime.now().date() if arg['-d'] == '' else datetime.datetime.strptime(arg['-d'], df_input).date()
    # date_input_obj = datetime.datetime.strptime('2019-05-01', df_input).date()
    logger.info("=============================================")
    logger.info("Start main function for date {}".format(date_input_obj))

    # Check if data available on web
    real_date_obj = check_web_availability(date_input_obj)
    
    # Check if data already in db
    check_db_records(real_date_obj)

    stock_codes = get_all_stock_quotes_from_hkexnews('CCASS', date = real_date_obj)
    stock_codes_sample = dict(itertools.islice(stock_codes.items(), 3))

    # Initiate session
    session_data = get_session_data()

    # Initiate result dataframe
    result = pd.DataFrame()

    for stock_code in stock_codes_sample:
        logger.info("=============================================")
        logger.info("Start parsing for code - {}".format(stock_code))

        page_source = get_html(real_date_obj, stock_code, copy.deepcopy(session_data))
        all_shareholding_df = parse_data(page_source, stock_code, real_date_obj)

        
        if(all_shareholding_df.shape[0] > 0):
        	result = result.append(all_shareholding_df)
        
        logger.info("Finished parsing for code - {}".format(stock_code))

    print(all_shareholding_df.head())
    logger.info("All done - {}".format(real_date_obj))


if __name__ == "__main__":
    main()
