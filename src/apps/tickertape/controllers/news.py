import requests
from dacite import from_dict

from ..models import NewsModel
from .search import SearchController


class NewsController:
    @staticmethod
    def get_last_10_news(tickersymbol: str, types: list = ['news-article', 'opinion-article']):
        search_items = SearchController.search(text=tickersymbol)
        sid = None

        for search_item in search_items:
            if search_item.ticker == tickersymbol:
                sid = search_item.sid

                break

        if not sid:
            raise ValueError('Could not find any matching element in tickertape for %s' % tickersymbol)

        # Available options for news types: news-video,news-article,opinion-article
        # news-video is currently not in default because the intention is to get the sentiment
        # from the news content
        # TODO: Possibly add it back because we are only getting sentiment from the desciption / title
        response = requests.get(
            'https://api.tickertape.in/stocks/feed/%(sid)s?count=%(count)s&offset=%(offset)s&types=%(types)s' % {
                'sid': sid,
                'count': 11,  # to get last 10 news
                'offset': 0,
                'types': ','.join(types)
            }
        )

        if response.status_code != 200:
            raise ValueError('Unexpected response code found: %d, response: %s' % (response.status_code, response.text))

        news = response.json()['data']['items']

        return [from_dict(data_class=NewsModel, data=news_item) for news_item in news]
