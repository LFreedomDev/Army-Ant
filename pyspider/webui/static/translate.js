
window.Translate = {
    "debug":true,
    "languages": {
        "default":{
            "title":"Default",
            "maps":{}
        },
        "zh-CN":{
            "title":"简体中文",
            "maps":{
                "scheduler":"调度器",
                "fetcher":"采集器",
                "processor":"处理器",
                "result_worker":"结果工作单元",
                "group":"分组",
                "project name":"项目名称",
                "status":"状态",
                "rate/burst":"速率/并发",
                "avg time":"耗时",
                "progress":"进度",
                "actions":"操作",
                "Create":"创建",
                "Recent Active Tasks":"最近任务",
                "Create New Project":"新建项目",
                "Project Name":"项目名称",
                "Start URL(s)":"入口链接",
                "Mode":"模式",
                "Close":"关闭",
                "Create":"创建",
                "Run":"运行",
                "Active Tasks":"活动任务",
                "Results":"结果集",
                "pyspider":"控制台",
                "Documentation":"文档",
                "WebDAV Mode":"WebDAV模式",
                "run":"运行",
                "messages":"消息",
                "follows":"跟寻",
                "html":"源码",
                "web":"WEB",
                "enable css selector helper":"CSS选择器",
                "save":"保存",
                "Project is not started, please set status to RUNNING or DEBUG.":"项目没有启动，请设置状态为 RUNNING 或 DEBUG."
            }
        },
        "zh-TW":{
            "title":"繁體中文",
            "maps":{
                "scheduler":"調度器",
                "fetcher":"采集器",
                "processor":"處理器",
                "result_worker":"結果工作單元",
                "group":"分組",
                "project name":"項目名稱",
                "status":"狀態",
                "rate/burst":"速率/并發",
                "avg time":"耗時",
                "progress":"進度",
                "actions":"操作",
                "Create":"創建",
                "Recent Active Tasks":"最近任務",
                "Create New Project":"新建項目",
                "Project Name":"項目名稱",
                "Start URL(s)":"入口鏈接",
                "Mode":"模式",
                "Close":"關閉",
                "Create":"創建",
                "Run":"運行",
                "Active Tasks":"活動任務",
                "Results":"結果集",
                "pyspider":"控制臺",
                "Documentation":"文檔",
                "WebDAV Mode":"WebDAV模式",
                "run":"運行",
                "messages":"消息",
                "follows":"跟尋",
                "html":"源碼",
                "web":"WEB",
                "enable css selector helper":"CSS選擇器",
                "save":"保存",
                "Project is not started, please set status to RUNNING or DEBUG.":"項目沒有啓動,請設置狀態為 RUNNING 或 DEBUG."
            }
        }
    }
}

function _translate(){

    function _setLang(lang) {
        _delLang();
        var Days = 30;
        var exp = new Date();
        exp.setTime(exp.getTime() + Days*24*60*60*1000);
        document.cookie = "lang="+ escape (lang) + ";expires=" + exp.toGMTString()+";path=/";
    }

    function _getLang() {
        var arr,reg=new RegExp("(^| )lang=([^;]*)(;|$)");
        if(arr=document.cookie.match(reg))
        return unescape(arr[2]);
        else return navigator.language;
    }

    function _delLang() {
        var exp = new Date();
        exp.setTime(exp.getTime() - 1);
        var cval=_getLang();
        if(cval!=null)
        document.cookie= "lang="+cval+";expires="+exp.toGMTString()+";path=/";
    }

    function _translateNode(element,lang){
        var parent = element.parentNode;
        var okey = $(element.parentNode).attr("data-okey");
        if(okey==undefined){
            okey=element.nodeValue;
            $(element.parentNode).attr("data-okey",okey); 
        }
        okey=okey.trim();
        var val = (lang=="default") ? okey:window["Translate"]["languages"][lang]["maps"][okey];
        if(val!=undefined){
            element.nodeValue = val;
        }
        else if(window.Translate["debug"]){
            console.log('"'+okey+'":"",')
        }
    }

    this.change = function(lang){
        if(lang==undefined || lang==null ||lang=="") lang =_getLang();
        if(window["Translate"]["languages"][lang]==undefined){
            lang="default";
        }
        _setLang(lang);
        
        var language =window["Translate"]["languages"][lang];
        var ignore = $(".CodeMirror,pre").find("*").contents().toArray();

        $("body").find("*").contents().toArray().filter(m=>m.nodeType==3).filter(m=>m.nodeValue.trim()!='' && !ignore.includes(m)).forEach(element => _translateNode(element,lang));
        if(document.getElementById("translate-lang-current"))
            document.getElementById("translate-lang-current").textContent = language["title"];
    }

    this.setControl = function(){
        var control=`<div class="btn-group dropup" style="position:fixed;bottom:0px;right:0px;">
            <button type="button" class="btn btn-info btn-sm"><span>Lang</span> : <span id="translate-lang-current"></span></button>
            <button type="button" class="btn btn-info btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
            <span class="caret"></span>
            <span class="sr-only">Toggle Dropdown</span>
            </button>
            <ul class="dropdown-menu" id="translate-lang-list">
            </ul>
        </div>`;

    
        $("body").append(control);
        for(var key in window["Translate"]["languages"]){
            $("#translate-lang-list").append(`<li><a href="#" onclick="window.Translate.translator.change('`+key+`')">`+window["Translate"]["languages"][key]["title"]+`</a></li>`)
        }
        
    }

    if(window.location.pathname=="/")  this.setControl();
}

window.Translate["translator"] = new _translate(),

window.onload = window.Translate["translator"]["change"]();