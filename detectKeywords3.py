#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
__author__ = 'Erimus'

import codecs
import json
import re
from datetime import datetime


# ═══════════════════════════════════════════════


Punctuations = ('，。／《》？；：‘’“”【】「」『』、·～！¥￥…*（）—" "'
                '\t\n\r,./<>?;:\'\"[]{}\\|`~!@#$%^&*()-_=+｜'  # 符号
                '.0123456789abcdefghijklmnopqrstuvwxyz'
                'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # 英文数字
                '｀・≡дﾟ')  # 特殊符号


# 绘制标题
def drawTitle(string):
    width = (len(string) + len(string.encode('utf-8'))) // 2
    hr = '=' * (width + 8)
    print('\n%s\n>>> %s <<<\n%s' % (hr, string, hr))


# Print format JSON
def formatJSON(obj, indent=4):
    return json.dumps(obj, ensure_ascii=False, indent=indent)


# 读取文件并转为utf-8
def loadFile(filename):
    with codecs.open(filename, 'r', 'utf-8') as f:
        content = f.read()
    return content[:]


# ═══════════════════════════════════════════════


# 获取英文单词及出现次数 asciiDict{单词:出现次数,...}
def getAsciiDict(content):
    # 英文数字分词并统计
    asciiContent = re.findall(r'[\da-zA-Z\.]+', content)
    # print(asciiContent)
    asciiDict = {}
    # 常用字
    general = ['233', '666']
    for word in asciiContent:
        word = word.upper()
        for gw in general:  # 统一常用词
            if gw in word:
                word = gw  # 合并B站类似于233333333这种情况
        asciiDict[word] = asciiDict.get(word, 0) + 1

    [asciiDict.pop(i) for i in list(asciiDict)
     if len(i) == 1 or asciiDict[i] == 1]  # 排除仅出现一次或者单字母
    # print(formatJSON(asciiDict))

    return asciiDict


# 获取中文词组及出现次数
# wdDict{词组长度:{词组:出现次数,...},...}
def getChineseDict(content, maxLength=4):
    for i in Punctuations[1:]:
        content = content.replace(i, Punctuations[0])  # 把标点都换成第一个
    contentLength = len(content.replace(Punctuations[0], ''))  # 全文有效长度
    drawTitle('Total Chinese Characters : %s' % contentLength)
    sentenceList = content.split(Punctuations[0])  # 拆分内容为句子列表
    [sentenceList.remove('') for i in sentenceList if i == '']  # 移除空项
    # print('|'.join(content))

    # 拆分不同长度的词到列表
    # wdDict[词长][词] = 次数
    # wdDict{1:{'好':23,'的':20,...},2{},...}
    wdDict = {}
    for length in range(1, maxLength + 1):  # 为了检索合并词预留长度
        # print('length:%s'%length)
        wdDict[length] = {}  # 不同字长分组
        for sentence in sentenceList:
            if len(sentence) >= length:  # 句子 长于 目标字长分组
                for i in range(len(sentence) - length + 1):  # 取词起始位置
                    word = sentence[i:i + length]
                    wdDict[length][word] = wdDict[length].get(word, 0) + 1

    # for length in wdDict: #打印字典
    #   for word in wdDict[length]:
    #       if wdDict[length][word]>=5: #只打印部分
    #           print(str(wdDict[length][word]).rjust(5),word)

    return wdDict


# ═══════════════════════════════════════════════


# 检查词频
def combineWords(wdDict, timesLimit=1,
                 thresholdMin=0.5, thresholdMax=0.2, debug=False):
    for mainWdLen in range(2, max(wdDict) + 1):  # 从长度2的词组开始罗列主词
        # 按出现次数倒序
        mainWordList = sorted(wdDict[mainWdLen].items(),
                              key=lambda x: x[1], reverse=True)
        nbrDict = {}  # 邻词字典

        for word, wordTimes in mainWordList:  # 取出主词(词，次数)
            combine(word, wordTimes, timesLimit, wdDict, mainWdLen, nbrDict,
                    thresholdMin, thresholdMax, debug)

    # print(formatJSON(wdDict))
    return wdDict


def combine(word, wordTimes, timesLimit, wdDict, mainWdLen, nbrDict,
            thresholdMin, thresholdMax, debug):
    wordTimes = wdDict[len(word)][word]

    # 排除只出现X次的词(不然剩余的低于XX词的词 比如1次 百分百会合体成功通过)
    if wordTimes < timesLimit:
        # 合体失败的情况下，主词次数清零，因子次数保留。反之亦然。
        wdDict[len(word)][word] = 0
        return

    # print('====================\n主词:\t%s\t%s'%(word,wordTimes))
    combineSuccess = 0
    # 把主词切分为AB两个因子
    for A_end in range(1, len(word))[::-1]:  # 取得包含的A词的词长 从长的开始取 避免优先取到短因子
        A_word = word[:A_end]  # 取出包含的A词
        for B_start in range(1, A_end + 1):
            B_word = word[B_start:]  # 取出包含的B词 从长的开始取

            A_times = wdDict[len(A_word)][A_word]  # A词出现次数
            B_times = wdDict[len(B_word)][B_word]  # B词出现次数
            if debug:
                print('  %s=%s,%s=%s,%s=%s' % (word, wordTimes,  # 打印主词
                                               A_word, A_times,  # 因子
                                               B_word, B_times))

            # 判断合词成功
            # 主词出现次数>min因子出现次数*阈值 = 主词占据该因子的比例很大
            # (主词很可能是个词组 e.g.域名=20,域=18,名=15)
            # 主词出现次数<min因子出现次数 = 该因子已被其他词占用
            # 主词出现次数>max因子出现次数*阈值 = 防止频度极高的常用词成为词组
            # (e.g.域名的=15,域名=20,的=200)
            if (min(A_times, B_times) * thresholdMin <= wordTimes
                    and wordTimes <= min(A_times, B_times)
                    and max(A_times, B_times) * thresholdMax <= wordTimes):
                # 去除邻词。
                remove_neighbor(mainWdLen, wdDict, word, nbrDict, debug)

                # 退还重叠部分的词的次数
                if A_end > B_start:
                    repeat = word[B_start:A_end]
                    if debug:
                        print('repeat: %s / %s (%s->%s)' %
                              (repeat, word, wdDict[len(repeat)][repeat],
                               wdDict[len(repeat)][repeat] + wordTimes))
                    wdDict[len(repeat)][repeat] += wordTimes

                # 主词次数保留 因子次数减去
                wdDict[len(A_word)][A_word] -= wordTimes
                wdDict[len(B_word)][B_word] -= wordTimes

                if debug:
                    print('==合体成功: %s=%s, %s=(%s->%s), %s=(%s->%s)\n' %
                          (word, wordTimes,
                           A_word, A_times, wdDict[len(A_word)][A_word],
                           B_word, B_times, wdDict[len(B_word)][B_word]))

                combineSuccess = 1
                break  # 合体成功一次即完结 退出B词循环

        if combineSuccess:
            break  # 退出A词循环

    if combineSuccess == 0:  # 所有因子组合都凝聚失败
        if debug:
            print('# 合体失败: %s\n' % word)
        wdDict[len(word)][word] = 0  # 合体失败的情况下，主词次数清零，因子次数保留。反之亦然。


# 去除邻词。
# 比如'德云'34次，那找出所有3个字含德云的，比如'德云社'33次，那么'云社'就-33次。
# 如果不去除，重复的部分'云'就会别重复扣除，那么其它含'云'的词组就会合体失败。
# 但去除的时候又要防止多次重复去除。
# 比如'ABCD'，'AB'聚合扣一次'BC'，'CD'聚合又扣一次'BC'，参考范例的'侯变'。
# 上级词确保至少有1字重叠
def remove_neighbor(mainWdLen, wdDict, word, nbrDict, debug):
    for higherLength in range(mainWdLen + 1, mainWdLen * 2):
        for higherWd in wdDict.get(higherLength, {}):
            # 获得当前上级词长两端的词，避免重复减去。
            # 比如'XXX'，整句'abXXXcd',4字仅处理['bXXX','XXXc']
            # word开头或结尾
            if word in [higherWd[:mainWdLen],
                        higherWd[-mainWdLen:]]:
                # 获取相邻词 仅替换一次
                nbr = ((higherWd[:mainWdLen]
                        + higherWd[-mainWdLen:])
                       .replace(word, '', 1))
                N_Times = wdDict[len(nbr)][nbr]  # 邻词原次数
                removed = nbrDict.get(nbr, 0)  # 已被移除过的次数
                # 更新邻词字典
                nbrDict[nbr] = max(wdDict[len(higherWd)][higherWd], removed)
                # 不出现负数
                wdDict[len(nbr)][nbr] -= (min(nbrDict[nbr] - removed,
                                              wdDict[len(nbr)][nbr]))
                if debug:
                    print('# %s=%s->%s,上级:%s=%s' %
                          (nbr, N_Times, wdDict[len(nbr)][nbr],
                           higherWd, wdDict[len(higherWd)][higherWd]))


# ═══════════════════════════════════════════════


# 排序并打印结果
def printResult(asciiDict, wdDict, wordLenMin=2, timesLimit=1,
                topLimit=999, doPrint=True, letter=True, digit=True):
    # drawTitle('RESULT')
    result = [i for i in asciiDict.items() if i[1] >= timesLimit]
    result = [list(x) for x in result]  # 取出英数
    if not letter:
        result = []
    if not digit:
        result = [i for i in result if not i[0].replace('.', '').isdigit()]

    for length in range(wordLenMin, max(wdDict) + 1)[::-1]:  # 优先长词组
        temp = [i for i in wdDict[length].items() if i[1] >= timesLimit]
        result += sorted([list(x) for x in temp],
                         key=lambda x: x[1], reverse=True)  # 正常统计
        # result += sorted([(i, j * length) for (i, j) in wdDict[length].items()],
        #                  key=lambda x: x[1], reverse=True)  # 字数加成
    result = sorted(result, key=lambda x: x[1], reverse=True)

    if doPrint:
        # drawTitle('Keywords Ranking')
        for i in result[:topLimit]:  # 打印前XX位
            print('%5s %s' % (i[1], i[0]))

    return result[:topLimit]


# ═══════════════════════════════════════════════


# 检查结果
def checkResult(wdDict, content):
    # print(formatJSON(wdDict))
    chineseLength = 0
    for length in range(1, max(wdDict) + 1)[::-1]:  # 优先长词组
        # 用移去的方法似乎无法保证顺序 检测不正确
        # 直接统计中文字数量
        for times in wdDict[length].values():
            chineseLength += length * times

    for i in Punctuations:
        content = content.replace(i, '')  # 原文去英数标点后的字符数量

    if len(content) != chineseLength:
        drawTitle('Result ERROR!')
        print('content: %s\twordDict: %s' % (len(content), chineseLength))


# ═══════════════════════════════════════════════


# 主入口
def detectKeywords(content, timesLimit=10, wordLenMin=2, wordLenMax=5,
                   thresholdMin=0.4, thresholdMax=0.2, topLimit=999,
                   doPrint=True, letter=True, digit=True, debug=False):
    asciiDict = getAsciiDict(content)
    wdDict = getChineseDict(content, wordLenMax)

    # test data
    # asciiDict = {}
    # wdDict = {1:{'互':17,'联':21,'网':22,'域':20,'名':21},2:{'互联':16,'联网':16,'网域':6,'域名':19},3:{'互联网':16,'联网域':6,'网域名':6},4:{'互联网域':6,'联网域名':6},5:{'互联网域名':6}}
    # wdDict = {1:{'美':20,'国':40,'政':18,'府':17},2:{'美国':20,'国政':8,'政府':17},3:{'美国政':7,'国政府':8},4:{'美国政府':7}}
    # wdDict = {1:{'气':12,'侯':10,'变':19,'化':11},2:{'气侯':6,'侯变':5,'变化':6},3:{'气侯变':5,'侯变化':5},4:{'气侯变化':5}}

    # (只处理>=X次出现的词),(越小越容易选到非词组),(越大越容易选到常用字)
    wdDict = combineWords(wdDict, timesLimit,
                          thresholdMin, thresholdMax, debug)
    checkResult(wdDict, content)
    keywordsList = printResult(asciiDict, wdDict, wordLenMin,
                               timesLimit, topLimit, doPrint,
                               letter=letter, digit=digit)  # 最小出现次数
    return keywordsList


# ═══════════════════════════════════════════════


if __name__ == '__main__':
    startTime = datetime.now()

    filename = 'test/text1.txt'
    content = loadFile(filename)

    debug = 0
    # debug = 1
    timesLimit = 5  # 最小出现次数
    wordLenMin = 2  # 最短词长度
    wordLenMax = 5  # 最长词长度
    thresholdMin = 0.6  # 主词占因子比例，越小越容易选到非词组。(e.g.互=17,联=21,互联=16)
    thresholdMax = 0.1  # 越大越容易选到常用字。(e.g.域名的=15,域名=20,的=200)
    topLimit = 5000  # 输出结果长度
    doPrint = True  # 是否打印结果
    detectKeywords(content, timesLimit, wordLenMin, wordLenMax,
                   thresholdMin, thresholdMax, topLimit, doPrint, debug)

    print('---\nUsed: %s' % (datetime.now() - startTime))
