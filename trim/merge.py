import os
import re
import pandas as pd
import geohash
import time
from geopy.distance import geodesic
import argparse


parser = argparse.ArgumentParser(
    description='Choose the location you want to analyze')
parser.add_argument(
    '-c', '--city', help="['臺北市','苗栗縣','花蓮縣','臺中市','臺中縣','臺東縣','基隆市','南投縣','澎湖縣','臺南市','彰化縣','陽明山','高雄市','雲林縣','金門縣','臺北縣','嘉義縣','連江縣','宜蘭縣','臺南縣','嘉義市','桃園縣','高雄縣','新竹市','新竹縣','屏東縣']", default='臺北市')
parser.add_argument(
    '-y', '--year', help='from year, example"110', type=int, default=112)
args = parser.parse_args()
location = args.city
year = args.year

start = time.time()

print("The time used to execute this is given below")


# 設定基準路徑為專案的根目錄
basePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 結合基準路徑和相對路徑來獲取絕對路徑


def get_absolute_path(relative_path):
    return os.path.abspath(os.path.join(basePath, relative_path))


def extract_ri(address):
    if pd.isna(address):
        return None
    try:
        match = re.search(r'(.+里)', address)
    except re.error as e:
        print(e)
    if match:
        return match.group(1)
    else:
        return None


# 讀取 MRT CSV 文件
mrt_df = pd.read_csv(get_absolute_path('init-data/geohash-northern-mrt.csv'))


def findCloseMRT(row, mrt_df):

    # 如果有換過可能會有多筆，用;隔開，只抓最後一筆
    filterRowLat = str(row['lat']).split(';')[-1]
    filterRowLon = str(row['lon']).split(';')[-1]

    if (filterRowLat == 'nan' or filterRowLon == 'nan'):
        return 'no location'

    # 將經緯度轉換為 geohash
    curGeoHash = geohash.encode(float(filterRowLat), float(filterRowLon))
    curLocation = (filterRowLat, filterRowLon)
    mrt_list = []
    for index, mrtRow in mrt_df.iterrows():
        precision6 = mrtRow['geohash'][0:6]  # W:1.2km , H:609.4m
        precision5 = mrtRow['geohash'][0:5]  # W:4.9km , H:4.9km
        mrtLocation = (mrtRow['lat'], mrtRow['lon'])
        if curGeoHash[0:6] == precision6:
            distanceBtMRTStationM = int(
                geodesic(curLocation, mrtLocation).meters)
            formatData = {'station_name_tw': mrtRow['station_name_tw'],
                          'line_name': mrtRow['line_name'],
                          'distance_meter': distanceBtMRTStationM}
            mrt_list.append(formatData)
        elif curGeoHash[0:5] == precision5:
            distanceBtMRTStationM = int(
                geodesic(curLocation, mrtLocation).meters)
            # 如果距離小於1.5km才加入list裡
            if distanceBtMRTStationM <= 1500:
                formatData = {'station_name_tw': mrtRow['station_name_tw'],
                              'line_name': mrtRow['line_name'],
                              'distance_meter': int(distanceBtMRTStationM)}
                mrt_list.append(formatData)

    return mrt_list
# def findCloseMRT(row, mrt_df):
#     # 如果有換過可能會有多筆，用;隔開，只抓最後一筆
#     filterRowLat = str(row['lat']).split(';')[-1]
#     filterRowLon = str(row['lon']).split(';')[-1]

#     if filterRowLat == 'nan' or filterRowLon == 'nan':
#         return 'no location'

#     # 將經緯度轉換為 geohash
#     curGeoHash = geohash.encode(float(filterRowLat), float(filterRowLon))
#     curLocation = (float(filterRowLat), float(filterRowLon))
#     mrt_list = []
#     # 提前過濾出所有可能的 geohash 範圍
#     precision6_matches = mrt_df[mrt_df['geohash'].str.startswith(
#         curGeoHash[:6])]
#     precision5_matches = mrt_df[mrt_df['geohash'].str.startswith(
#         curGeoHash[:5])]

#     # 處理精度為 6 的 geohash # W:1.2km , H:609.4m
#     for _, mrtRow in precision6_matches.iterrows():
#         mrtLocation = (mrtRow['lat'], mrtRow['lon'])
#         distanceBtMRTStationM = geodesic(curLocation, mrtLocation).meters
#         formatData = {'station_name_tw': mrtRow['station_name_tw'],
#                       'line_name': mrtRow['line_name'],
#                       'distance_meter': distanceBtMRTStationM}
#         mrt_list.append(formatData)

#     # 處理精度為 5 的 geohash # W:4.9km , H:4.9km
#     for _, mrtRow in precision5_matches.iterrows():
#         mrtLocation = (mrtRow['lat'], mrtRow['lon'])
#         distanceBtMRTStationM = geodesic(curLocation, mrtLocation).meters
#         if distanceBtMRTStationM <= 1500:
#             formatData = {'station_name_tw': mrtRow['station_name_tw'],
#                           'line_name': mrtRow['line_name'],
#                           'distance_meter': int(distanceBtMRTStationM)}
#             mrt_list.append(formatData)

#     return mrt_list


initSourcePath = get_absolute_path('init-data')
addressPath = f'/{location}{str(year)}_Address_Finish.csv'
address_df = pd.read_csv(initSourcePath+addressPath)
address_df['里'] = address_df['Response_Address'].apply(extract_ri)

organizePath= f'/{location}-{year}-{year}-organize.csv'
organize_df = pd.read_csv(basePath+organizePath)
merged_df = pd.concat([organize_df, address_df['里'],
                      address_df['Response_X'], address_df['Response_Y']], axis=1)
# longitude 經度 latitude 緯度
merged_df.rename(columns={'Response_X': 'lon',
                 'Response_Y': 'lat'}, inplace=True)


# merged_df['MRTS'] = merged_df.apply(findCloseMRT, axis=1)
# 使用 apply 方法並傳遞 mrt_df
merged_df['MRTS'] = merged_df.apply(findCloseMRT, axis=1, mrt_df=mrt_df)


merged_df.to_csv(basePath+f'/{location}-{year}-{year}-merged.csv')
end = time.time()

print(end - start)
