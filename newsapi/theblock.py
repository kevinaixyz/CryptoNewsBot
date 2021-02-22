import pandas as pd
import requests
from datetime import datetime
from config import config


class TheBlock:

    url = 'https://www.theblockcrypto.com/wp-json/v1/posts/?post_type={}&page={}&s={}&category={}&tag={}&author={}&posts_per_page={}'

    block_header = {
        'referer': 'https://www.theblockcrypto.com/',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'
    }
    @classmethod
    def get_theblock_new_cats(cls, tag_list):
        tags = []
        for t in tag_list:
            tags.append(t['name'])
        return tags

    @classmethod
    def relate_to_index_tokens(cls, tags):
        tokens = config.tokens
        is_relate = 'N'
        tags_str = ','.join(tags)
        for token in tokens:
            if token in tags_str or token.lower() in tags_str:
                is_relate = 'Y'
        return is_relate

    @classmethod
    def parse_theblock_news(cls, resp):
        posts = resp.json()['posts']
        block_news_list = []
        for post in posts:
            news = {
                'id': 'theblock-'+str(post['id']),
                'title': post['title'],
                'content': post['body'],
                'label': post['label'],
                'category': cls.get_theblock_new_cats(post['categories']),
                'tags': ','.join(cls.get_theblock_new_cats(post['tags'])),
                'publish_datetime': post['published'],
                'url': post['url'],
                'certainty_num': '',
                'certainty': '',
                'impact': ''
            }
            block_news_list.append(news)
        block_df = pd.DataFrame(block_news_list)
        block_df['date'] = block_df['publish_datetime'].apply(lambda x: datetime.strptime(x[0:10], '%Y-%m-%d').date())
        block_df['week'] = block_df['date'].apply(lambda x: x.isocalendar()[1])
        block_df = block_df[
            ['id', 'date', 'week', 'title', 'tags', 'certainty_num', 'certainty', 'impact',
             'url']]
        block_df.sort_values(by=['date'], inplace=True)
        return block_df

    @classmethod
    def extract_theblock_news(cls, from_date, to_date):
        df_list = []
        block_s = requests.Session()
        page = 1

        while True:
            new_url = cls.url.format('', page, '', '', '', '', 20)
            r = block_s.get(new_url, headers=cls.block_header)
            df = cls.parse_theblock_news(r)
            print('{} - {}'.format('the-block', df.iloc[-1]['date']))
            if df.iloc[-1]['date'] >= from_date:
                df_list.append(df)
                page = page + 1
            else:
                break
        df = pd.concat(df_list)
        df = df.query('date>=@from_date & date<=@to_date').copy()
        df.sort_values(by=['date'], inplace=True)
        # save to CSV
        # outdir = os.getcwd()+'/NewsDownloader/downloads'
        #
        # if not os.path.exists(outdir):
        #     os.mkdir(outdir)
        # fullname = os.path.join(outdir, 'theblock.csv')
        # print(fullname)
        # df.to_csv(fullname)
        return df
