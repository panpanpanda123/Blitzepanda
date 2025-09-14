def save_results_to_excel(keyword_freq, categories, keyword_file='关键词频率.xlsx', category_file='分类结果.xlsx'):
    keyword_freq_df = pd.DataFrame(list(keyword_freq.items()), columns=['关键词', '频率']).sort_values(by='频率', ascending=False)
    categories_df = pd.DataFrame(categories, columns=['分类结果'])
    keyword_freq_df.to_excel(keyword_file, index=False)
    categories_df.to_excel(category_file, index=False)
