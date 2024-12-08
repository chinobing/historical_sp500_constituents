import os
from datetime import date, datetime
import pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def create_constituents(df):
    # create Dataframe with current constituents
    ticker_list = []
    for i, row in df.iterrows():
        tmp_val = row['ticker']
        ticker_list.append(tmp_val)

    res_string = ','.join(ticker_list)

    results_df = pd.DataFrame({'date': date.today(),
                               'tickers': [res_string],
                               })

    return results_df

def diff_tickers(sp500):
    added_tickers = {}
    removed_tickers = {}

    for i in range(1, len(sp500.index)):
        prev_tickers = set(sp500.iloc[i - 1].tickers)
        current_tickers = set(sp500.iloc[i].tickers)

        added = current_tickers - prev_tickers
        if added:
            added_tickers[sp500.index[i]] = list(added)

        removed = prev_tickers - current_tickers
        if removed:
            removed_tickers[sp500.index[i]] = list(removed)

    at_only = pd.DataFrame(added_tickers.items(), columns=['date', 'added_tickers'])
    rt_only = pd.DataFrame(removed_tickers.items(), columns=['date', 'removed_tickers'])
    combined = pd.merge(at_only, rt_only, on=['date'], how='outer')
    combined = combined.sort_values('date', ascending=True)
    combined = combined.set_index('date')
    
    return combined


def main():
    # read historical data
    sp500_hist = pd.read_csv('sp_500_historical_components.csv')

    # current companies
    sp_500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    sp_500_constituents = pd.read_html(sp_500_url, header=0)[0].rename(columns=str.lower)
    sp_500_constituents['date'] = date.today()
    sp_500_constituents.to_csv('sp500_constituents.csv', index=False)
    sp_500_constituents.drop(['gics sector', 'gics sub-industry',
                              'headquarters location', 'date added',
                              'cik', 'founded','security'], axis=1, inplace=True)
    
    sp_500_constituents.columns = ['ticker', 'date']
    sp_500_constituents.sort_values(by='ticker', ascending=True,inplace=True)

    df = create_constituents(sp_500_constituents)
    df['date'] = pd.to_datetime(df['date']).dt.strftime("%Y-%m-%d")
    final = pd.concat([sp500_hist, df], ignore_index=True)

    # output sp_500_historical_components
    final = final.drop_duplicates(subset=['date', 'tickers'],keep='last')
    final.to_csv('sp_500_historical_components.csv', index=False)

    #
    # get added and removed components
    filename = 'sp_500_historical_components.csv'
    sp500_historical = pd.read_csv(filename, index_col='date')

    # Convert ticker column from csv to list, then sort.
    sp500_historical['tickers'] = sp500_historical['tickers'].apply(lambda x: sorted(x.split(',')))

    # sort dataframe by date
    sp500_historical = sp500_historical.sort_index()
    combined = diff_tickers(sp500_historical)
    combined.to_csv('sp500_changes_since_1996.csv')

    #
    # rewrite README.md
    changes_readme = combined.iloc[-50:]
    changes_readme = changes_readme.sort_index(ascending=False)
    
    YML = "README.md"
    f = open(YML, "r+", encoding="UTF-8")
    list1 = f.readlines()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    list1 = list1[:10]
    list1 += [f'S&P500 Constituents Auto Renew at **{current_datetime}**']
    list1 += ['\n\n']
    list1 += [changes_readme.to_markdown()]
    f = open(YML, "w+", encoding="UTF-8")
    f.writelines(list1)
    f.close()


if __name__ == '__main__':
    main()
