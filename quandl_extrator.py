import requests

# for i in range(1,3000):
#     print("=======================================")
#     code = str(i).zfill(5)
#     url = 'https://www.quandl.com/api/v3/datasets/HKEX/{}?limit=10'.format(code)
#     print(url)
#     r = requests.get(url)
#     print(r.content)
#     print("=======================================")


code = str(1).zfill(5)
url = 'https://www.quandl.com/api/v3/datasets/HKEX/{}?limit=10'.format(code)

r = requests.get(url)

