Army-Ant
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
           'table':string,      #存储表头
           'get':bool,          #启用获取缓存，缓存为空就重新爬取
           'force_get':bool,    #强制获取缓存，缓存为空不重新爬取
           'save':bool,         #是否保存到缓存
           'itag':int,          #缓存版本
           'disallow':{         #禁用缓存规则，response 各项字段
                'status_code':[503,502,501,500]        
           }
       },   
 }
```
