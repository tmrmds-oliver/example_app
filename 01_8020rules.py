import streamlit.components as stc

# Utils
import base64 
import time
timestr = time.strftime("%Y%m%d-%H%M%S")
import pandas as pd 
import streamlit as st
import numpy as np
import pickle
import pandas as pd
from io import BytesIO
# from pyxlsb import open_workbook as open_xlsb
# pip install pyxlsb
# pip install xlsxwriter

# 這邊就用80/20
# 問題：如何將某檔案上傳，取95%利潤；product取會員？

# --------------- 定義function區 -------------------

def user_input_features():
    
    # para: year 
    year = st.sidebar.selectbox('Year', range(2018, 2020))
    month = st.sidebar.selectbox('Month', range(1, 13))
    date = st.sidebar.selectbox('Date', range(1, 31))
    
    # para: product 
    product = st.sidebar.selectbox('查看標的',('系列','去識別化會員編碼'))
    
    # para: profit 
    profit = st.sidebar.selectbox('計算標的',('利潤','單價'))
    
    # profit_percent
    profit_percent  = st.sidebar.slider('需要貢獻多少比例的利潤', 0.1,1.0,0.8)
    
    data = {'year': str(year)+ '-'+ str(month) +'-'+str(date),
            'product': product,
            'profit': profit,
            'profit_percent': profit_percent,
            }
    # features = pd.DataFrame(data, index=[0])
    return data



def product_contribution(data, year ,product, profit,profit_percent, time):
    '''

    Parameters
    ----------
    data : dataFrame
        要放入的交易資料.
        
    year : 日期形式
        舉例：'2019-1-1'.
        
    product : 字串
        data裡面的「產品」欄位名稱.
        
    profit : 字串
        data裡面的「利潤」欄位名稱.
        
    profit_percent : int, optional
        篩選貢獻多少「%」利潤優先分析的產品. The default is 0.8.

    Returns
    -------
    建議優先分析的產品.

    '''
    from dateutil import parser
        
    sales_data_2019 = data[ (data[time] > parser.parse(year)) ]

    # 產品/貢獻比例：計算每一個產品的利潤總和
    product_profit =  sales_data_2019.groupby(product, as_index = False )[profit].sum()
    product_profit = product_profit.sort_values(profit, ascending = False  )
    
    # 產品的貢獻比
    product_profit['利潤佔比'] = product_profit[profit] / product_profit[profit].sum()
    product_profit['累計利潤佔比'] = product_profit['利潤佔比'].cumsum()
    
    # 產品比
    product_profit['累計產品次數'] = range(1,len(product_profit)+1)
    product_profit['累計產品佔比'] = product_profit['累計產品次數'] / len(product_profit)
    
    # 四捨五入
    product_profit['累計產品佔比'], product_profit['累計利潤佔比'],product_profit['利潤佔比'] = round(product_profit['累計產品佔比'], 2), round(product_profit['累計利潤佔比'], 2), round(product_profit['利潤佔比'], 2)
    
    # 輸出篩選產品貢獻度（利潤）資料
    product_profit.to_csv('0_產品貢獻度（利潤）表.csv', encoding = 'utf-8-sig')
    
    # 產品/貢獻度比例圖
    import plotly.express as px
    
    fig = px.bar(product_profit, x=product, y='利潤佔比',
                 hover_data=['累計利潤佔比', '累計產品佔比'], color=profit,
                 text = '累計利潤佔比',
                 height= 400,
                 title='產品/貢獻度比例圖'
                 )
    fig.update_traces( textposition='outside')
    st.plotly_chart(fig)
    
    
    # 篩選貢獻80%利潤的產品
    
    product_profit_selected = product_profit[product_profit['累計利潤佔比']<=profit_percent]
    
    import plotly.express as px
    
    fig2 = px.bar(product_profit_selected, x=product, y='利潤佔比',
                 hover_data=['累計利潤佔比', '累計產品佔比'], color=profit,
                 text = '累計利潤佔比',
                 height= 600,
                 title='貢獻' + str(profit_percent*100) + '%的' + '產品貢獻度比例圖'
                 )
    fig.update_traces( textposition='outside')
    st.plotly_chart(fig2)
    
    with st.expander("Data Types Summary"):
        st.dataframe(product_profit_selected)
    # 建議優先分析的產品
    download = csv_downloader(product_profit_selected,
                                  filename='1_' + '貢獻' + str(profit_percent*100) + '%的' + '產品貢獻度比例表')

    
    st.markdown("#### Download File ###")
    to_excel(product_profit_selected)
    
def csv_downloader(data,filename):
	csvfile = data.to_csv()
	b64 = base64.b64encode(csvfile.encode("UTF-8-sig")).decode()
	new_filename = filename+"_{}_.csv".format(timestr)
	st.markdown("#### Download File ###")
	href = f'<a href="data:file/csv;base64,{b64}" download="{new_filename}">Click Here!!</a>'
	st.markdown(href,unsafe_allow_html=True)


def to_excel(df):
    towrite = BytesIO()
    downloaded_file = df.to_excel(towrite, index=False, header=True) # write to BytesIO buffer
    towrite.seek(0)  # reset pointer
    b64 = base64.b64encode(towrite.read()).decode() 
    linko= f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="myfilename.xlsx">Download excel file</a>'
    st.markdown(linko, unsafe_allow_html=True)

# --------------- Display -------------------

st.write("""
# 零售案例 80/20法則 - 重點系列產品選擇 App

""")

st.sidebar.header('User Input Features')

uploaded_file = st.sidebar.file_uploader("請上傳您的CSV檔案", type=["csv"])

if uploaded_file is not None:
    sales_data = pd.read_csv(uploaded_file)
else:
    sales_data = pd.read_csv('data/sales_data_sample.csv')
    # input_df = user_input_features()
para = user_input_features()

st.header('Specified Input parameters')
st.write(para)
st.write('---')


# df = input_df

# %%

#### 讀取訂單資料
# sales_data = pd.read_csv('sales_data.csv')
sales_data['利潤'] = sales_data['單價'] - sales_data['成本']

# 將訂單時間轉換成datetime形式
sales_data['訂單時間'] = pd.to_datetime(sales_data['訂單時間'])
sales_data.info()

# st.dataframe(sales_data)

# Displays the user input features
st.subheader('User Input features')

if uploaded_file is not None:
    st.write(sales_data)
else:
    st.write('Awaiting CSV file to be uploaded. Currently using example input parameters (shown below).')
    st.write(sales_data)


# Descriptive
		
with st.expander("Data Types Summary"):
	st.dataframe(sales_data.dtypes)

with st.expander("Descriptive Summary"):
	st.dataframe(sales_data.describe())

with st.expander("廣告代號all Distribution"):
	st.dataframe(sales_data['廣告代號all'].value_counts())

with st.expander("系列 Distribution"):
	st.dataframe(sales_data['系列'].value_counts())


st.header('產品/貢獻度比例圖匯總')
# 使用function
## 參數說明
# - data：我們要放入分析的資料
# - year：從什麼日期開始往後計算產品的利潤，舉例：2019-1-1
# - product：【注意！】資料要具有product的欄位名稱，或者對應的欄位名稱，如：產品，那就要將本參數改成'產品'
# - profit：說明要計算產品利潤
# - profit_percent：計算多少的產品有超過80%的利潤貢獻分析

product_contribution(
                     data=sales_data, 
                     year=para['year'] ,
                     product=para['product'], 
                     profit=para['profit'],
                     time = '訂單時間',
                     profit_percent =para['profit_percent'])


