pyspider 
========

base binux/pyspider
add request cache(only for mongo)
add multi lang.

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
       },
   },
 }
```
