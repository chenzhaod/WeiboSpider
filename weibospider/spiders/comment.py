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
from spiders.common import parse_user_info, parse_time, url_to_mid
import os
import dropbox
import tempfile


class CommentSpider(Spider):
    """
    微博评论数据采集
    """
    name = "comment"

    def start_requests(self):
        """
        爬虫入口
        """
        # Dropbox API token, 20231205
        dbx_token = os.environ.get('ACCESS_TOKEN')
        dbx_path = '/Dissertation/weibo_data/records_and_logs/combined_post_ids.txt'

        # Connect to Dropbox, 20231205
        dbx = dropbox.Dropbox(dbx_token)

        # Create a temporary file, 20231205
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            # Download the file from Dropbox
            _, res = dbx.files_download(dbx_path)
            temp_file.write(res.content.decode('utf-8'))
            temp_file.seek(0) # Go back to the beginning of the file

            # Read the ID list from the temporary file, 20231205
            tweet_ids = [line.strip() for line in temp_file]


        # 这里tweet_ids可替换成实际待采集的数据
        #tweet_ids = ['Mb15BDYR0']
        for tweet_id in tweet_ids:
            mid = url_to_mid(tweet_id)
            url = f"https://weibo.com/ajax/statuses/buildComments?" \
                  f"is_reload=1&id={mid}&is_show_bulletin=2&is_mix=0&count=20"
            yield Request(url, callback=self.parse, meta={'source_url': url, 'original_tweet_id': tweet_id})
            # added original_tweet_id as metadata, 20231205

    def parse(self, response, **kwargs):
        """
        网页解析
        """
        data = json.loads(response.text)
        original_tweet_id = response.meta['original_tweet_id'] # retrieve original tweet id from meta data, 20231205
        for comment_info in data['data']:
            item = self.parse_comment(comment_info, original_tweet_id) # added original tweet id, 20231205
            yield item
        if data.get('max_id', 0) != 0:
            url = response.meta['source_url'] + '&max_id=' + str(data['max_id'])
            yield Request(url, callback=self.parse, meta=response.meta)

    @staticmethod
    def parse_comment(data, original_tweet_id=None): # added original_tweet_id, 20231205
        """
        解析comment
        """
        item = dict()
        item['original_tweet_id'] = original_tweet_id # added 20231205
        item['created_at'] = parse_time(data['created_at'])
        item['_id'] = data['id']
        item['like_counts'] = data['like_counts']
        item['ip_location'] = data['source']
        item['content'] = data['text_raw']
        item['comment_user'] = parse_user_info(data['user'])
        return item
