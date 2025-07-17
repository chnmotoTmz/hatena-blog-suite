import pandas as pd

# CSVファイルのパス
csv_path = 'data/genre_prompts.csv'

df = pd.read_csv(csv_path)

# ジャンルごとにグループ化して件数を表示
print('ジャンルごとの件数:')
print(df['ジャンル'].value_counts())
print('\nジャンルごとのサンプル:')
for genre, group in df.groupby('ジャンル'):
    print(f'--- {genre} ---')
    print(group[['キーワード', 'プロンプト']].head(1).to_string(index=False))
    print()
