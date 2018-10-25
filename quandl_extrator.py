import requests
import pandas as pd
import quandl
import re
import psycopg2
from datetime import datetime
import logging
import sys

logger = logging.getLogger('HKEX Scheduler')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/cronjob.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh.setFormatter(formatter)
logger.addHandler(fh)


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

# date = datetime.now().strftime(df_input) if arg['-d'] == '' else datetime.strptime(arg['-d'], df_input)
date = datetime.strptime('2018-10-24', df_input)

print('Checking data...')
try:
    conn = psycopg2.connect(connstion_string)
except:
    exit('Error: Unable to connect to the database')
try:
    cur = conn.cursor()
    sql = ' SELECT COUNT(1) FROM public.stock WHERE date = %s '
    data=[date]
    cur.execute(sql,data)
    result = cur.fetchone()
    conn.commit()
    conn.close()
except:
    print('Error: SQL error')

if result[0] != 0:
    exit(date.strftime(df_input) + ' exists')

# Defind empty dataframe for output
result = pd.DataFrame()

quandl.ApiConfig.api_key = "nNXFy-SJNtuz6mvifMe3"
real_col = ""

# Define list of sequence for stock
# stockListOption = [1,2,3,4,5,6,11,12,16,17,19,23,27,66,135,151,175,267,293,330,358,386,388,390,489,494,688,700,728,762,823,857,883,902,914,939,941,992,998,1044,1088,1109,1113,1171,1186,1211,1288,1299,1336,1339,1359,1398,1800,1816,1880,1898,1919,1928,1988,2018,2038,2282,2318,2319,2328,2333,2388,2600,2601,2628,2777,2800,2822,2823,2827,2828,2888,2899,3323,3328,3800,3888,3968,3988,6030]
# stockListAll = list(range(1,4000)) + list(range(4601,4609)) + list(range(6030,6031)) + list(range(6099,6900))
# stockListNotOption = [x for x in stockListAll if x not in stockListOption] 
# seqList = [stockListOption, stockListNotOption]
stockListOption = range(1, 5)
seqList = [stockListOption]

for stockList in seqList:
    for num in stockList:
        
        code        = str(num).zfill(5)
        code_str    = "HKEX/{}".format(code)
        
        print("=======================================") 
        print("Start getting - {}".format(code))
        try:
            data = quandl.get(code_str, rows=1)
            data['code'] = code
            
            col_name = data.columns.tolist()
            clean_col_name = [re.sub(r'\W+','', x) for x in col_name]
            col_dict = dict(zip(col_name, clean_col_name))

            data.rename(columns=col_dict, inplace=True)

            result = pd.concat([result, data], sort=True)
            print(result.tail())
        except:
            print("No record")
            pass

result = result.reset_index()

old_col = result.columns.values.tolist()
new_col = ['date', 'ask', 'bid', 'change', 'high', 'lot_size', 'low', 'net_change', 'close', 'pe', 'open', 'volume', 'turnover', 'code']
rename_col_dict = dict(zip(old_col, new_col))
result = result.rename(columns = rename_col_dict)

result = result[['date', 'ask', 'bid', 'open', 'high', 'low', 'close', 'volume', 'turnover', 'code']]

result['volume'] = result['volume'] * 1000
result['turnover'] = result['turnover'] * 1000

result = result.dropna()
result = result.loc[result.date == date]

print(result)

