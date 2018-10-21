import requests
import json
import pandas as pd
import quandl
import re

result = pd.DataFrame()

quandl.ApiConfig.api_key = "nNXFy-SJNtuz6mvifMe3"
real_col = ""

# for i in range(1, 100):
for i in range(1, 500):
    
    code        = str(i).zfill(5)
    code_str    = "HKEX/{}".format(code)
    
    print("=======================================") 
    print("Start getting - {}".format(code))
    try:
        data = quandl.get(code_str, rows=1)
        data['code'] = code
        
        col_name = data.columns.tolist()
        clean_col_name = [re.sub('\W+','', x) for x in col_name]
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