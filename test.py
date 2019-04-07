import psycopg2
import requests
import sys
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta



df_input = '%Y-%m-%d'
df_webInput = '%y%m%d'
df_cell = '%b%y'

date = datetime.now()

try:
    #url = 'https://www.hkex.com.hk/eng/stat/dmstat/dayrpt/dqe' + date.strftime(df_webInput) + '.htm'
    url = 'http://www.hkex.com.hk/eng/stat/dmstat/dayrpt/dqe' + date.strftime(df_webInput) + '.htm'
    response = requests.get(url)
    if response.content.decode('utf-8').find('The page requested may have been relocated') != -1:
        logger.info('Market closed.')
        exit('Market closed.')
    data = response.content.decode('utf-8').replace('\r\n','\n')
except:
    logger.error('The website cannot be reached')
    exit('Error: The website cannot be reached')
#with open("from.html", "r") as file:
#    data = file.read()

logger.info('Parsing data...')
summary = data.split('<A NAME="SUMMARY">')[1]
optionMapping = {}

startToCapture = False
for line in summary.split('<A NAME="')[0].split('\n'):
    if startToCapture and line.strip() != '':
        try:
            optionMapping[line[:3]] = {
                'desc':line[4:28].strip(),
                'code':"'" + line[30:34].strip().replace('NIL','NULL') + "'"
            }
        except:
            optionMapping[line[:3]] = {
                'desc':line[4:28].strip(),
                'code':'NULL'
            }
    startToCapture = line.strip() != '' and (line[:4] == 'CODE' or startToCapture)

items = summary.split('<A NAME="')[1:]
obj = {}


for item in items:
    item_id = item[:3]
    obj[item_id] = []
    rows = item.split('\n')
    for row in rows:
        while row.find('  ') != -1:
            row = row.replace('  ',' ')
        cells = row.split(' ')
        if len(cells) == 12 and not cells[0] in ['','CLASS']:
            addedIntervalDate = (date + relativedelta(months=int(arg['-i']) - 1)).replace(day=1)
            optionDate = datetime.strptime(cells[0],df_cell)
            if addedIntervalDate >= optionDate:
                cells = [(c.replace('+','').replace(',',''),'NULL')[c.strip() == '-'] for c in cells]
                cells[0] = optionDate

                obj[item_id].append(cells)

logger.info('Connecting to DB...')
try:
    conn = psycopg2.connect(connstion_string)
except:
    logger.error('Unable to connect to the database')
    exit('Error: Unable to connect to the database')
try:
    cur = conn.cursor()
    for option in obj:
        sqlVal = []
        if len(obj[option]) != 0:
            for record in obj[option]:
                sqlVal.append("(DEFAULT,'" + date.strftime(df_input) + "'," + str(optionMapping[option]['code']) + ",'" + option + "','" + optionMapping[option]['desc'].replace("'","''") + "','" + record[0].strftime(df_input) + "'," + record[1]+",'"+record[2]+"',"+record[3]+","+record[4]+","+record[5]+","+record[6]+","+record[7]+","+record[8]+","+record[9]+","+record[10]+","+record[11]+")")
            sql = ' INSERT INTO public.option(id, date, code, option_name, option_desc, option_date, strike, contract, open, high, low, settle, delta_settle, iv, volume, oi, delta_oi) VALUES '
            sql += ','.join(sqlVal)
            cur.execute(sql)
    conn.commit()
    conn.close()

except:
    logger.error('SQL error')
    with open('data.html', 'a') as the_file:
        the_file.write(data)
    with open('error.sql', 'a') as the_file:
        the_file.write(sql)
logger.info('Done')
