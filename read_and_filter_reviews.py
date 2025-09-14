def read_and_filter_reviews(file_path, score_column='评分', review_column='评价', threshold=4.0):
    df = pd.read_excel(file_path)
    return df[df[score_column] < threshold][review_column].dropna().tolist()
