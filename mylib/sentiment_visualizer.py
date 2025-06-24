import glob
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import streamlit as st

@st.cache_data
def load_and_label(folder_path: str, review_col="review", score_col="score"):
    """폴더 내 CSV 로드 + score → label 변환"""
    paths = glob.glob(f"{folder_path}/*.csv")
    if not paths:
        raise FileNotFoundError(f"No CSV files in {folder_path!r}")
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    df = df.dropna(subset=[review_col, score_col]).copy()
    def to_label(s):
        if s >= 8:   return "positive"
        if s <= 3:   return "negative"
        return "neutral"
    df["label"] = df[score_col].apply(to_label)
    return df

def plot_distribution(df, label_col="label"):
    """원본 분포 Bar chart"""
    counts = df[label_col].value_counts()
    st.subheader("1) 원본 감성 분포")
    st.bar_chart(counts)

def train_and_predict(df, review_col="review", label_col="label"):
    """TF-IDF + LogisticRegression 학습 → y_test, y_pred, classes 반환"""
    X_train, X_test, y_train, y_test = train_test_split(
        df[review_col], df[label_col],
        test_size=0.2, stratify=df[label_col], random_state=42
    )
    vect = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
    X_tr = vect.fit_transform(X_train)
    X_te = vect.transform(X_test)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_tr, y_train)
    y_pred = model.predict(X_te)
    return y_test, y_pred, model.classes_

def show_classification_report(y_test, y_pred):
    """Classification Report 데이터프레임으로 표시"""
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).T
    st.subheader("2) Classification Report")
    st.dataframe(report_df)

def plot_confusion(y_test, y_pred, classes):
    """Confusion Matrix heatmap"""
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    fig, ax = plt.subplots()
    cax = ax.matshow(cm, cmap="Blues")
    fig.colorbar(cax)
    ax.set_xticks(np.arange(len(classes)))
    ax.set_yticks(np.arange(len(classes)))
    ax.set_xticklabels(classes)
    ax.set_yticklabels(classes)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    st.subheader("3) Confusion Matrix")
    st.pyplot(fig)

def generate_wordclouds(df, text_col="review", label_col="label"):
    """감성별 워드클라우드 출력"""
    st.subheader("4) 감성별 워드클라우드")
    stop = set(STOPWORDS) | {"game","games","one","the","play","played","really","feel","time","will","story","good"}
    for lbl in ["negative","neutral","positive"]:
        texts = df[df[label_col]==lbl][text_col].astype(str)
        if texts.empty:
            st.write(f"`{lbl}` 리뷰 없음")
            continue
        wc = WordCloud(
            font_path="c:/Windows/Fonts/malgun.ttf",
            background_color="white",
            width=600, height=400,
            stopwords=stop
        ).generate(" ".join(texts))
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.markdown(f"**{lbl} 워드클라우드**")
        st.pyplot(fig)
