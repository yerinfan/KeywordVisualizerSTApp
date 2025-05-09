# sentiment_analyzer.py

import pandas as pd
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# 초기 설정 (최초 실행 시만 다운로드 필요)
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

def analyze_sentiment(df: pd.DataFrame, text_column: str = "review") -> pd.DataFrame:
    """
    감성 분석을 수행하고 결과 컬럼을 추가한 DataFrame을 반환합니다.
    Parameters:
        df (pd.DataFrame): 리뷰 데이터프레임
        text_column (str): 리뷰가 들어 있는 컬럼명 (기본값 "review")
    Returns:
        pd.DataFrame: 감정점수 및 분류가 추가된 데이터프레임
    """
    if text_column not in df.columns:
        raise ValueError(f"컬럼 '{text_column}'이(가) DataFrame에 없습니다.")

    df = df.copy()
    df["감정점수"] = df[text_column].astype(str).apply(lambda x: sia.polarity_scores(x)["compound"])
    df["감정분류"] = df["감정점수"].apply(
        lambda s: "긍정" if s >= 0.05 else ("부정" if s <= -0.05 else "중립")
    )
    return df
