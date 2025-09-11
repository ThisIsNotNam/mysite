import requests
import pandas
from io import BytesIO



def getTKB():
    mtx=[['', ''], ['', 'Không có dữ liệu']]
    errorCode = 0
    try:
        session = requests.Session()
        login_url = "https://thptchuyen.hatinh.edu.vn"
        session.get(login_url)
        target_url = "https://thptchuyen.hatinh.edu.vn/upload/51504/20250904/68b95fa42051fba742037bb6325e4c/TKB_HK1-6-9-2025/tkb_class_6_0.html"
        response = session.get(target_url)
        html=response.content
        tables=pandas.read_html(BytesIO(html), encoding='utf-8')
        data=tables[0]

        data=data.fillna("")
        # data=data.drop(data.columns[0], axis=1)

        fc=data.columns[0]
        data[fc]=pandas.to_numeric(data[fc], errors='coerce').round(0).astype('Int64').combine_first(data[fc])

        mtx=data.values.tolist()

        mtx[0][0]="Tiết"
        errorCode = 0
        errorStr = ""
    except BaseException as e:
        mtx[0][0]="Thông báo"
        mtx[0][1]="Lỗi từ máy chủ, hoặc chúng tôi không thể lấy thông tin TKB từ nhà trường!"
        mtx[1][0]="Lỗi:"
        errorStr = f"{e}"
        errorCode = 1

    return mtx, errorCode, errorStr