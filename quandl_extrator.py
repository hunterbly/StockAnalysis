import requests
import json
import pandas as pd
import quandl
import re

# Defind empty dataframe for output
result = pd.DataFrame()

quandl.ApiConfig.api_key = "nNXFy-SJNtuz6mvifMe3"
real_col = ""

# Define list of sequence for stock
stockListOption = [1,2,3,4,5,6,11,12,16,17,19,23,27,66,135,151,175,267,293,330,358,386,388,390,489,494,688,700,728,762,823,857,883,902,914,939,941,992,998,1044,1088,1109,1113,1171,1186,1211,1288,1299,1336,1339,1359,1398,1800,1816,1880,1898,1919,1928,1988,2018,2038,2282,2318,2319,2328,2333,2388,2600,2601,2628,2777,2800,2822,2823,2827,2828,2888,2899,3323,3328,3800,3888,3968,3988,6030]
stockListAll = list(range(1,4000)) + list(range(4601,4609)) + list(range(6030,6031)) + list(range(6099,6900))
stockListNotOption = [x for x in stockListAll if x not in stockListOption] 
seqList = [stockListOption, stockListNotOption]

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

# data.columns = ['date', 'ask','bid', 'change', 'high', 'lot_size', 'low', 'net_change', 'close', 'pe', 'open', 'volume', 'turnover', 'code']
# result.columns = real_col
print(result)

# for i in range(1,3000):
#     print("=======================================")
#     code = str(i).zfill(5)
#     url = 'https://www.quandl.com/api/v3/datasets/HKEX/{}?limit=10'.format(code)
#     print(url)
#     r = requests.get(url)
#     print(r.content)
#     print("=======================================")

# result_list = []

# for i in range(1,5):
#     date = '2018-10-19'
#     # code = str(1).zfill(5)
#     code = str(i).zfill(5)
#     url = 'https://www.quandl.com/api/v3/datasets/HKEX/{}?limit=10'.format(code)

#     r = requests.get(url)
#     content = r.content.decode("utf-8")
#     print(content)
#     data_json = json.loads(content)
#     data_list = data_json['dataset']['data']

#     # df = pd.DataFrame(data_list)
#     # df.columns = ['date', 'close','net_change', 'change', 'bid', 'ask', 'pe', 'high', 'low', 'open', 'volume', 'turnover','lot_size']
#     # df['code'] = code
#     # df_selected = df.loc[df['date']== date]
#     # print(df_selected)
#     # result.append(df_selected)

#     for record in data_list:
#         if record[0] == date:
#             #row = record.append(code)
#             row = record
#             print(row)
#         else:
#             pass

#     result_list.append(row)    

# print(result_list)