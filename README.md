pyspider 
========

base binux/pyspider

1.add request cache
```python
 crawl_config = {
   'requestdb':{
       'table':'', 
       'itag':'',
       'disallow':{
           'url': [u'error.shtml']
       },
   },
 }
```
