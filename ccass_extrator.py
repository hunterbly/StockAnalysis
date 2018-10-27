import itertools

import psycopg2
import psycopg2.extras
import sys
import requests
from bs4 import BeautifulSoup
import time
import datetime
import logging
from requests.exceptions import ConnectionError

import copy
import re
import pandas as pd
import os
from urllib3.exceptions import ReadTimeoutError, ConnectTimeoutError

def main():

    logger = logging.getLogger('CCASS Scheduler')
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('/var/log/test.log')
    ch = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    df_input = '%Y-%m-%d'
    df_webInput = '%y%m%d'
    df_cell = '%b%y'

    arg = {
        '-d': '',
        '-i': '3',
        '-ip': 'localhost'
    }


    for i in range(len(sys.argv)):
        if sys.argv[i] in arg:
            arg[sys.argv[i]] = sys.argv[i+1]

    connstion_string = "dbname='stock' user='postgres' host='" + arg['-ip'] + "' password='P@ssw0rDB'"

    date = datetime.datetime.now() if arg['-d'] == '' else datetime.datetime.strptime(arg['-d'], df_input)

    # checking data in database
    logger.info('Checking data')

    try:
        conn = psycopg2.connect(connstion_string)
    except:
        logger.error('Error: Unable to connect to the database')
        exit('Error: Unable to connect to the database')
    try:
        cur = conn.cursor()
        sql = " SELECT COUNT(1) FROM public.ccass WHERE date = '{0}' ".format(date.strftime(df_input))
        cur.execute(sql)
        result = cur.fetchone()
        conn.commit()
        conn.close()

    except:
        logger.error('Error: SQL error')

    if result[0] != 0:
        logger.info(date.strftime(df_input) + ' already exist')
        exit(date.strftime(df_input) + ' already exist')

    logger.info('Connecting to the website')

    stock_codes = get_all_stock_quotes_from_hkexnews('CCASS', date = date)

    session_data = get_session_data()

    #stock_codes_sample = dict(itertools.islice(stock_codes.items(), 3))

    result = pd.DataFrame()

    for stock_code in stock_codes:

        page_source = get_html(date, stock_code, copy.deepcopy(session_data))

        all_shareholding_df = parse_data(page_source, stock_code, date)

        if(all_shareholding_df.shape[0] > 0):
        	result = result.append(all_shareholding_df)

        logger.info("Finished parsing for code - %s" % (stock_code))

    # Change column name
    result.columns = ['participant_code', 'participant', 'number', 'code', 'date']

    result['percentage'] = result.groupby('code')['number'].apply(lambda x: round(x.astype(float)/x.sum(), 6))
    result['participant'] = ""

    logger.info("Writing to Database")

    try:
        connstion_string = "dbname='stock' user='postgres' host='" + arg['-ip'] + "' password='P@ssw0rDB'"
        conn = psycopg2.connect(connstion_string)

    except:
        logger.error('Error: Unable to connect to the database')
        exit('Error: Unable to connect to the database')
    try:
        if len(result) > 0:
            df_columns = list(result)

            columns = ",".join(df_columns)


            values = "VALUES ( {})".format(",".join(["%s" for _ in df_columns]))
            insert_stmt = "INSERT INTO {} ({}) {}".format("ccass", columns,values)
            logger.info(insert_stmt)

            cur = conn.cursor()
            psycopg2.extras.execute_batch(cur, insert_stmt, result.values)
            conn.commit()
            cur.close()
            logger.info("Done")

    except Exception as e:
        logger.error('Error: SQL error')
        logger.error(e)



def get_all_stock_quotes_from_hkexnews(purpose, date=datetime.date.today()):
    # Go to page in hkex for entire stock code list
    # logging.debug('Getting stock quotes from HKEXnews')
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

    #logging.info('..Getting session info.')
    response = get_or_post_data('get', url)
    soup = BeautifulSoup(response.content, 'html.parser')
    data = {}
    for tag in soup.find_all('input'):
        if tag['id'] == '__VIEWSTATE' or tag['id'] == '__VIEWSTATEGENERATOR' or tag['id'] == '__EVENTVALIDATION':
            data[tag['id']] = tag['value']
    return data

def get_or_post_data(method, url, data=None, headers=None):
    # For handling block IP issues
    count = 0
    sleep_duration = [5,10,60,120,300,600,1200,2400]
    while True:
        try:
            logging.debug('....Getting response from website.')
            if method == 'get':
                response = requests.get(url, timeout=10)
            elif method == 'post':
                response = requests.post(url, data=data, headers=headers, timeout=10)
            else:
                logging.error('Method NOT stated.')
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
    logging.debug('....Filling in other required info.')
    today = datetime.date.today()
    data['today'] = '{0:0>4}{1:0>2}{2:0>2}'.format(today.year, today.month, today.day)
    data['ddlShareholdingDay'] = '{0:0>2}'.format(date.day)
    data['ddlShareholdingMonth'] = '{0:0>2}'.format(date.month)
    data['ddlShareholdingYear'] = '{0:0>4}'.format(date.year)
    data['txtStockCode'] = stock_code
    data['sortBy'] = ''
    data['selPartID'] = ''
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
    logging.debug('....Parsing page source')
    soup = BeautifulSoup(page_source, 'html.parser')

    # Initialize parameters
    all_organized_rows = []
    HEADER_COLS = ['Participant ID', 'Name of CCASS Participant(* for Consenting Investor Participants )', 'Shareholding']

    if 'No match record found' not in page_source:
        # Get all rows relating to CCASS shareholding
        # Only if there are CCASS shareholding in the first place
        logging.debug('....Collecting CCASS shareholding.')
        ccass_participant_shareholding_table = soup.find('table', {'id': 'participantShareholdingList'})
        try:
            ccass_participant_shareholding_rows = ccass_participant_shareholding_table.find_all('tr')
        except:
            return None
        for row in ccass_participant_shareholding_rows:
            organized_row = [i.get_text().strip() for i in row.find_all('td')]

            # Ensure rows are not empty or the header row
            if not organized_row == ['']:
                row_to_add = organized_row[:2] + [organized_row[3]]
                if row_to_add != HEADER_COLS:
                    all_organized_rows.append(row_to_add)

    # Get all rows relating to (1) unnamed CCASS shareholding and (2) non-CCASS shareholding
    logging.debug('....Collecting other shareholding')
    holding_summary_table = soup.find('div', {'id': 'pnlResultSummary'})
    holding_summary_rows = holding_summary_table.find_all('tr')
    # Parse each row of the summary table
    for row in holding_summary_rows:
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
    logging.debug('....Organizing data to required format.')
    all_shareholding_df = pd.DataFrame(all_organized_rows, columns=HEADER_COLS)
    all_shareholding_df['Shareholding'] = all_shareholding_df['Shareholding'].apply(lambda x: int(str(x).replace(',', '')))
    all_shareholding_df['Stock Code'] = stock_code
    all_shareholding_df['Date'] = date

    return all_shareholding_df

if __name__ == "__main__":
    main()
