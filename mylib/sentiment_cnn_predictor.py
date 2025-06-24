# mylib/sentiment_cnn_predictor.py

import tensorflow as tf
import pickle
import numpy as np
import re
from tensorflow.keras.preprocessing.sequence import pad_sequences

def clean_text(text):
    return re.sub(r"[^가-힣\s]", "", str(text))

def load_cnn_model(model_path="cnn_bilstm_model.h5", tokenizer_path="tokenizer_final.pkl"):
    model = tf.keras.models.load_model(model_path)
    with open(tokenizer_path, "rb") as f:
        tokenizer = pickle.load(f)
    return model, tokenizer

def predict_sentiment(text, model, tokenizer, max_len=100):
    text = clean_text(text)
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=max_len)
    pred = model.predict(padded)
    label_idx = np.argmax(pred, axis=1)[0]
    confidence = float(np.max(pred))
    label_map = {0: "부정", 1: "중립", 2: "긍정"}
    return label_map[label_idx], confidence
