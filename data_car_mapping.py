

import pandas as pd
import numpy as np
import mysql.connector
import pymysql


# 엔카
db_infos = pymysql.connect(
    user='daa_car_market',
    passwd='autoplusdaa!@',
    host='139.150.73.218',
    db='CAR_MARKET_DB',
    charset='utf8'
)

qurey = ''' 
            SELECT
                tcplm.KIND,
                tcplm.MAKER,
                tcplm.MODEL,
                tcplm.MODEL_DETAIL,
                tcplm.GRADE,
                tcplm.GRADE_DETAIL,
                tcplm.YEARS,
                tcplm.FUEL,
                tcplm.KM,
                tcplm.KIND,
                tcplm.MISSION,
                tcplm.COLOR,
                tcplm.PRICE,
                tcplm.NEW_PRICE,
                tcplm.OPTIONS_PRICE,
                tcplm.FRAME_REPAIR,
                tcplm.PLATES_NUMBER,
                tcplm.ADD_DATE,
                tcplm.FIRST_DATE,
                tcplm.AP_MODEL_ID,
                ANMM.GRADENO
            FROM 
                TBL_CAR_PRODUCT_LIST_1MONTH tcplm
                LEFT JOIN atb_ncar_model_ml ANMM
                    ON tcplm.AP_MODEL_ID = ANMM.AP_MODEL_ID 
				
'''

cursor = db_infos.cursor(pymysql.cursors.DictCursor)
cursor.execute(qurey)
mss = cursor.fetchall()


data_list = []
for idx, row in enumerate(mss):
    kind = row['KIND']
    maker = row['MAKER']
    model = row['MODEL']
    model_detail = row['MODEL_DETAIL']
    grade = row['GRADE']
    years = row['YEARS']
    fuel = row['FUEL']
    plates_number = row['PLATES_NUMBER']
    row_data = [kind, maker, model, model_detail, grade, years, fuel, plates_number]
    data_list.append(row_data)
mss = pd.DataFrame(data=data_list, columns = ['차종', '제조사', '모델명', '상세모델명', '등급명', '연식', '연료', '차량번호'])

print("-----1month 테이블-----")
print(len(mss))

# 해당 차대번호 가져오기
db_infos2 = pymysql.connect(
    user='AP_MSS',
    passwd='ap20190324$!',
    host='117.52.74.158',
    db='AP_MSS',
    charset='utf8'
)

qurey2 = ''' SELECT
                PLATES_NUMBER,
                VIN_NUMBER
            FROM TBL_CAR_PRODUCT_LIST
'''

cursor2 = db_infos2.cursor(pymysql.cursors.DictCursor)
cursor2.execute(qurey2)
mss2 = cursor2.fetchall()

data_list = []
for idx, row in enumerate(mss2):
    plates_number = row['PLATES_NUMBER']
    vin_number = row['VIN_NUMBER']
    row_data = [plates_number, vin_number]
    data_list.append(row_data)
mss2 = pd.DataFrame(data=data_list, columns = ['차량번호', '차대번호'])

print("-----차대번호 테이블-----")
print(len(mss2))

# mss2에서 차량번호 중복 제거 (첫 번째만 남김)
mss2_unique = mss2.drop_duplicates(subset=['차량번호'], keep='first')

# 차량번호 기준으로 LEFT JOIN
mss = pd.merge(
    mss,
    mss2_unique[['차량번호', '차대번호']],
    how='left',
    on='차량번호'   # 두 테이블 모두 같은 컬럼명일 때
)

print("-------매칭중-------")
print(len(mss))
print("--------매칭된개수-------")
print(len(mss['차대번호'].isnull()))


df = pd.read_excel('C:/Users/24100801/Desktop/25년 7월 신규_이전 데이터.xlsx', sheet_name = '이전_A10_TRANSR_REGIST')
print(len(df))


# 전처리
df['차대번호']  = df['차대번호'].astype(str).str.strip()
mss['차대번호'] = mss['차대번호'].astype(str).str.strip()

df = df.dropna(subset=['차대번호'])
mss = mss.dropna(subset=['차대번호'])

# mss: 앞 11자리 기준 최빈 (제조사, 모델명) 구하기
mss['차대번호11'] = mss['차대번호'].str[:11]
counts = (
    mss.groupby(['차대번호11', '차종', '제조사', '모델명'])
       .size()
       .reset_index(name='count')
)
top_groups = (
    counts.sort_values(['차대번호11', 'count', '차종', '제조사', '모델명'],
                       ascending=[True, False, True, True, True])
          .drop_duplicates(subset=['차대번호11'])
          [['차대번호11', '차종', '제조사', '모델명']]
)

# 1차: 11자리 병합
df['차대번호11'] = df['차대번호'].str[:11]
df = df.merge(top_groups, on='차대번호11', how='left')
df = df.drop(columns=['차대번호11'])

# 반복: 10~6자리까지 점진적으로 채우기
for n in range(10, 5, -1):  # 10,9,8,7,6
    unmatched = df['제조사'].isna()
    if unmatched.any():
        key_col = f'차대번호{n}'
        # mss에서 n자리 키 생성
        mss[key_col] = mss['차대번호'].str[:n]
        # n자리 기준 top 그룹 계산
        counts_n = (
            mss.groupby([key_col, '차종', '제조사', '모델명'])
               .size()
               .reset_index(name='count')
        )
        top_groups_n = (
            counts_n.sort_values([key_col, 'count', '차종', '제조사', '모델명'],
                                 ascending=[True, False, True, True, True])
                     .drop_duplicates(subset=[key_col])
                     [[key_col, '차종', '제조사', '모델명']]
        )
        # 해당 n자리만 다시 병합 (NaN인 행만)
        df.loc[unmatched, key_col] = df.loc[unmatched, '차대번호'].str[:n]
        df = df.merge(top_groups_n, how='left', left_on=key_col, right_on=key_col, suffixes=('', f'_{n}'))

        # 새로 매칭된 값 채워넣기
        for col in ['차종', '제조사', '모델명']:
            df[col] = df[col].fillna(df[f'{col}_{n}'])
            df = df.drop(columns=[f'{col}_{n}'])

        # 임시 key 삭제
        df = df.drop(columns=[key_col])

# 0) 차명 정리(공백 방어). 원본을 건드리지 않으려면 임시 컬럼 사용
df['차명_norm'] = df['차명'].astype(str).str.strip()

# 1) 참조 테이블: 차명별로 이미 확정된 (제조사, 모델명)의 '최빈' 조합 구하기
ref = df[df['차명_norm'].ne('') & df['차종'].notna() & df['제조사'].notna() & df['모델명'].notna()].copy()

if not ref.empty:
    ref_counts = (
        ref.groupby(['차명_norm', '차종', '제조사', '모델명'])
           .size()
           .reset_index(name='count')
    )
    # 동률 시에도 결정 규칙을 고정(사전순)해서 재현성 확보
    ref_top = (
        ref_counts.sort_values(['차명_norm', 'count', '차종', '제조사', '모델명'],
                               ascending=[True, False, True, True, True])
                 .drop_duplicates(subset=['차명_norm'], keep='first')
                 [['차명_norm', '차종', '제조사', '모델명']]
                 .rename(columns={'차종':'차종_ref', '제조사':'제조사_ref', '모델명':'모델명_ref'})
    )

    # 2) 아직 미채움 + 차명 있는 행에만 매핑 머지
    mask_need = df['제조사'].isna() & df['차명_norm'].ne('')
    if mask_need.any():
        df = df.merge(ref_top, how='left', left_on='차명_norm', right_on='차명_norm')

        # 3) 못 채운 곳을 ref로 보간
        df['차종'] = df['차종'].fillna(df['차종_ref'])
        df['제조사'] = df['제조사'].fillna(df['제조사_ref'])
        df['모델명'] = df['모델명'].fillna(df['모델명_ref'])

        # 4) 임시 컬럼 정리
        df = df.drop(columns=['차종_ref', '제조사_ref', '모델명_ref'])

# 공통 임시 컬럼 정리
df = df.drop(columns=['차명_norm'])

print(df[['차대번호', '차종', '제조사', '모델명']])

df.to_excel('C:/Users/24100801/Desktop/차대번호매핑.xlsx', index = False)