#todolist 代理池和代理ip扩充；ip_check中的代理模块用封装更好的模块import实现；多线程threadpool；class化；db输出。
# v0.2 增加get_page_try函数。格式化字符串；增加url_list;完善文件路径；增加req.headers；发现ping通地址并不稳定，增加尝试次数。保留一些循环range(len())可读性。
# v0.1 加入了ip_check函数，响应时间5秒，初次筛选放宽。修改问题：端口re匹配，切块slice中的find匹配不严谨。
import os
import urllib.request
import re
import time
import pickle


def get_page_try(url):
    html = 0
    try:
        req_head = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                    'Host':'www.xicidaili.com',
                    'Connection': 'keep-alive',
                    'DNT': '1'}
        #req_head['Referer'] = 'http://www.xicidaili.com/nn/' #总出错时试试
        #req_head['Cookie'] = ''
        req = urllib.request.Request(url,headers=req_head)
        response = urllib.request.urlopen(req,timeout=5)
        html = response.read()
    except Exception as e:
        print(e)
        print('%s地址访问失败！' % url)
        time.sleep(2)
    return html

def get_page(url):
    html = get_page_try(url)
    i = 0
    while (i < 2 and html == 0): #尝试访问三次
        html = get_page_try(url)
        i += 1
    if html == 0 : #增加访问页面失败退出执行
        raise SystemExit
    return html

def get_iplist_slice(url):  # 根据http://www.xicidaili.com/网站格式，对网页分割为多个包含代理ip信息的块
    html = get_page(url).decode('utf-8')
    # print(html)
    start = 0
    end = 0
    iplist_slice = []
    while html.find('<tr class="', end) != -1:
        start = html.find('<tr class="', end)
        end = html.find('/tr>', start)
        iplist_slice.append(html[start:end + 4])  # 源代码不加><两括号时竟然从里面一个/tr.png处截断了，还是要严谨！
    return iplist_slice


def get_iplist(iplist_slice):
    iplist = []
    for i in range(len(iplist_slice)):  # 筛选获得ip，端口，协议格式，连接速度，持续时间信息
        ip = re.search(r'<td>((?:(?:[01]?\d?\d|2[0-4]\d|25[0-5]).){3}(?:[01]?\d?\d|2[0-4]\d|25[0-5]))</td>',
                       iplist_slice[i])
        port = re.search(r'<td>([0-9]{1,5})</td>', iplist_slice[i])  # 有的端口尽然是手滑五位数，无语
        protocol = re.search(r'<td>([HTPS]{4,5})</td>', iplist_slice[i])
        speed = re.search(r'(\d{1,2}\.\d{0,3})秒', iplist_slice[i])
        lasting_time = re.search(r'(\d{1,2}分钟|\d{1,2}小时|\d{1,4}天)', iplist_slice[i])
        # print(i)
        lasting_day = lasting_time.group()
        # print(iplist_slice[i])
        if (float(speed.group(1)) < 2) and (lasting_day.find('天') != -1):  # 筛选连接速度小于2秒，存在时间大于等于1天的代理ip
            ip_dict = {'ip': ip.group(1) + ':' + port.group(1), 'protocol': protocol.group(1).lower(),
                       'speed': speed.group(1) + '秒', '持续时间': lasting_day}
            iplist.append(ip_dict)
    for i in iplist:
        print(i)
    return iplist


def save_iplist(iplist,url,save_ip_dir):# 保存为pickle文件
    if iplist != []:
        filename = 'iplist_%s_%s.pkl' % (time.strftime("%Y%m%d", time.localtime()),url.split('/')[-2])   # 修改代理ip保存pkl文件名称,原格式以日期保存
        with open(filename, 'wb') as iplist_pickle:
            pickle.dump(iplist, iplist_pickle)
            print('\n检测后保存%s个代理ip完毕\n于%s文件夹中，为pickle文件。' % (len(iplist),save_ip_dir))
            print('pickle.load()打开open("文件名","rb")，即可获得列表文件使用，元素为ip字典，包含key：ip，protocol,speed,持续时间。')
            print('例：iplist[0]有\n%s' % iplist[0])
    else :
        print('未找到合适的代理！')


def ip_check(iplist):  # 通过一次连接判断代理是否可用
    iplist_new = []
    for i in range(len(iplist)):
        proxy_ip = iplist[i]['ip']
        proxy_protocol = iplist[i]['protocol']
        print(proxy_ip)

        proxy_support = urllib.request.ProxyHandler({proxy_protocol: proxy_ip})
        opener = urllib.request.build_opener(proxy_support)
        headers = ('User-Agent',
                   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0')
        opener.addheaders = [headers]
        urllib.request.install_opener(opener)

        req = urllib.request.Request('http://1212.ip138.com/ic.asp')  # ip地址查询网站
        #req.add_header('User-Agent',
        #               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:24.0) Gecko/20100101 Firefox/24.0')
        try:
            response = urllib.request.urlopen(req, timeout=5)  # 5秒响应时间
            html = response.read().decode('gb2312')
            html = re.search(r'<center>(.+?)</center>', html)  # 根据ip138网页，只输出核心内容部分（原因：有时输出网页后缀包含utf-8格式等大量无关内容）
            print(html.group(1))
        except Exception as e:
            print(e)
            #try: # 给个机会 再试一次
            #    time.sleep(1)
            #    response = urllib.request.urlopen(req, timeout=5)
            #    html = response.read().decode('gb2312')
            #    html = re.search(r'<center>(.+?)</center>', html)
            #    print(html.group(1))
            #except Exception as e:
            #    print(e)
            #else:
            #    iplist_new.append(iplist[i])
        else:
            iplist_new.append(iplist[i])
        time.sleep(1)
    return iplist_new


def ip_get_main():
    save_ip_dir = r'C:\Users\get_ip_proxy'  # 默认输出保存路径
    temp_dir = input(r'输入输出保存路径(Enter默认C:\Users\get_ip_proxy)：')
    if (temp_dir != ''):
        save_ip_dir = temp_dir
    try:
        os.chdir(save_ip_dir)
    except FileNotFoundError:
        print('找不到该路径，请修改save_ip_dir值为已存在文件保存路径再运行。')
        raise SystemExit

    folder = 'ip_proxy'  # 用于建立代理ip保存文件夹
    try:
        os.chdir(folder)
    except FileNotFoundError:
        os.mkdir(folder)
        print('已在%s下创建%s文件夹用于保存输出文件' % (save_ip_dir, folder))
        os.chdir(folder)

    url_list = ['http://www.xicidaili.com/nn/','http://www.xicidaili.com/wn/'] #提供代理的网站
    for each_url in url_list:
        iplist_slice = get_iplist_slice(each_url)
        # for i in iplist_slice:
        #   print(i)

        iplist = get_iplist(iplist_slice)
        print('\n找到并筛选出%s个代理ip。' % len(iplist))
        iplist = ip_check(iplist)
        save_iplist(iplist,each_url,save_ip_dir)


if __name__ == '__main__':
    ip_get_main()
