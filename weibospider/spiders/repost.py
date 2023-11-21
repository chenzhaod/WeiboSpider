#!/usr/bin/env python
# encoding: utf-8
"""
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2020/4/14
"""
import json
from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_tweet_info, url_to_mid


class RepostSpider(Spider):
    """
    微博转发数据采集
    """
    name = "repost"

    def start_requests(self):
        """
        爬虫入口
        """
        # Relative path to the ID list file, 20231117
        file_path = '../data/combined_post_ids.txt'

        # open and read the ID list, 20231117
        with open(file_path, 'r') as file:
            tweet_ids = [line.strip() for line in file]

        # 这里tweet_ids可替换成实际待采集的数据
        #tweet_ids = ['Mb15BDYR0']
        for tweet_id in tweet_ids:
            mid = url_to_mid(tweet_id)
            url = f"https://weibo.com/ajax/statuses/repostTimeline?id={mid}&page=1&moduleID=feed&count=10"
            yield Request(url, callback=self.parse, meta={'page_num': 1, 'mid': mid, 'original_tweet_id': tweet_id})
            # added original_tweet_id as metadata, 20231106

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        data = json.loads(response.text)
        for tweet in data['data']:
            item = parse_tweet_info(tweet, original_tweet_id=response.meta['original_tweet_id']) # added original_tweet_id, 20231106
            yield item
        if data['data']:
            mid, page_num, original_tweet_id = response.meta['mid'], response.meta['page_num'], response.meta['original_tweet_id'] # added original tweet id, 20231106
            page_num += 1
            url = f"https://weibo.com/ajax/statuses/repostTimeline?id={mid}&page={page_num}&moduleID=feed&count=10"
            yield Request(url, callback=self.parse, meta={'page_num': page_num, 'mid': mid, 'original_tweet_id': original_tweet_id}) # added original tweet id, 20231106
