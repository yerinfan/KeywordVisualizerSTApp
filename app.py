import streamlit as st
from konlpy.tag import Komoran
from collections import Counter
import pandas as pd
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

from mylib.sentiment_cnn_predictor import load_cnn_model, predict_sentiment
import mylib.myTextMining as tm
import mylib.NaverNewsCrawler as nnc
from mylib.metacritic_crawler3 import crawl_game_reviews
from mylib.sentiment_analyzer import analyze_sentiment
from mylib.sentiment_visualizer import (
    load_and_label,
    plot_distribution,
    train_and_predict,
    show_classification_report,
    plot_confusion,
    generate_wordclouds
)

st.set_page_config(layout="wide")
st.sidebar.header("파일 업로드 및 분석 설정")
# — 공통 CSV 업로더 (고유 key) —
uploaded = st.sidebar.file_uploader("CSV 파일 업로드", type=["csv"], key="uploader_all")
col = st.sidebar.text_input("텍스트 컬럼명", "review", key="col_txt")
btn_check = st.sidebar.button("컬럼 확인", key="btn_check")

if btn_check and uploaded:
    df_chk = pd.read_csv(uploaded)
    if col in df_chk.columns:
        st.sidebar.success(f"'{col}' 존재함")
        st.session_state.valid = True
    else:
        st.sidebar.error(f"'{col}' 없음")
        st.session_state.valid = False

# — 뉴스 키워드 분석 —
if st.sidebar.button("뉴스 키워드 분석", key="btn_news"):
    if uploaded and st.session_state.valid:
        df = pd.read_csv(uploaded)
        corpus = df[col].dropna().tolist()
        counter = tm.analyze_word_freq(
            corpus, Komoran().pos,
            tags=['NNG','NNP','VV','VA'],
            stopwords=['하며', '입', '하고', '로써', '하여', '애', '제', '그', '이', '하', '있', '받', '영화', '것',
                 '검색', '단어', '통하', '영어', '정보', '보', '말', '인터넷', '사용', '뜻', '되', '위하', '따르']
        )
        if st.checkbox("바 차트", value=True):
            tm.visualize_barchart(counter, "뉴스 키워드","빈도","단어")
        if st.checkbox("워드클라우드", value=True):
            tm.visualize_wordcloud(counter)

# — 기존 뉴스 키워드 / Metacritic 감성 분석 UI는 그대로 아래에 배치 —
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

if start_analysis:
    st.info("분석을 시작합니다...")
    if uploaded_file is not None:
        st.success("업로드한 CSV 파일을 분석합니다.")
        df = pd.read_csv(uploaded_file)
        corpus_list = df["description"].dropna().tolist()

    tokenizer = Komoran().pos
    tags = ['NNG', 'NNP', 'VV', 'VA']
    stopwords = ['하며', '입', '하고', '로써', '하여', '애', '제', '그', '이', '하', '있', '받', '영화', '것',
                 '검색', '단어', '통하', '영어', '정보', '보', '말', '인터넷', '사용', '뜻', '되', '위하', '따르']
    counter = tm.analyze_word_freq(corpus_list, tokenizer, tags, stopwords)
    if show_bar:
        st.subheader(" 키워드 빈도수 그래프")
        tm.visualize_barchart(counter, "뉴스 키워드 분석", "빈도수", "키워드", max_words=bar_count)
    if show_wc:
        st.subheader(" 워드클라우드")
        tm.visualize_wordcloud(counter, max_words=wc_count)

st.title("🎮 Metacritic 리뷰 감성 분석기")
url = st.text_input("게임 리뷰 URL", "https://www.metacritic.com/game/elden-ring/user-reviews?platform=playstation-5", key="url_meta")
if st.button("크롤링 & 분석", key="btn_meta"):
    df_meta = crawl_game_reviews(url)
    df_meta = analyze_sentiment(df_meta)
    st.bar_chart(df_meta["감정분류"].value_counts())
    st.dataframe(df_meta)

    csv = df_meta.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 리뷰 CSV 다운로드", data=csv, file_name="metacritic_reviews.csv", mime="text/csv")

def score_to_label(s):
    if s >= 8:
        return "positive"
    elif s <= 3:
        return "negative"
    else:
        return "neutral"

@st.cache_resource
def load_model_and_tokenizer():
    return load_cnn_model("cnn_bilstm_model.h5", "tokenizer_final.pkl")

model, tokenizer = load_model_and_tokenizer()

st.title("💬 실시간 감성 분석 (텍스트 입력)")
user_input = st.text_input("문장을 입력하세요", placeholder="예: 이 게임은 정말 최고야!")
if st.button("예측하기", key="btn_predict_text"):
    if user_input.strip() == "":
        st.warning("문장을 입력해 주세요.")
    else:
        label, conf = predict_sentiment(user_input, model, tokenizer)
        st.success(f"예측 결과: **{label}** (신뢰도: {conf:.2f})")
