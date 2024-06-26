
import os
import pandas as pd
import argparse
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

parser = argparse.ArgumentParser(
    description='Choose the location you want to analyze')
parser.add_argument(
    '-c', '--city', help="['台北市','苗栗縣','花蓮縣','台中市','台中縣','台東縣','基隆市','南投縣','澎湖縣','台南市','彰化縣','陽明山','高雄市','雲林縣','金門縣','台北縣','嘉義縣','連江縣','宜蘭縣','台南縣','嘉義市','桃園縣','高雄縣','新竹市','新竹縣','屏東縣']", default='台北市')
parser.add_argument(
    '-f', '--yearsfrom', help='from year, example"110', type=int, default=111)
parser.add_argument(
    '-t', '--yearsto', help='to year, example:111', type=int, default=112)
args = parser.parse_args()
location = args.city
fromYear = args.yearsfrom
toYear = args.yearsto

location_str = """台北市 A 苗栗縣 K 花蓮縣 U
台中市 B 台中縣 L 台東縣 V
基隆市 C 南投縣 M 澎湖縣 X
台南市 D 彰化縣 N 陽明山 Y
高雄市 E 雲林縣 P 金門縣 W
新北市 F 嘉義縣 Q 連江縣 Z
宜蘭縣 G 台南縣 R 嘉義市 I
桃園縣 H 高雄縣 S 新竹市 O
新竹縣 J 屏東縣 T"""

# create a dictionary to convert location to letter
locToLetter = dict(
    zip(location_str.split()[::2], location_str.lower().split()[1::2]))

# for d in os.listdir('crawler/real_estate/') :
#     if int(d[:3]) >= fromYear and int(d[:3]) <= toYear:
#         print(d)


# 歷年資料夾
dirs = [d for d in os.listdir('real_estate/') if not d.startswith('.DS')
        if int(d[:3]) >= fromYear and int(d[:3]) <= toYear]
dfs = []
for d in dirs:
    df = pd.read_csv(os.path.join(
        'real_estate/'+d, locToLetter[location] + '_lvr_land_a.csv'), index_col=False)
    df['Q'] = d[-1]
    dfs.append(df.iloc[1:])

df = pd.concat(dfs, sort=True)

# 新增交易年份
df['year'] = pd.to_numeric(df['交易年月日'].str[:-4], errors='coerce') + 1911

# 平方公尺換成坪
df['單價元平方公尺'] = df['單價元平方公尺'].astype(float)
df['單價元坪'] = df['單價元平方公尺'] * 3.30579

# 建物型態
df['建物型態2'] = df['建物型態'].str.split('(').str[0]

# 刪除有備註之交易（多為親友交易、價格不正常之交易）
df = df[df['備註'].isnull()]

# 將index改成年月日
df.index = pd.to_datetime(df['year'].astype(
    str) + df['交易年月日'].str[-4:], errors='coerce')
df.sort_index(inplace=True)
df.head()
# df.to_csv(location+'.csv')

# @title 數據分析

plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.sans-serif'] = ['Arial Unicode Ms']

# 自定義字體變數
myfont = FontProperties()
myfont.set_size(15)

prices = {}
# 程式碼首先會迭代 DataFrame 中 '鄉鎮市區' 列中的每個獨特地區。
# 對於每個地區，它會應用一些條件（cond）來篩選 DataFrame (df)。
# 這些條件篩選出該地區內用途為住宅物件（'主要用途' 是 '住家用'）且價格位於 5 到 95 百分位數之間的資料。
# 接著，它將篩選後的 DataFrame 按 'year' 列進行分組，並計算自 2012 年以來每年每平方米的平均價格。
# 最後，它將結果存儲在一個名為 prices 的字典中，以地區名稱作為鍵，而各年份的每平方米平均價格作為值。
for district in set(df['鄉鎮市區']):
    cond = (
        (df['主要用途'] == '住家用')
        & (df['鄉鎮市區'] == district)
        & (df['單價元坪'] < df["單價元坪"].quantile(0.95))
        & (df['單價元坪'] > df["單價元坪"].quantile(0.05))
    )
    groups = df[cond]['year']
    prices[district] = df[cond]['單價元坪'].astype(
        float).groupby(groups).mean().loc[2012:]

price_history = pd.DataFrame(prices)
price_history.to_csv(location+'price_history.csv')
price_history.plot()

plt.title('各區平均單價', fontproperties=myfont)
plt.legend(prop=myfont)
plt.show()
