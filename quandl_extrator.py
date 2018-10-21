import requests
import json
import pandas as pd

# for i in range(1,3000):
#     print("=======================================")
#     code = str(i).zfill(5)
#     url = 'https://www.quandl.com/api/v3/datasets/HKEX/{}?limit=10'.format(code)
#     print(url)
#     r = requests.get(url)
#     print(r.content)
#     print("=======================================")

date = '2018-10-19'
code = str(1).zfill(5)
url = 'https://www.quandl.com/api/v3/datasets/HKEX/{}?limit=10'.format(code)

r = requests.get(url)
content = r.content.decode("utf-8")
data_json = json.loads(content)
data_list = data_json['dataset']['data']

df = pd.DataFrame(data_list)
df.columns = ['date', 'close','net_change', 'change', 'bid', 'ask', 'pe', 'high', 'low', 'open', 'volume', 'turnover','lot_size']
df['code'] = code
df_selected = df.loc[df['date']== date]
print(df_selected)