#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'Erimus'


import re
import math

'''
读取文件并转为utf-8
'''
def loadFile(filename):
	# 获取文本内容 并转换成列表
	file = open(filename,'r')
	content = file.read().decode('utf-8')
	file.close()
	return content


'''
获取英文单词及出现次数
asciiDict{单词:出现次数,...}
'''
def getAsciiDict(content):
	# 英文数字分词并统计
	asciiContent = re.findall(u'[\da-zA-Z\.]+',content)
	# print asciiContent
	asciiDict = {}
	for i in asciiContent:
		i = i.upper()
		asciiDict[i] = asciiDict.get(i,0)+1
	# print asciiDict
	for i in asciiDict.keys(): #加keys 不然过程中dict在变
		if len(i)==1 or asciiDict[i]<appearTimeLimit:
			asciiDict.pop(i)
		# else:
		# 	print i,asciiDict[i]
	return asciiDict


'''
获取中文词组及出现次数
contentDict{词组长度:{词组:出现次数,...},
			...}
'''
def getChineseDict(content,maxLength=4):
	# 移除标点符号
	Punctuations = u'，。／《》？；：‘’“”【】「」、·～！¥…*（）—" "\t\n\r,./<>?;:\'\"[]{}\\|`~!^*()-_=+' #符号
	Punctuations += u'.0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' #英文数字
	for i in Punctuations[1:]:
		content = content.replace(i,Punctuations[0]) #把后续标点符号都换成第一个
	contentLength = float(len(content.replace(Punctuations[0],''))) #全文有效长度
	print drawTitle('TOTAL CHARACTERS : %s'%int(contentLength))
	content = content.split(Punctuations[0]) #拆分内容到列表
	while '' in content:
		content.remove('')
	# print '|'.join(content)

	'''
	拆分不同长度的词到列表
	contentDict[词长][词] = 次数
	'''
	contentDict = {}
	for wordLength in range(1,maxLength*2): #为了检索合并词预留长度
		# print 'wordLength:%s'%wordLength
		contentDict[wordLength] = {} #不同字长分组
		for words in content:
			if len(words)>= wordLength: #去标点后的分词 长于 目标字长分组
				for i in range(len(words)-wordLength+1): #取词起始位置
					word = words[i:i+wordLength]
					if word in contentDict[wordLength]:
						contentDict[wordLength][word] += 1
					else:
						contentDict[wordLength][word] = 1

	# for length in contentDict: #打印字典
	# 	for word in contentDict[length]:
	# 		if contentDict[length][word]>4: #只打印部分
	# 			print word,str(contentDict[length][word]).rjust(5)

	return contentDict


'''
检查词频
'''
def combineWords(contentDict,tolerance=0.5):
	contentDictCopy = {}
	for key in contentDict:
		contentDictCopy[key] = contentDict[key].copy()

	for longWordLength in range(2,maxLength+1): #从长度2的词组开始罗列主词
		# print 'longWordLength:%s\tshortWordLength:%s'%(longWordLength,shortWordLength)
		mainWordList = sorted(contentDictCopy[longWordLength].items(),key=lambda x:x[1],reverse=True) #按出现次数倒序
		# print mainWordList
		for mainWord in mainWordList: #取出主词(词，次数)
			word = mainWord[0]
			wordTimes = contentDictCopy[len(word)][word] #动态更新词出现的次数		

			if wordTimes<=1:
				contentDictCopy[len(word)].pop(word)
				continue #排除只出现一次的词 * 被手动排除的词

			# print u'====================\n主词:\t%s\t%s'%(word,wordTimes)

			hasCommon = False
			for commonWord in commonList:
				if word.find(commonWord)==0 or word.find(commonWord)==len(word)-1:
					hasCommon = True
			if hasCommon:
				contentDictCopy[len(word)].pop(word)
				# print u'合体失败 - 头尾含常用词'
				continue

			combineSuccess = 0
			for shortWordLength in range(1,longWordLength): #取得包含的词的词长
				A_word = word[:shortWordLength] #取出包含的A词
				B_word = word[shortWordLength:] #取出包含的B词
				if A_word not in contentDictCopy[len(A_word)] or B_word not in contentDictCopy[len(B_word)]:
					continue
				A_times = contentDictCopy[len(A_word)].get(A_word,0) #A词出现次数
				B_times = contentDictCopy[len(B_word)].get(B_word,0) #B词出现次数

				# print '= %s=%s,%s=%s,%s=%s'%(mainWord[0],wordTimes,A_word,A_times,B_word,B_times)

				# 主词出现次数>因子出现次数*阈值=主词占据该因子的比例很大(主词很可能是个词组)
				if min(A_times,B_times)*tolerance < wordTimes:
					contentDictCopy[len(A_word)][A_word] -= wordTimes
					contentDictCopy[len(B_word)][B_word] -= wordTimes
					# print '> %s=%s,%s=%s,%s=%s'%(word,wordTimes,A_word,contentDictCopy[len(A_word)][A_word],B_word,contentDictCopy[len(B_word)][B_word])
					# print '# %s=%s,%s=%s,%s=%s'%(word,wordTimes,A_word,contentDict[len(A_word)][A_word],B_word,contentDict[len(B_word)][B_word])

					# 排除连续情况 e.g.'的推荐算法'找到了'推荐'，要排除'的推'和'荐算'
					# print u'跟踪词在排除后:%s'%(contentDictCopy[3][u'丰臣秀'])
					combineSuccess += 1

			if combineSuccess==0:
				# print u'合体失败'
				contentDictCopy[len(word)].pop(word)
			else:
				# print u'合体成功:%s'%combineSuccess
				contentDictCopy = excludeWords(word,contentDictCopy)

		contentDictCopy = caculateWordsTimes(contentDict,contentDictCopy,longWordLength)
		# printResult({},contentDictCopy)
		# print u'打印Copy:%s,当前词长%s'%(contentDictCopy[1][u'网'],longWordLength)
	contentDictCopy = excludeCommonWord(contentDictCopy)
	return contentDictCopy


'''
获得一个长度组的有效词组之后
重新计算下级词组的使用频次
防止重复扣除次数
'''
def caculateWordsTimes(contentDict,contentDictCopy,lengthLimit):
	# print u'跟踪词在times开始:%s'%(contentDictCopy[3][u'丰臣秀'])
	longWordList = set([i for (i,j) in contentDictCopy[lengthLimit].items() if j>1])
	# print '|'.join(longWordList)
	recoveredWord=set()
	for lengthNow in range(1,lengthLimit)[::-1]: #待处理的词长 从当前级的低一级到1级 降序
		# print 'lengthNow:%s'%lengthNow
		shortWordList = set()
		for longWord in longWordList: #抽出词语
			# print 'longWord:%s'%longWord
			longWordTimes = contentDictCopy[len(longWord)].get(longWord,0)
			shortWord1,shortWord2 = longWord[:-1],longWord[1:]
			# print shortWord1,shortWord2,lengthNow
			shortWordList.add(shortWord1)
			shortWordList.add(shortWord2)
			# print 'longWord:%s=%s'%(longWord,longWordTimes)
			if longWordTimes>0:
				# contentDictCopy = caculateWordsTimesToSingle(contentDict,contentDictCopy,longWord,longWordTimes)
				for length in range(1,len(longWord))[::-1]: #因子的长度
					for start in range(len(longWord)-length+1):
						word = longWord[start:start+length]
						# print u'%s=%s,word:%s=%s-%s'%(longWord,longWordTimes,word,contentDictCopy[length].get(word),longWordTimes)
						if word in contentDict[length]:
							if word not in recoveredWord:
								recoveredWord.add(word)
								contentDictCopy[length][word] = contentDict[length][word] #原始数据代入
								# print u'原始数据写入:%s=%s'%(word,contentDictCopy[length][word])
							contentDictCopy[length][word] -= longWordTimes
							# print '# %s -> %s'%(contentDictCopy[length][word]+longWordTimes,contentDictCopy[length][word])

				# print u'跟踪词在single:%s'%(contentDictCopy[3][u'丰臣秀'])

		# print '|'.join(list(shortWordList))
		longWordList = shortWordList
	# print u'跟踪词在times结束:%s'%(contentDictCopy[3][u'丰臣秀'])
	return contentDictCopy


'''
去除有效词组前后相连的非重要词
'''
def excludeWords(word,contentDict):
	for length in range(len(word)+1,len(word)*2):
		for searchWord in contentDict[length].keys(): #设定范围
			wordStart = searchWord.find(word)
			# print 'wordStart:%s'%wordStart
			if wordStart>=0:
				# print 'form:%s - %s'%(searchWord,word)
				# print 'searchin:%s,start:%s'%(searchWord,wordStart)
				for start in range(wordStart-len(word)+1,wordStart+len(word)):
					if start>=0 and start+len(word)<=len(searchWord) and start!=wordStart:
						excludeWord = searchWord[start:start+len(word)] #要排除的词
						excludeWordTimes = contentDict[len(excludeWord)].get(excludeWord,0) #要排除的词出现次数
						if start<wordStart:
							combineWord = searchWord[start:wordStart+len(word)] #找出合词 o.g.的美国
						else:
							combineWord = searchWord[wordStart:start+len(word)] #找出合词 o.g.美国的
						if len(combineWord)<=max(contentDict.keys()): #合词长度在字典
							combineWordTimes = contentDict[len(combineWord)].get(combineWord,0)  #找出合词出现次数
							# print u'排除:%s,%s=%s;%s=%s'%(searchWord,combineWord,combineWordTimes,excludeWord,excludeWordTimes)
							if contentDict[len(excludeWord)].get(excludeWord,0)>0:
								# contentDict[len(excludeWord)][excludeWord] -= min(excludeWordTimes,combineWordTimes)
								contentDict[len(excludeWord)][excludeWord] = 0
								# print u'# %s\t%s -> %s'%(excludeWord,excludeWordTimes,contentDict[len(excludeWord)][excludeWord])
	return contentDict


'''
排除常用字为头尾的词
比如 的XX XX的 是XX XX是
'''
def excludeCommonWord(contentDictCopy):
	for length in range(2,maxLength+1):
		for word in contentDictCopy[length]:
			if contentDictCopy[length][word]>2: #过滤几乎被淘汰的词
				for commonWord in commonList:
					if word.find(commonWord)==0 or word.find(commonWord)==length-1:
						newWord = word.replace(commonWord,'')
						# print 'word=%s=%s,newWord=%s=%s'%(word,contentDictCopy[length][word],newWord,contentDictCopy[len(newWord)][newWord])
						contentDictCopy[len(newWord)][newWord] += contentDictCopy[length][word]
						contentDictCopy[length].pop(word)

	return contentDictCopy


'''
打印结果
'''
def printResult(asciiDict,contentDict):
	# print drawTitle('RESULT')
	result = sorted(asciiDict.items())
	for length in range(2,maxLength+1)[::-1]:
		result += sorted([(i,j) for (i,j) in contentDict[length].items() if j>=appearTimeLimit],key=lambda x:x[1],reverse=True) #正常统计
		# result += sorted([(i,j*length) for (i,j) in contentDict[length].items()],key=lambda x:x[1],reverse=True) #字数加成
	result = sorted(result,key=lambda x:x[1],reverse=True)

	for i in result[:]:
		print i[0],i[1]


'''
绘制标题
'''
def drawTitle(string):
	return '\n┌'+'─'*(len(string)+2)+'┐\n│ '+string+' │\n└'+'─'*(len(string)+2)+'┘'

'''
主入口
'''

filename = 'test/text1.txt'
maxLength = 5
appearTimeLimit = 5
commonList = [i for i in u'是的一些'] #常用字(避免这些字开头或结尾)
content = loadFile(filename)
asciiDict = getAsciiDict(content)
baseContentDict = getChineseDict(content,maxLength) #最长词长度
newContentDict = combineWords(baseContentDict,0.5) #宽容度 范围0-1 数字越大代表
printResult(asciiDict,newContentDict)