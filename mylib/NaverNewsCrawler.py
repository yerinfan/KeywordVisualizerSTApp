# 검색 API 호출, 응답을 JSON 데이터로 return하는 함수 작성
# API 호출 결과에 문제가 있을 경우 exception으로 처리
# exception 발생 시 exception과 호출 url 확인
import urllib.request
import json

def searchNaverNews(keyword, start, display):

    client_id = "WwKDIVdAlu63Ljcj0cE6"
    client_secret = "vu7tyVzVx5"

    # 한글 검색어 안전하게 변환
    encText = urllib.parse.quote(keyword)

    # url + query 생성
    url = "https://openapi.naver.com/v1/search/news.json?query=" + encText # JSON 결과

    # request message 구성
    new_url = url + f"&start={start}&display={display}"
    request = urllib.request.Request(new_url)
    request.add_header("X-Naver-Client-Id",client_id)
    request.add_header("X-Naver-Client-Secret",client_secret)

    resultJSON = None
    try:
        #request -> response 받아오기
        response = urllib.request.urlopen(request)
        
        # 받아온 결과가 정상인지 확인
        rescode = response.getcode()
        
        if(rescode==200):
            #정상이면 데이터 읽어오기
            response_body = response.read()
            # 한글이 있으면 utf-8로 decoding 하기
            resultJSON = json.loads(response_body.decode('utf-8'))
        else:
            print("Error Code:" + rescode)
    except Exception as e :
        print(e)
        print(f"Error:{new_url}")

    return resultJSON

#응답데이터를 리스트에 저장 (검색 결과는 json의 'items'에 들어 있음)
def setNewsSearchResult(resultAll, resultJSON):
    for result in resultJSON['items']:
        resultAll.append(result)

# JSON의 list를 dataframe으로 변환하여 csv 파일로 저장
def saveSearchResult_CSV(json_list, filename):
    import pandas as pd
    data_df = pd.DataFrame(json_list)
    data_df.to_csv(filename)
    print(f"{filename} SAVED")

# 검색어 입력 함수
def insertKeyword(keyword):
    resultAll = []
    start = 1
    display = 10
    resultJSON = searchNaverNews(keyword, start, display)

    while (resultJSON != None) and (resultJSON['display'] > 0):
        setNewsSearchResult(resultAll, resultJSON)
        start += resultJSON['display']
        resultJSON = searchNaverNews(keyword, start, display)

    filename = f"./data/{keyword}_naver_news.csv"
    saveSearchResult_CSV(resultAll, filename)
    return filename