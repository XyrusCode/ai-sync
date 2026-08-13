#!/usr/bin/env python3
import json, os, re
from pathlib import Path

SVG_DIR = Path("/Users/moonshot/kimi-design-skill/assets/icons")
OUT_DIR = Path("/Users/moonshot/kimi-design-skill/references/icons")
CAT_DIR = OUT_DIR / "categories"
CAT_DIR.mkdir(parents=True, exist_ok=True)

# Classification rules: keyword -> category
KEYWORD_CAT = {
    "arrows": ["up","down","left","right","upperleft","upperright","lowerleft","lowerright",
               "leftright","updown","change","enter","previous","next","collapse","expand",
               "goback","moveforward","unfold"],
    "formatting": ["bold","italic","underline","strikethrough","leftalign","centeralign","rightalign",
                   "justify","topup","bottom","moveup","movedown","linespace","wordspace","intervalspace",
                   "topalign","bottomalign","centervertically","wraptext","flatten","ordered","pagestyle"],
    "image": ["crop","rotate","flip","alpha","colorless","textcolor","cropping","replace",
              "imagecreate","imagefailed","imageicon","imagegenerate","croprotation","watermark"],
    "data": ["diagram","tabular","linechart","histogram","viewall","data","model","prism","knowledge","mcp"],
    "brand": ["apple","android","kimiplus","kimiold","alphalab","okcomputer",
              "webbridge","koder","prism","robot","k15"],
    "chat": ["addconversation","catalog","volon","voloff","phonecall","publishpost","comment","send_"],
    "input": ["upload","uploadfile","uploadwechat","circleplus","keyboard","voicein","camera",
              "write","translate","scanmath","prosearch","recognize","clip","box","voicewave",
              "recordvoice","microscope","scan"],
    "media": ["volon","voloff","phonecall","camera","voicein","voicewave","play","video",
              "recordvoice","soundgenerate","music","imagecreate","imagefailed","imageicon","imagegenerate"],
    "file": ["document","docdone","folder","folderopen","excel","download","save"],
    "status": ["loadingright","loadingdone","checkboxempty","checkboxin","completed","error",
               "pause","safe","warning","info","stop","normal","bad","smile","select",
               "allselected","multiselected"],
    "editor": ["text","image","download","magnify","minify","textselect","undo","redo","edit",
               "pencil","eraser","brush","font","color","stroke","textcolor","colorless"],
    "navigation": ["tabkimi","tabdiscover","tabme","browse","unbrowse","browser","internet",
                   "leftbar","rightbar","desktop","mobile","mobiledesktopadopt","list","history"],
    "social": ["like","dislike","share","message","redpacket","gift","group","joingroup","publishpost"],
    "system": ["setting","lightmode","darkmode","followsystem","management","profile","power",
               "battery","switch","connectors","diagnosis","skill","task","create","todo",
               "game","hand","icon","locate","memory","businesscard","pages","post",
               "business","artifact","union","pintotop","unpinfromtop","layer","deregister",
               "update","clearhistory","popupclosed","findasset","reduce","move","at","dot",
               "question","ban"],
    "general": [],
}

FORCED = {
    "Upload":"input","UploadFile":"input","UploadWechat":"input","Download":"file","Save":"file",
    "Box":"input","Clip":"input","ImageCreate":"input","Recognize":"input","Scan":"input",
    "ScanMath":"input","ProSearch":"input","Write":"input","Translate":"input","Microscope":"input",
    "Magnify":"image","Minify":"image","TextSelect":"editor","Undo":"editor","Redo":"editor",
    "Edit":"editor","Pencil":"editor","Eraser":"editor","Brush":"editor","Font":"editor",
    "Color":"image","Stroke":"image","TextColor":"image","Colorless":"image","Alpha":"image",
    "Cropping":"image","Replace":"image","CropRotation":"image","Watermark":"image",
    "FullScreen":"image","FitScreen":"image","FitScreen_b":"image","Document":"file",
    "Document_b":"file","DocDone":"file","Folder":"file","FolderOpen":"file","Excel":"file",
    "Browser":"navigation","Browser_b":"navigation","InternetOn":"navigation","InternetOff":"navigation",
    "InternetOff_b":"navigation","InternetOpen":"navigation","LeftBar":"navigation","RightBar":"navigation",
    "Desktop":"navigation","Mobile":"navigation","MobileDesktopAdopt":"navigation",
    "TabKimi":"navigation","TabDiscover":"navigation","TabMe":"navigation","Browse":"navigation",
    "Unbrowse":"navigation","List":"navigation","Catalog":"navigation","History":"navigation",
    "AddConversation":"chat","Comment":"chat","CommentAdd":"chat","PublishPost":"chat",
    "PhoneCall":"chat","VolOn":"chat","VolOff":"chat","Like":"social","Like_b":"social",
    "Dislike":"social","Dislike_b":"social","Share":"social","Share_b":"social","Message":"social",
    "RedPacket":"social","Gift":"social","Group":"social","JoinGroup":"social",
    "Link":"general","Pin":"general","Tag":"general","Info":"status","Warning":"status",
    "Error":"status","Completed":"status","Pause":"status","Stop":"status","Normal":"status",
    "Bad":"status","Smile":"status","CheckboxEmpty":"status","CheckboxIn":"status",
    "Select":"status","AllSelected":"status","MultiSelected":"status","LoadingRight":"status",
    "LoadingDone":"status","Setting":"system","Setting_line":"system","Management":"system",
    "Profile":"system","Power":"system","Battery":"system","Keyboard":"system","Switch":"system",
    "Connectors":"system","Diagnosis":"system","Skill":"system","Skill_b":"system","Task":"system",
    "TaskSubAgentOff":"system","Create":"system","Todo":"system","Game":"system","Hand":"system",
    "Icon":"system","Locate":"system","Memory":"system","BusinessCard":"system","Pages":"system",
    "Post":"system","Business":"system","Artifact":"system","Union":"system","PinToTop":"system",
    "UnpinFromTop":"system","Layer":"system","Deregister":"system","Update":"system",
    "ClearHistory":"system","PopupClosed":"system","FindAsset":"system","Reduce":"system",
    "Move":"system","At":"system","Dot":"system","Question":"system","Ban":"system",
    "MCP":"data","Knowledge":"data","Model":"data","Prism":"brand","Koder":"brand",
    "Robot":"brand","KimiPlus":"brand","KimiOld":"brand","Alphalab":"brand",
    "OKComputer":"brand","WebBridge":"brand","k15":"brand","k15_b":"brand","k15_c":"brand",
    "Apple":"brand","Android":"brand","Diagram":"data","Tabular":"data","Linechart":"data",
    "Histogram":"data","ViewAll":"data","Data":"data","Line":"formatting","Ordered":"formatting",
    "PageStyle":"formatting","WrapText":"formatting","WrapText_b":"formatting","Flatten":"formatting",
    "TopUp":"formatting","MoveUp":"formatting","MoveDown":"formatting","LineSpace":"formatting",
    "WordSpace":"formatting","IntervalSpace":"formatting","Cropping":"image","Replace":"image",
    "FullScreen":"image","FitScreen":"image","FitScreen_b":"image","CropRotation":"image",
    "TextColor":"image","Colorless":"image","Alpha":"image","Flip":"image","Flip_b":"image",
    "Stroke":"image","TabStroke":"image","TabStroke_b":"image","Shape":"image","Font":"editor",
    "TopAlign":"formatting","BottomAlign":"formatting","CenterVertically":"formatting",
    "LeftAlign":"formatting","CenterAlign":"formatting","RightAlign":"formatting","Justify":"formatting",
    "Bold":"formatting","Italic":"formatting","Underline":"formatting","StrikeThrough":"formatting",
    "Send_a":"chat","Send_b":"chat","SignIn":"general","SignOut":"general","Output":"general",
    "FoldLeft":"general","ExpandRight":"general","CirclePlus":"input","LightMode":"system",
    "DarkMode":"system","FollowSystem":"system","Left_c":"arrows","Right_c":"arrows","Up_c":"arrows",
    "GoBack":"arrows","GoBack_Number":"arrows","MoveForward":"arrows","Unfold":"arrows",
    "Enter":"arrows","Enter_r":"arrows","Previous":"arrows","Next":"arrows","Collapse":"arrows",
    "Expand":"arrows","Change":"arrows","Change_b":"arrows","Up":"arrows","Down":"arrows",
    "Left":"arrows","Right":"arrows","UpperLeft":"arrows","UpperRight":"arrows",
    "LowerLeft":"arrows","LowerRight":"arrows","LeftRight":"arrows","UpDown":"arrows",
    "Up_b":"arrows","Down_b":"arrows","Left_b":"arrows","Right_b":"arrows",
    "LeftRight_b":"arrows","UpDown_b":"arrows","Play":"media","Video":"media","Music":"media",
    "Sounds":"media","SoundGenerate":"media","RecordVoice":"media","VoiceWave":"media",
    "VoiceIn":"media","VolOn":"media","VolOff":"media","PhoneCall":"media",
    "ImageCreate":"media","ImageFailed":"media","ImageIcon":"media","ImageGenerate":"media",
    "DocDone":"file","Excel":"file","PPT":"file","PPT_b":"file","Tabular":"data",
}

CN_MAP = {
    "Add":["添加","新建","加号"],"AddConversation":["新建会话","新对话"],"AllSelected":["全选"],
    "Alpha":["透明度","透明"],"Alphalab":["Alphalab"],"Android":["安卓"],"Apple":["苹果"],
    "Artifact":["Artifact"],"At":["@","提及"],"Bad":["差评","不好"],"Ban":["禁止","屏蔽"],
    "Battery":["电池","电量"],"Bold":["粗体","加粗"],"Bookmark":["书签","收藏"],
    "Bottom":["底部","底对齐"],"BottomAlign":["底部对齐"],"Box":["盒子","工具箱"],
    "Browse":["浏览","探索"],"Browser":["浏览器"],"Brush":["画笔","刷子"],
    "Business":["商务","商业"],"BusinessCard":["名片"],"Camera":["相机","拍照"],
    "Catalog":["目录","分类"],"CenterAlign":["居中对齐"],"CenterVertically":["垂直居中"],
    "Change":["交换","切换","转换"],"Check":["勾选","对勾","确认"],
    "CheckboxEmpty":["空复选框","未勾选"],"CheckboxIn":["复选框选中","已勾选"],
    "CirclePlus":["圆形加号"],"ClearHistory":["清空历史","清除记录"],
    "Clip":["回形针","附件"],"Close":["关闭","叉号","删除"],"Code":["代码"],
    "Collapse":["收起","折叠"],"Collect":["收藏","收集"],"Color":["颜色","填充色"],
    "Colorless":["无颜色","去色"],"Comment":["评论","留言"],"CommentAdd":["添加评论"],
    "Completed":["完成","成功"],"Computer":["电脑","计算机"],"Connectors":["连接器","连接"],
    "Copy":["复制"],"Create":["创建"],"Cropping":["裁剪"],"CropRotation":["旋转裁剪"],
    "DarkMode":["深色模式","夜间模式"],"Data":["数据"],"Delete":["删除","移除","垃圾桶"],
    "Deregister":["注销","解绑"],"Desktop":["桌面端","电脑"],"Diagnosis":["诊断"],
    "Diagram":["图表","关系图"],"Dislike":["踩","不喜欢","差评"],"DocDone":["文档完成"],
    "Document":["文档"],"Dot":["圆点","点"],"Down":["向下","下降","下载"],
    "Download":["下载","导出"],"Edit":["编辑","修改"],"Enter":["回车","进入"],
    "Eraser":["橡皮擦"],"Error":["错误","失败"],"Excel":["Excel"],
    "Exclamation":["感叹号","提示"],"Expand":["展开","放大"],"ExpandRight":["向右展开"],
    "FindAsset":["查找资源"],"FitScreen":["适应屏幕","全屏适配"],"Flatten":["扁平化","合并图层"],
    "Flip":["翻转","镜像"],"Folder":["文件夹"],"FolderOpen":["打开文件夹"],
    "FoldLeft":["向左折叠"],"FollowSystem":["跟随系统"],"Font":["字体"],
    "FullScreen":["全屏"],"Game":["游戏"],"Gift":["礼物","红包"],
    "GoBack":["返回","后退"],"Group":["群组","分组"],"Hand":["手","手势"],
    "Histogram":["柱状图"],"History":["历史","记录"],"Icon":["图标"],
    "Image":["图片","图像"],"ImageCreate":["生成图片","AI生图"],
    "ImageFailed":["图片加载失败"],"ImageGenerate":["图片生成"],
    "ImageIcon":["图片图标"],"Info":["信息","提示"],"InternetOff":["网络断开"],
    "InternetOn":["网络连接"],"InternetOpen":["网络开放"],"Italic":["斜体"],
    "JoinGroup":["加入群组"],"Justify":["两端对齐"],"Keyboard":["键盘"],
    "KimiOld":["旧版Kimi"],"KimiPlus":["Kimi+"],
    "Knowledge":["知识库"],"Koder":["Koder"],"Layer":["图层"],
    "Left":["向左","左箭头"],"LeftAlign":["左对齐"],"LeftBar":["左侧面板"],
    "LightMode":["浅色模式","日间模式"],"Like":["赞","喜欢","好评"],
    "Line":["线条","直线"],"Linechart":["折线图"],"LineSpace":["行间距"],
    "Link":["链接","超链接"],"List":["列表"],"LoadingDone":["加载完成"],
    "LoadingRight":["加载中","转圈"],"Locate":["定位"],"LowerLeft":["左下箭头"],
    "LowerRight":["右下箭头"],"Magnify":["放大","放大镜"],"Management":["管理"],
    "MathFormula":["数学公式"],"MCP":["MCP"],"Memory":["记忆","历史记忆"],
    "Message":["消息","私信"],"Microscope":["显微镜"],"Minify":["缩小"],
    "Minus":["减号","删除"],"Mobile":["移动端","手机"],
    "MobileDesktopAdopt":["自适应","多端适配"],"Model":["模型"],
    "More":["更多","省略号"],"Move":["移动"],"MoveDown":["下移"],
    "MoveForward":["前进","下一步"],"MoveUp":["上移"],"MultiSelected":["多选"],
    "Music":["音乐"],"Next":["下一步","下一个"],"Normal":["一般","普通"],
    "Notification":["通知","消息提醒"],"OKComputer":["OK Computer"],
    "Ordered":["有序列表","编号列表"],"Output":["输出","导出"],
    "PageStyle":["页面样式"],"Pages":["页面"],"Pause":["暂停"],
    "Pencil":["铅笔"],"PhoneCall":["电话","语音通话"],"Pin":["置顶","固定"],
    "PinToTop":["置顶"],"Play":["播放"],"Plus":["加号","增加"],
    "PopupClosed":["弹窗关闭"],"Post":["发布","帖子"],"Power":["电源"],
    "PPT":["PPT"],"Previous":["上一步","上一个"],"Prism":["Prism"],
    "Profile":["个人资料","头像"],"ProSearch":["深度搜索","高级搜索"],
    "PublishPost":["发布帖子"],"Question":["问题","帮助"],
    "Recognize":["识别","OCR"],"RecordVoice":["录音"],
    "Redo":["重做","恢复"],"RedPacket":["红包"],"Reduce":["减少","压缩"],
    "Refresh":["刷新","重新加载"],"Replace":["替换"],"Review":["回顾","复习"],
    "Right":["向右","右箭头"],"RightAlign":["右对齐"],"RightBar":["右侧面板"],
    "Robot":["机器人"],"Safe":["安全","保险箱"],"Save":["保存"],
    "Scan":["扫描"],"ScanMath":["扫描数学"],"Search":["搜索","查找","查询"],
    "Select":["选择"],"Send_a":["发送"],"Send_b":["发送"],
    "Setting":["设置"],"Setting_line":["设置(线性)"],"Shape":["形状"],
    "Share":["分享"],"SignIn":["登录"],"SignOut":["退出","登出"],
    "Skill":["技能","Skill"],"Smile":["微笑","满意"],
    "SoundGenerate":["生成音频","AI音频"],"Sounds":["声音"],
    "Stop":["停止"],"StrikeThrough":["删除线"],"Stroke":["描边","边框"],
    "Style":["样式"],"Switch":["开关","切换"],"TabDiscover":["发现页"],
    "TabKimi":["Kimi页"],"TabMe":["我的页"],"TabStroke":["描边样式"],
    "Tabular":["表格"],"Tag":["标签"],"Task":["任务"],
    "TaskSubAgentOff":["子任务关闭"],"Text":["文本","文字"],
    "TextColor":["文字颜色"],"TextSelect":["文本选择"],"Todo":["待办","清单"],
    "TopAlign":["顶部对齐"],"TopUp":["向上置顶"],"Translate":["翻译"],
    "Underline":["下划线"],"Undo":["撤销"],"Unbrowse":["取消浏览"],
    "Unfold":["展开","打开"],"UnpinFromTop":["取消置顶"],
    "Update":["更新","升级"],"Upload":["上传"],"UploadFile":["上传文件"],
    "UploadWechat":["从微信上传"],"UpperLeft":["左上箭头"],"UpperRight":["右上箭头"],
    "Video":["视频"],"ViewAll":["查看全部"],"VoiceIn":["语音输入"],
    "VoiceWave":["声波","语音波形"],"VolOff":["静音"],"VolOn":["音量开"],
    "Warning":["警告","提醒"],"Watermark":["水印"],"WebBridge":["WebBridge"],
    "WordSpace":["字间距"],"WrapText":["换行","自动换行"],"Write":["写作","创作"],
}

def get_category(name):
    if name in FORCED:
        return FORCED[name]
    nm = name.lower()
    for cat, keys in KEYWORD_CAT.items():
        if cat == "general":
            continue
        for k in keys:
            if k in nm:
                return cat
    return "general"

def aliases(name):
    out = [name.lower()]
    base = re.sub(r'_[bcr]$', '', name)
    if base != name:
        out.append(base.lower())
    if name in CN_MAP:
        out.extend(CN_MAP[name])
    return list(dict.fromkeys(out))

RULES = {
    "Upload": (["file upload","asset import","upload from local device"],["download","export","cloud sync"]),
    "Download": (["file download","export to local device"],["upload","import","share"]),
    "Share": (["share content","share to external"],["export to file","copy link"]),
    "Search": (["search input","global search","table search"],["zoom","inspect","analytics"]),
    "Magnify": (["zoom in","enlarge image"],["search","find text"]),
    "Minify": (["zoom out","shrink image"],["search","compress file"]),
    "Edit": (["edit content","modify text"],["create new","write from scratch"]),
    "Write": (["write content","compose text"],["edit existing","annotate"]),
    "Like": (["thumbs up","approve","favorite"],["bookmark","star","collect"]),
    "Dislike": (["thumbs down","disapprove"],["delete","report","block"]),
    "Copy": (["duplicate","copy to clipboard"],["cut","move","clone"]),
    "Delete": (["delete item","remove","trash"],["clear history","deregister","archive"]),
    "ClearHistory": (["clear history","clear records"],["delete account","remove item"]),
    "Stop": (["stop process","halt generation"],["pause","cancel","close"]),
    "Pause": (["pause playback","pause process"],["stop","end","terminate"]),
    "Warning": (["alert","caution","needs attention"],["error","blocked","success"]),
    "Error": (["error state","failure","something went wrong"],["warning","caution","missing"]),
    "Info": (["information","help tip","details"],["warning","error","notification"]),
    "Setting": (["app settings","preferences","configuration"],["filter sliders","tune values","management"]),
    "Management": (["admin management","user management","system management"],["settings","personal preferences"]),
    "Add": (["add item","create new","insert"],["upload file","compose text","expand"]),
    "Close": (["close dialog","dismiss","remove tag"],["delete forever","logout","stop"]),
    "Check": (["confirm","selected","verified"],["radio button","favorite","bookmark"]),
    "CheckboxEmpty": (["multi-select","form checkbox"],["radio button","toggle switch"]),
    "CheckboxIn": (["multi-select","form checkbox"],["radio button","toggle switch"]),
    "Refresh": (["reload","refresh data","sync"],["undo","retry","rotate"]),
    "Link": (["hyperlink","attach URL","connect"],["share","export","attach file"]),
    "Comment": (["comment","reply","discussion"],["chat","message","note"]),
    "Message": (["direct message","chat","inbox"],["comment","notification","announcement"]),
    "Notification": (["notification bell","alerts","reminders"],["message","inbox","announcement"]),
    "Pin": (["pin to top","sticky","keep visible"],["bookmark","favorite","lock"]),
    "PinToTop": (["pin to top","sticky","keep visible"],["bookmark","favorite","lock"]),
    "Bookmark": (["bookmark","save for later"],["pin","favorite","collect"]),
    "Collect": (["collect","gather items"],["bookmark","favorite","save"]),
    "Send_a": (["send message","submit"],["share","forward","export"]),
    "Send_b": (["send message","submit"],["share","forward","export"]),
    "Undo": (["undo action","history step"],["reset","revert","reload"]),
    "Redo": (["redo action","history step"],["reset","revert","reload"]),
    "SignIn": (["login","authentication"],["register","delete account","switch user"]),
    "SignOut": (["logout","authentication"],["register","delete account","switch user"]),
    "LightMode": (["light theme","day mode"],["brightness","contrast"]),
    "DarkMode": (["dark theme","night mode"],["brightness","contrast"]),
    "FollowSystem": (["follow system theme","auto theme"],["brightness","contrast"]),
}

def get_rules(name):
    if name in RULES:
        return RULES[name]
    return ([],[])

files = sorted([f.stem for f in SVG_DIR.glob("*.svg")])
manifest = []
categories = {}

for name in files:
    cat = get_category(name)
    use_for, avoid_for = get_rules(name)
    entry = {
        "name": name + "Icon",
        "file": name + ".svg",
        "category": cat,
        "aliases": aliases(name),
        "use_for": use_for if use_for else [cat + " related action"],
        "avoid_for": avoid_for if avoid_for else ["unrelated context"],
        "color_mode": "currentColor",
        "default_size": 20,
    }
    manifest.append(entry)
    categories.setdefault(cat, []).append(entry)

# Write manifest
with open(OUT_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# Write categories
for cat, items in categories.items():
    with open(CAT_DIR / f"{cat}.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Generated manifest with {len(manifest)} icons in {len(categories)} categories.")
