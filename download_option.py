import requests
import pandas as pd
import numpy as np
import re
import psycopg2
import psycopg2.extras
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.logger import setup_logger
import sys

__all__ = 'Option'
logger = setup_logger(__all__)

def main():

    ###################################
    ### Parse input arguments        ##
    ###################################

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

    date_obj = datetime.now().date() if arg['-d'] == '' else datetime.strptime(arg['-d'], df_input).date()

    ###################################
    ### Database checking            ##
    ###################################

    check_db_records(date_obj)

    ###################################
    ### Grep and parse data          ##
    ###################################

    # Get from url
    page_source = get_html(date_obj = date_obj)

    # Parse page
    df_mapping  = parse_mapping(page = page_source, date_obj = date_obj)
    df_option   = parse_option(page = page_source, date_obj = date_obj)

    ###################################
    ### Processing data              ##
    ###################################

    # Merge mapping table
    df_merge     = df_option.merge(df_mapping, on = "option_name", how = "left")
    max_date_obj = get_max_date(date_obj = date_obj, extra_month = 2)

    # filter by max_date
    df_filter = df_merge[(df_merge.option_date <= np.datetime64(max_date_obj))]  # Filter out rows that is n extra months away
    df_filter = df_filter.assign(option_desc = "")

    # Change dtype to numeric and add date column
    numeric_cols = ['strike', 'open', 'high', 'low', 'settle', 'delta_settle', 'iv', 'volume', 'oi', 'delta_oi', 'code']
    df_filter[numeric_cols] = df_filter[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df_filter['date'] = date_obj

    ###################################
    ### Insert to database           ##
    ###################################

    insert_to_db(df_filter)

    return None


def get_html(date_obj):

    """ Get reponse from url """

    try:
        date_str = date_obj.strftime('%y%m%d')

        url = 'http://www.hkex.com.hk/eng/stat/dmstat/dayrpt/dqe' + date_str + '.htm'
        response = requests.get(url)
        if response.content.decode('utf-8').find('The page requested may have been relocated') != -1:
            logger.warning('Market closed')
            sys.exit(0)
        page = response.content.decode('utf-8').replace('\r\n','\n')
        logger.info("=============================================")
        logger.info('Getting data for date - {}'.format(date_obj))

    except:
        logger.error('The website cannot be reached')
        sys.exit(0)

    return(page)

def parse_mapping(page, date_obj):

    """
    Parse mapping table to match option code to underlying stock

    Args:
        page (str): Reponse get from the url
        date_obj (Datetime): Python date object for the option to be parsed

    Returns:
        df (Dataframe): Mapping table for option code to stock code

    Example:
        input_date_obj = datetime.strptime("2019-04-18", "%Y-%m-%d").date()
        page           = get_html(input_date_obj)
        df_mapping     = parse_mapping(page, input_date_obj)

    Data preview:
          option_name   code    option_desc
             A50        2823  X ISHARES A50
             AAC        2018       AAC TECH
             ACC        0914    ANHUI CONCH
             AIA        1299            AIA
             AIR        0753      AIR CHINA
    """

    summary = page.split('<A NAME="SUMMARY">')[1]
    mapping_list = []

    startToCapture = False
    for line in summary.split('<A NAME="')[0].split('\n'):
        option_name = line[:3]
        if startToCapture and line.strip() != '':

            try:
                option_desc = line[4:28].strip()
                stock_code  = line[30:34].strip().replace('NIL','NULL')

            except:
                option_desc = line[4:28].strip()
                stock_code  = 'NULL'

            row = [option_name, stock_code, option_desc]
            mapping_list.append(row)

        startToCapture = line.strip() != '' and (line[:4] == 'CODE' or startToCapture)

    # Change list to dataframe
    col_name = ['option_name', 'code', 'option_desc']
    df       = pd.DataFrame(mapping_list, columns = col_name)

    return(df)

def parse_option(page, date_obj):

    """
    Parse option data

    Args:
        page (str): Reponse get from the url
        date_obj (Datetime): Python date object for the option to be parsed

    Returns:
        df (Dataframe): Option data

    Example:
        input_date_obj = datetime.strptime("2019-04-18", "%Y-%m-%d").date()
        page           = get_html(input_date_obj)
        df_obtion      = parse_option(page, input_date_obj)

    Data preview:
        option_name option_date  strike contract  open  high   low  settle  delta_settle  iv  volumn    oi  delta_oi  code option_desc
                A50  2019-04-30    7.50        C  0.00  0.00  0.00    8.06         -0.12   0       0     0       0.0  2823
                A50  2019-04-30    7.75        C  0.00  0.00  0.00    7.81         -0.12   0       0     0       0.0  2823
                A50  2019-04-30    8.00        C  0.00  0.00  0.00    7.56         -0.12   0       0     0       0.0  2823
                A50  2019-04-30    8.25        C  0.00  0.00  0.00    7.31         -0.12   0       0     0       0.0  2823
    """

    summary     = page.split('<A NAME="SUMMARY">')[1]
    options     = summary.split('<A NAME="')[1:]
    all_rows    = []

    for opt in options:

        opt_id = opt[:3]          # Option code, e.g. A50
        rows = opt.split('\n')    # Each data row

        for row in rows:
            while row.find('  ') != -1:
                row = row.replace('  ',' ')
            cells = row.split(' ')

            # Parsing row (data) to different columns
            if len(cells) == 12 and not cells[0] in ['','CLASS']:

                option_date = datetime.strptime(cells[0], '%b%y')
                option_date = get_max_date(date_obj = option_date, extra_month = 0)   # Get end date of the month for option expiration date

                cells = [(c.replace('+','').replace(',',''),'NULL')[c.strip() == '-'] for c in cells]
                cells[0] = option_date
                cells.insert(0, opt_id)     # Add option id to the list before append
                all_rows.append(cells)

    # Change list to dataframe
    col_name = ['option_name', 'option_date', 'strike', 'contract', 'open', 'high', 'low', 'settle', 'delta_settle', 'iv', 'volume', 'oi', 'delta_oi']
    df       = pd.DataFrame(all_rows, columns=col_name)

    logger.info('Parsing data for date - {}'.format(date_obj))

    return(df)

def get_max_date(date_obj, extra_month):

    """
    Get date of the input with extra month

    Args:
        date_obj (DateTime): Date time object
        extra_month (int): extra number of month to be considered.

    Returns:
        max_date_obj: Date time object with the extra month

    Example:
        date_obj = datetime.strptime('2019-04-18', '%Y-%m-%d').date()
        max_date_obj(date_obj = date_obj, extra_month = 2)
    """

    max_date_obj = date_obj + relativedelta(months = extra_month) + relativedelta(day=31) # if date = 2019-04-12, extra = 2, return 2019-06-30
    return(max_date_obj)

def insert_to_db(df):

    """ insert data to database """

    connection_string = "dbname='stock' user='db_user' host='" + 'localhost' + "' port = 4004 password='P@ssw0rDB'"
    df_columns = df.columns.values.tolist()

    # create (col1,col2,...)
    columns = ",".join(df_columns)

    # create VALUES('%s', '%s",...) one '%s' per column
    values = "VALUES({})".format(",".join(["%s" for _ in df_columns]))

    #create INSERT INTO table (columns) VALUES('%s',...)
    insert_stmt = "INSERT INTO {} ({}) {}".format('option', columns, values)
    try:
        conn = psycopg2.connect(connection_string)

        cur = conn.cursor()
        psycopg2.extras.execute_batch(cur, insert_stmt, df.values)
        conn.commit()
        conn.close()

        logger.info("=============================================")
        logger.info("No of records - {}".format(df.shape[0]))
        logger.info("Finished insert into Option")

        logger.info("=============================================")
        logger.info("STATUS - SUCCESS")

    except Exception as e:
        print(e)
        logger.warning("No database available")

def check_db_records(date):
    """
    Check if there is records in the database, exit program if there is

    Args:
        date (DateTime): Date time object

    Returns:
        None
    """

    connection_string = "dbname='stock' user='db_user' host='" + 'localhost' + "' port = 4004 password='P@ssw0rDB'"
    count_stmt = "SELECT COUNT(1) FROM option WHERE date = '{}'".format(date)

    try:
        conn = psycopg2.connect(connection_string)
        cur = conn.cursor()
        cur.execute(count_stmt)
        result = cur.fetchall()
        conn.close()

        logger.info('Checking Option records in Database for date - {}'.format(date))
    except:
        logger.warning("Something wrong with date checking in database. Probably no database being setup")
        result = np.nan

    if np.isnan(result):
        pass
    elif result[0][0] != 0:           # Return the first element (count) in the tuple
        logger.warning('Option records exist in database for date - {}'.format(date))
        sys.exit()
    else:
        logger.info('Finished checking. Processing')

    return None

if __name__ == "__main__":
    main()
