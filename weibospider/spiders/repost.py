#!/usr/bin/env python
# encoding: utf-8
"""
Author: nghuyong
Mail: nghuyong@163.com
Created Time: 2020/4/14
"""
import json
import os

from scrapy import Spider
from scrapy.http import Request
from spiders.common import parse_tweet_info, url_to_mid
import dropbox
import tempfile


class RepostSpider(Spider):
    """
    微博转发数据采集
    """
    name = "repost"

    def start_requests(self):
        """
        爬虫入口
        """
        # Dropbox API token
        dbx_token = os.environ.get('ACCESS_TOKEN')
        dbx_path = '/Dissertation/weibo_data/records_and_logs/combined_post_ids.txt'

        # Connect to Dropbox
        dbx = dropbox.Dropbox(dbx_token)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            # Download the file from Dropbox
            _, res = dbx.files_download(dbx_path)
            temp_file.write(res.content.decode('utf-8'))
            temp_file.seek(0) # Go back to the beginning of the file

            # Read the ID list from the temporary file
            tweet_ids = [line.strip() for line in temp_file]

        # Delete the temporary file
        os.remove(temp_file.name)

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
