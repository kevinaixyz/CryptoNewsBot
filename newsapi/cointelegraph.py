import pandas as pd
import requests
from datetime import datetime, date
import os


class Cointelegraph:
    url = 'https://cointelegraph.com/api/v1/content/json/_mp?lang=en&page={}'
    cointelegraph_headers = {
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://cointelegraph.com',
        'referer': 'https://cointelegraph.com/',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
    }

    @classmethod
    def parse_cointelegraph_news(cls, resp):
        posts = resp.json()['posts']
        news_list = []
        if posts == None:
            return
        for post in posts:
            # filter out news that is not latest news
            if post['category_title']!='Latest News':
                continue
            news = {
                'id': 'cointelegraph-'+str(post['id']),
                'publish_datetime': post['publishedW3'],
                'title': post['title'],
                'category': post['category_title'],
                'lead': post['lead'],
                'url': post['url'],
                'certainty_num': '',
                'certainty': '',
                'impact': ''
            }
            news_list.append(news)
        df = pd.DataFrame(news_list)
        df['date'] = df['publish_datetime'].apply(lambda x: datetime.strptime(x[0:10], '%Y-%m-%d').date())
        df['week'] = df['date'].apply(lambda x: x.isocalendar()[1])
        df = df[['id', 'date', 'week', 'title', 'category', 'certainty_num', 'certainty', 'impact', 'url']]
        return df

    @classmethod
    def extract_cointelegraph_news(cls, from_date, to_date):
        page = 1
        df_list = []
        s = requests.Session()

        while True:
            new_url = cls.url.format(page)
            r = s.post(new_url, headers=cls.cointelegraph_headers)
            df = cls.parse_cointelegraph_news(r)
            print('{} - {}'.format('cointelegraph', df.iloc[0]['date']))
            if df.iloc[0]['date'] >= from_date:
                page = page + 1
                df_list.append(df)
            else:
                break
        df = pd.concat(df_list)
        df.sort_values(by=['date'], inplace=True)
        df = df.query('date>=@from_date & date<=@to_date').copy()
        # save to CSV
        # outdir = os.getcwd()+'/NewsDownloader/downloads'
        # if not os.path.exists(outdir):
        #     os.mkdir(outdir)
        # fullname = os.path.join(outdir, 'cointelegraph.csv')
        # df.to_csv(fullname)
        return df
