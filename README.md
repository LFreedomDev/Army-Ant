pyspider 
========

base binux/pyspider

1.add request cache

 crawl_config = {
   'requestdb':{
       'table':'bookdao', #储存表
       'itag':'',     #更新缓存版本
       'disallow':{    #禁用缓存关键词匹配
           'url': [u'error.shtml']
       },
   },
 }
