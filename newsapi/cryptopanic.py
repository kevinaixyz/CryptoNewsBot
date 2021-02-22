import pandas as pd
import requests
from datetime import datetime, date
import io
from config import config


class CryptoPanic:
    url = 'https://cryptopanic.com/api/v1/posts/?auth_token={}'.format(
        config.cryptopanic_auth_token) + '&kind=news&region=en&filter=&currencies={}'
    @classmethod
    def get_ccy_list(cls, ccy_list):
        token_list = []
        for ccy in ccy_list:
            token_list.append(ccy['code'])
        return token_list

    @classmethod
    def parse_cryptopanic_news(cls, session, url, token, post_list, from_date, to_date):
        resp = session.get(url)
        resp_obj = resp.json()
        post_list.extend(resp_obj['results'])
        batch_date = date.fromisoformat(post_list[-1]['created_at'][0:10])
        if 'next' in resp_obj and resp_obj['next'] is not None and batch_date >= from_date:
            next_url = resp_obj['next']
            return cls.parse_cryptopanic_news(session, next_url, token, post_list, from_date, to_date)
        else:
            news_list = []
            for post in post_list:
                news = {
                    'source': post['source']['domain'],
                    'id': post['id'],
                    'url': post['url'],
                    'title': post['title'],
                    'currencies': cls.get_ccy_list(post['currencies']) if 'currencies' in post else [],
                    'token': token,
                    'publish_datetime': post['created_at']}
                news_list.append(news)
                news_df = pd.DataFrame(news_list)
                # news_df.set_index('id', inplace=True)
                news_df['publish_date'] = news_df['publish_datetime'].apply(
                    lambda x: datetime.strptime(x[0:10], '%Y-%m-%d'))
                news_df.sort_values('publish_date', inplace=True)
                news_df = news_df.query('publish_date>=@from_date & publish_date<=@to_date')
        return news_df

    @classmethod
    def extract_cryptopanic_news(cls, from_date, to_date, tokens):
        df_list = []
        req_session = requests.Session()
        page = 1
        # tokens = config.tokens
        for token in tokens:
            print('{} - {}'.format('cryptopanic', token))
            token_url = cls.url.format(token)
            post_list = []
            df = cls.parse_cryptopanic_news(req_session, token_url, token, post_list, from_date, to_date)
            df_list.append(df)
            # if from_date is not None:
            #     # df = df.query('publish_date>=@from_date')
            #     # if df.iloc[-1]['publish_date'].date()>=from_date:

            #     page=page+1
        df = pd.concat(df_list, ignore_index=True)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        value = buffer.getvalue()
        buffer.close()
        # save to CSV
        # outdir = os.getcwd()+'/NewsDownloader/downloads'
        # if not os.path.exists(outdir):
        #     os.mkdir(outdir)
        # file_name = 'cryptopanic-({}-{}).csv'
        # fullname = os.path.join(outdir, file_name.format(from_date.isoformat(), to_date.isoformat()))
        # df.to_csv(fullname)

        return value