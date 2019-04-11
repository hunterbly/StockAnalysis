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

import copy
import re
import pandas as pd
import os
from urllib3.exceptions import ReadTimeoutError, ConnectTimeoutError

__all__ = 'CCASS'
logger = setup_logger(__all__)

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
        stock_codes[row_contents[index_code].text.strip()] = row_contents[index_name].text.strip()

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
            logger.info('Getting response from website.')
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

def main():
    logger.info("Start main function")

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

    #date = datetime.datetime.now() if arg['-d'] == '' else datetime.datetime.strptime(arg['-d'], df_input)
    date = datetime.datetime.strptime('2019-04-03', df_input)

    stock_codes = get_all_stock_quotes_from_hkexnews('CCASS', date = date)

    session_data = get_session_data()


    stock_codes_sample = dict(itertools.islice(stock_codes.items(), 3))

    result = pd.DataFrame()

    for stock_code in stock_codes_sample:

        page_source = get_html(date, stock_code, copy.deepcopy(session_data))
        all_shareholding_df = parse_data(page_source, stock_code, date)
        print(all_shareholding_df)
        #
        # if(all_shareholding_df.shape[0] > 0):
        # 	result = result.append(all_shareholding_df)
        #
        # logger.info("Finished parsing for code - %s" % (stock_code))

def get_html(date, stock_code, data=None):

    url = 'http://www.hkexnews.hk/sdw/search/searchsdw.aspx'

    # Get session info if not available
    if data is None:
        data = get_session_data()

    # Fill in other data required by the POST request
    logger.info('Filling in other required info.')
    today = datetime.date.today()
    data['today'] = '{0:0>4}{1:0>2}{2:0>2}'.format(today.year, today.month, today.day)
    data['txtShareholdingDate'] = '2019/04/07'
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
    logger.info('Parsing page source')
    soup = BeautifulSoup(page_source, 'html.parser')

    # Initialize parameters
    all_organized_rows = []
    HEADER_COLS = ['Participant ID', 'Name of CCASS Participant(* for Consenting Investor Participants )', 'Shareholding']

    if 'No match record found' not in page_source:
        # Get all rows relating to CCASS shareholding
        # Only if there are CCASS shareholding in the first place
        logger.info('Collecting CCASS shareholders info')

        # ccass_participant_shareholding_table = soup.find('table', {'class':['table-scroll', 'table-sort', 'table-mobile-list']})

        # try:
        #     ccass_participant_shareholding_rows = ccass_participant_shareholding_table.find_all('tr')
        # except:
        #     return None
        # for counter, row in enumerate(ccass_participant_shareholding_rows):
        #     if counter == 0:
        #         pass
        #     else:
        #         row = [i.get_text().strip() for i in row.find_all('td')]
        #         print(row)

        #         # Ensure rows are not empty or the header row
        #         if not row == ['']:
        #             participant_id  = row[0].replace("Participant ID:\n", "")
        #             name            = row[1].replace("Name of CCASS Participant (* for Consenting Investor Participants ):\n", "")
        #             address         = row[2].replace("Address:\n", "")
        #             shareholding    = row[3].replace("Shareholding:\n", "")
        #             percentage      = row[4].replace("% of the total number of Issued Shares/ Warrants/ Units:\n", "")
                    
        #             # Remove special characters
        #             shareholding    = int(shareholding.replace(",", ""))
        #             percentage      = round(float(percentage.replace("%", ""))/100, 4)

        #             row_to_add      = [participant_id, name, address, shareholding, percentage]
        #             print(row_to_add)
        #             all_organized_rows.append(row_to_add)
        #         else:
        #             logger.warning("Row data not available")
            
    logger.info('Getting CCASS summary')

    holding_summary_rows = soup.find('div', {'class': 'ccass-search-summary-table'}).contents
    holding_summary_rows = [x for x in holding_summary_rows if not(isinstance(x, str))]

    # Parse each row of the summary table
    for row in holding_summary_rows:
        print(row)
        ## <<-- Up to here
        organized_row = [re.sub(' +', ' ', i.get_text().strip().replace('\n', '')) for i in row.find_all('td')]

        # Unnamed CCASS Shareholding
        if organized_row[0] == 'Non-consenting Investor Participants':
            all_organized_rows.append(['', 'Unnamed CCASS Shareholding', organized_row[1]])

        # Calculate non-CCASS shareholding
        elif organized_row[0] == 'Total':
            total_ccass = int(organized_row[1].replace(',', ''))
        elif organized_row[0].startswith('Total number of Issued Shares/Warrants/Units') or organized_row[0].startswith('Total number of A Shares listed and traded on the SSE/SZSE'):
            # Ensure total CCASS shareholding is found, if not assume amount is 0.
            # Normally this amount will not be 0 since the 'Total' row must come before
            # the 'Total number of Issued Shares/Warrants/Units (last updated figure)' row
            # With the only exception that there is no 'Total' row at all,
            # which means all shares are held by non-CCASS participants
            try:
                total_ccass
            except NameError:
                total_ccass = 0
            all_organized_rows.append(['', 'Non-CCASS Shareholding', int(organized_row[1].replace(',', '')) - total_ccass])

    # Organize data into pandas dataframe and convert
    logger.info('Organizing data to required format.')
    all_shareholding_df = pd.DataFrame(all_organized_rows, columns=HEADER_COLS)
    all_shareholding_df['Shareholding'] = all_shareholding_df['Shareholding'].apply(lambda x: int(str(x).replace(',', '')))
    all_shareholding_df['Stock Code'] = stock_code
    all_shareholding_df['Date'] = date

    return all_shareholding_df

if __name__ == "__main__":
    main()
