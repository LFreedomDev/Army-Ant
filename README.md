pyspider 
========

base binux/pyspider

#### Appends

1.request cache(only for mongo)

2.multi lang.

#### Usage

step.1 configure requestdb connection string and auto turn on request cache
```json
{ 
    "requestdb": "mongodb+requestdb://host/requestdb",
}
```

step.2 custom configure setting in project
```python
 crawl_config = {
   'requestdb':{
       'table':'',      #default with project name
       'itag':'',       #cache ver.
       'disallow':{     #disable cache rules
           'url': ['keyword_1','keyword_2','keyword_n'],
           'content':[],
       },
   },
 }
```
