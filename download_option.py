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
    
    #date_obj = datetime.now().date() if arg['-d'] == '' else datetime.strptime(arg['-d'], df_input).date()
    date_obj = datetime.strptime('2019-04-18', '%Y-%m-%d').date()
    page_source = get_html(date_obj = date_obj)

    df_mapping  = parse_mapping(page = page_source, date_obj = date_obj)
    df_option   = parse_option(page = page_source, date_obj = date_obj)

    print(df_option)
    

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
    df = pd.DataFrame(mapping_list, columns = col_name)

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
                optionDate = datetime.strptime(cells[0], '%b%y').strftime("%Y-%m-%d")
                cells = [(c.replace('+','').replace(',',''),'NULL')[c.strip() == '-'] for c in cells]
                cells[0] = optionDate
                cells.insert(0, opt_id)     # Add option id to the list before append
                all_rows.append(cells)
    
    # Change list to dataframe
    col_name = ['option_name', 'option_date', 'strike', 'contract', 'open', 'high', 'low', 'settle', 'delta_settle', 'iv', 'volumn', 'oi', 'delta_oi']
    df = pd.DataFrame(all_rows, columns=col_name)

    return(df)

if __name__ == "__main__":
    main()