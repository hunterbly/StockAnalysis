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
    ######
    # Parse program arguments
    ######

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
    
    # Get from url
    page_source = get_html(date_obj = date_obj)

    # Parse page
    df_mapping  = parse_mapping(page = page_source, date_obj = date_obj)
    df_option   = parse_option(page = page_source, date_obj = date_obj)

    # Merge mapping table
    df_merge     = df_option.merge(df_mapping, on = "option_name", how = "left")
    max_date_obj = get_max_date(date_obj = date_obj, extra_month = 2)

    # filter by max_date
    df_filter = df_merge[(df_merge.option_date <= np.datetime64(max_date_obj))]  # Filter out rows that is n extra months away
    df_filter = df_filter.assign(option_desc = "")

    # Change dtype to numeric
    numeric_cols = ['strike', 'open', 'high', 'low', 'settle', 'delta_settle', 'iv', 'volume', 'oi', 'delta_oi', 'code']
    df_filter[numeric_cols] = df_filter[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # Write to db
    insert_to_db(df_filter)


def get_html(date_obj):
    try:
        date_str = date_obj.strftime('%y%m%d')

        url = 'http://www.hkex.com.hk/eng/stat/dmstat/dayrpt/dqe' + date_str + '.htm'
        response = requests.get(url)
        if response.content.decode('utf-8').find('The page requested may have been relocated') != -1:
            logger.info('Market closed.')
            sys.exit(0)
        page = response.content.decode('utf-8').replace('\r\n','\n')
    except:
        logger.error('The website cannot be reached')
        sys.exit(0)

    return(page)

def parse_mapping(page, date_obj):
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

    connection_string = "dbname='stock' user='db_user' host='" + 'localhost' + "' password='P@ssw0rDB'"
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
        logger.info("Finished insert into CCASS")

    except Exception as e:
        print(e)
        logger.warning("No database available")

if __name__ == "__main__":
    main()
