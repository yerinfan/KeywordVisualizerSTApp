#mylib\myTextMining.py
from collections import Counter

def load_corpus_from_csv(corpus_file, col_name):
    import pandas as pd
    data_df = pd.read_csv(corpus_file)
    result_list = list(data_df[col_name])
    return result_list

def tokenize_korean_corpus(corpus_list, tokenizer, tags, stopwords):
    
    text_pos_list = []
    for text in corpus_list:
         if isinstance(text, str):  # 문자열일 때만 처리
            text_pos = tokenizer(text)
            text_pos_list.extend(text_pos)
    token_list = [token for token, tag in text_pos_list if tag in tags and token not in stopwords]
    return token_list

def analyze_word_freq(corpus_list, tokenizer, tags, stopwords):
    token_list = tokenize_korean_corpus(corpus_list, tokenizer, tags, stopwords)
    counter = Counter(token_list)
    return counter

def visualize_barchart(counter, title, xlabel, ylabel, max_words=20):
    import matplotlib.pyplot as plt
    from matplotlib import font_manager, rc
    import streamlit as st

    most_common = counter.most_common(max_words)
    word_list = [word for word, _ in most_common]
    count_list = [count for _, count in most_common]

    font_path = "c:/Windows/Fonts/malgun.ttf"
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_name)

    fig, ax = plt.subplots()
    ax.barh(word_list[::-1], count_list[::-1])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    st.pyplot(fig)  # ✅ Streamlit에서 그래프 출력
    
def visualize_wordcloud(counter, max_words=50):
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    import streamlit as st

    font_path = "c:/Windows/Fonts/malgun.ttf"
    wordcloud = WordCloud(font_path=font_path,
                          width=600,
                          height=400,
                          max_words=max_words,
                          background_color='ivory').generate_from_frequencies(counter)

    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')

    st.pyplot(fig)  # ✅ Streamlit에서 이미지 출력