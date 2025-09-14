def count_keywords(keywords):
    return pd.Series(keywords).value_counts()
