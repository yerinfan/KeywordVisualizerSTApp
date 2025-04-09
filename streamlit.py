import streamlit as st
from konlpy.tag import Komoran
from collections import Counter
import mylib.myTextMining as tm
import mylib.NaverNewsCrawler as nnc
import pandas as pd
import os

uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type=["csv"])

col_name = st.sidebar.text_input("데이터가 있는 컬럼명", value="review")
check_col_button = st.sidebar.button("데이터 파일 확인")

df = None

if check_col_button:
    try:
        df = pd.read_csv(uploaded_file)
        if col_name in df.columns:
            st.sidebar.success(f"'{col_name}' 컬럼이 존재합니다!")
            st.session_state["valid_column"] = True
        else:
            st.sidebar.error(f"'{col_name}' 컬럼이 존재하지 않습니다.")
            st.session_state["valid_column"] = False
    except Exception as e:
        st.sidebar.error(f"CSV 파일을 읽을 수 없습니다: {e}")
        st.session_state["valid_column"] = False

st.sidebar.header("설정")

show_bar = st.sidebar.checkbox("빈도수 그래프", value=True)
bar_count = st.sidebar.slider("단어 수", 10, 50, 20)

show_wc = st.sidebar.checkbox("워드클라우드", value=True)
wc_count = st.sidebar.slider("단어 수", 20, 500, 50)

start_analysis = st.sidebar.button("🔍 분석 시작")

os.makedirs("./data", exist_ok=True)

# ======== 분석 로직 ========
if start_analysis:
    st.info("분석을 시작합니다...")

    # 1. corpus 데이터 불러오기
    if uploaded_file is not None:
        st.success("업로드한 CSV 파일을 분석합니다.")
        df = pd.read_csv(uploaded_file)
        corpus_list = df["description"].dropna().tolist()

    # 2. 형태소 분석 설정
    tokenizer = Komoran().pos
    tags = ['NNG', 'NNP', 'VV', 'VA']
    stopwords = ['하며', '입', '하고', '로써', '하여', '애', '제', '그', '이', '하', '있', '받', '영화', '것',
                 '검색', '단어', '통하', '영어', '정보', '보', '말', '인터넷', '사용', '뜻', '되', '위하', '따르']

    # 3. 빈도 분석
    counter = tm.analyze_word_freq(corpus_list, tokenizer, tags, stopwords)

    # 4. 시각화 출력
    if show_bar:
        st.subheader(" 키워드 빈도수 그래프")
        tm.visualize_barchart(counter, "뉴스 키워드 분석", "빈도수", "키워드", max_words=bar_count)

    if show_wc:
        st.subheader(" 워드클라우드")
        tm.visualize_wordcloud(counter, max_words=wc_count)