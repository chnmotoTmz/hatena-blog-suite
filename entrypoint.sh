#!/bin/bash
# RAGモデル自動再学習
python -c "import pandas as pd; from src.rag import train_and_save_model; df = pd.read_csv('data/genre_prompts.csv'); texts = df['プロンプト'].tolist(); train_and_save_model(texts, 'genre_prompts')"
# 本来のアプリ起動
exec python main.py
