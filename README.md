네이버 뉴스 크롤링 Streamlit 프로젝트

네이버 뉴스 검색 api 활용하여 웹 크롤링 학습을 진행 중입니다.


1. 검색어를 입력하면 관련 검색어의 뉴스 기사들을 크롤링하여 csv파일로 추출할 수 있다.
2. csv 파일을 전송하면 해당 파일의 키워드 빈도수를 바차트로 시각화
3. csv 파일의 키워드 빈도 기반 워드클라우드 이미지 생성 및 출력 가능
4. 텍스트 분석 기능을 라이브러리 형태로 모듈화


+ metacritic 게임 사용자 리뷰 크롤러 & 감성분석

metacritic 사이트의 게임 리뷰를 크롤링합니다. 
이 때 리뷰 점수 3이하는 부정, 8이상을 긍정, 나머지 중립으로 처리하였습니다.

Streamlit에서 제공하는 기능
1. Metacritic URL 기반 리뷰 크롤링 → 감성분석
2. 분석된 리뷰 CSV 다운로드 버튼 제공
3. 리뷰 점수 기반 감정 레이블링 → 분포 시각화
4. 텍스트 감성 예측 (입력창 기반)

영어 리뷰의 경우 메타크리틱 리뷰 약 40만건을 이용하여 cnn 기반으로 감성 분석 학습을 진행하였습니다.
val_accuracy 결과 약 80%

한국어 리뷰의 경우 영어 리뷰를 lm studio를 이용해 번역한 한글 리뷰와 팀원의 한국어 리뷰를 통합 데이터(약 30만건)를 사용하였습니다.
감성 분성 학습은 biLSTM과 cnn을 결합하여 진행하였습니다.
val_accuracy 결과 약 70%



사용한 기술스택
Python 3.10 
TensorFlow 2.10 + Keras
Streamlit
NLTK (SentimentIntensityAnalyzer)
scikit-learn
Selenium (Metacritic 크롤링)
KoNLPy + Komoran (뉴스 키워드 분석)
Matplotlib, WordCloud
