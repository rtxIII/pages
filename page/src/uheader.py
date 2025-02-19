import os
import logging
import datetime
from os.path import join, getsize
from aip.nlp import AipNlp
from aip.base import BAIDU_NLP_SECRET_KEY, BAIDU_NLP_APP_ID, BAIDU_NLP_APP_KEY
logger = logging.getLogger(__name__)

CONTENT_LOCATION = './content/post'

a = AipNlp(appId=BAIDU_NLP_APP_ID, apiKey=BAIDU_NLP_APP_KEY, secretKey=BAIDU_NLP_SECRET_KEY)

def get_jiagu():
    import jiagu
    jiagu.init()
    return jiagu


def jiagu_pos(jiagu, words):
    ret = {
           'location': [],
           'people': [],
           'org': [],
           'other': []
           }
    _cut = jiagu.seg(words)
    _result = jiagu.pos(_cut)
    for i,each in  enumerate(_result):
        if each in ['ns', 'nn']:
            '''
            ns　 　地名
            nn 　　族名
            '''
            ret['location'].append(_cut[i])
        if each in ['nh','nhf','nhs']:
            '''
            nh　 　人名
            nhf　　姓
            nhs　　名
            '''
            ret['people'].append(_cut[i])
        if each in ['ni','nz']:
            '''
            ni 　　机构名
            nz 　　其他专名
            '''
            ret['org'].append(_cut[i])
        if each in ['n','nt','nd','nl']:
            '''
            n　　　普通名词
            nt　 　时间名词
            nd　 　方位名词
            nl　 　处所名词
            '''
            ret['other'].append(_cut[i])
    return ret

def today_now(date_format='%Y-%m-%d'):
    return datetime.datetime.now().strftime(date_format)

def generate_header(title, category, tags, term, description:str, date:str=today_now()):
    return "+++\ndate = \"" + date + "\"\ntitle = \""  \
        + title + "\"\ndescription = \"" + description + "\"" \
        + "\ntags = [\"" + tags + "\"]" \
        + "\nterm = [\"" + term + "\"]" \
        + "\ncategories = [\"" + category + "\"]\n+++"

def get_meta(title, content, max_summary_len=100):
    j = get_jiagu()
    #print(content)
    summary = a.newsSummary( content, max_summary_len).get('summary', '')
    categories = []
    topic_item = a.topic(title, content, options=None).get('item', {})
    for k,v in topic_item.items():  # type: ignore 
        if v:
            for each in v:
                t = each.get('tag')
                if t:
                    categories.append(t)

    keyword_items = a.keyword(title, content, options=None).get('items', [])
    tags = []
    for each in keyword_items:
        tags.append(each.get('tag'))  # type: ignore 
    terms_items = jiagu_pos(j, content)
    terms = []
    terms_location = terms_items['location']
    terms.extend(terms_location)
    terms_people = terms_items['people']
    terms.extend(terms_people)
    terms_org = terms_items['org']
    terms.extend(terms_org)
    terms_other = terms_items['other']
    return {
       'categories': ','.join(categories),
       'terms': ','.join(terms),
       'summary': summary.replace('\"', '\''),
       'tags': ','.join(tags)
    }

def update_file_header(file, header):
    with open(join(CONTENT_LOCATION, file), "r+", encoding='UTF-8') as f:
        # 读取文件内容
        content = f.read()
        # 替换内容
        content = header + "\n\n" + content
        # 将指针移动到文件开头
        f.seek(0)
        # 清空文件
        f.truncate()
        # 将修改后的内容写入文件
        f.write(content)
        # 关闭文件
        f.close()
    print(file + " updated")

def check_markdown():
    for root, dirs, files in os.walk(CONTENT_LOCATION):
        print("Checking....", root, end="\n")
        for file in files:
            if file.endswith('.md'):
                print(file, "checking....\n", end="")
                with open(join(root, file), 'r') as f:
                    content = f.read()
                    title = file.strip('.md').strip('.markdown')
                    if content.startswith('+++\n'):
                        print(title + " is valid")
                    else:
                        print(title + " is invalid")
                        _meta  = get_meta(title, content)
                        header = generate_header(title, _meta['categories'], _meta['tags'], _meta['terms'], _meta['summary'])
                        print(header)
                        update_file_header(file, header)


if __name__ == '__main__':
    check_markdown()
