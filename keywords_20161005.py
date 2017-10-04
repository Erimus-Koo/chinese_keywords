#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'Erimus'


import re
import math



"""
绘制标题
"""
def drawTitle(string):
	print '\n┌'+'─'*(len(string)+2)+'┐\n│ '+string+' │\n└'+'─'*(len(string)+2)+'┘'



"""
读取文件并转为utf-8
"""
def loadFile(filename):
	# 获取文本内容 并转换成列表
	file = open(filename,'r')
	content = file.read().decode('utf-8')
	file.close()
	return content



"""
获取英文单词及出现次数
asciiDict{单词:出现次数,...}
"""
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
		if len(i)==1 or asciiDict[i]==1:
			asciiDict.pop(i)
		# else:
		# 	print i,asciiDict[i]
	return asciiDict



"""
获取中文词组及出现次数
contentDict{词组长度:{词组:出现次数,...},
			...}
"""
def getChineseDict(content,maxLength=4):
	# 移除标点符号
	Punctuations = u'，。／《》？；：‘’“”【】「」、·～！¥…*（）—" "\t\n\r,./<>?;:\'\"[]{}\\|`~!^*()-_=+' #符号
	Punctuations += u'.0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' #英文数字
	for i in Punctuations[1:]:
		content = content.replace(i,Punctuations[0]) #把后续标点符号都换成第一个
	contentLength = float(len(content.replace(Punctuations[0],''))) #全文有效长度
	drawTitle('TOTAL CHARACTERS : %s'%int(contentLength))
	content = content.split(Punctuations[0]) #拆分内容到列表
	while '' in content: #移除连续符号或英数造成的空项
		content.remove('')
	# print '|'.join(content)

	"""
	拆分不同长度的词到列表
	contentDict[词长][词] = 次数
	contentDict{1:{'好':23,'的':20,...},2{},...}
	"""
	contentDict = {}
	for wordLength in range(1,maxLength+1): #为了检索合并词预留长度
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
	# 		if contentDict[length][word]>=5: #只打印部分
	# 			print word,str(contentDict[length][word]).rjust(5)

	return content,contentDict



"""
检查词频
"""
def combineWords(content,contentDict,timesLimit=1,moreThanMin=0.5,moreThanMax=0.2):
	originalContentDict = contentDict
	contentDict = {} #复制contentDict
	for key in originalContentDict:
		contentDict[key] = originalContentDict[key].copy()

	combineDict = {} #合体记录

	for longWordLength in range(2,max(contentDict)+1): #从长度2的词组开始罗列主词
		#按出现次数倒序
		mainWordList = sorted(contentDict[longWordLength].items(),key=lambda x:x[1],reverse=True)

		for mainWord in mainWordList: #取出主词(词，次数)
			word = mainWord[0]
			wordTimes = contentDict[len(word)].get(word,0) #动态更新词出现的次数

			if wordTimes<timesLimit:
				continue 
				# 被手动排除的词 & 排除只出现XX次的词(不然剩余的低于XX词的词 比如1次 百分百会合体成功通过)
				# 设置太低，会导致字数少的高频字被字数多的消解，而字数高的高频字最终未必存活(显示时被过滤)，导致字数低的高频字消失。
				# 	可以通过因子归还解决，即最后没用到的词组的因子数按原路径加回去。但取数值没问题，取top百分比会出现循环。
				# 排除数设置高时，按公式也只会使用高频的因子。目前未发现副作用。

			# print u'====================\n主词:\t%s\t%s'%(word,wordTimes)

			combineSuccess = False
			for A_end in range(1,len(word)): #取得包含的词的词长
				A_word = word[:A_end] #取出包含的A词
				for B_start in range(1,A_end+1):
					B_word = word[B_start:] #取出包含的B词
					# print 'A=%s\tB=%s'%(A_word,B_word)
					if A_word not in contentDict[len(A_word)] or B_word not in contentDict[len(B_word)]:
						continue #如果因子已不存在则跳过
					A_times = contentDict[len(A_word)][A_word] #A词出现次数
					B_times = contentDict[len(B_word)][B_word] #B词出现次数

					# print '= %s=%s,%s=%s,%s=%s'%(mainWord[0],wordTimes,A_word,A_times,B_word,B_times)

					# 主词出现次数>min因子出现次数*阈值 = 主词占据该因子的比例很大(主词很可能是个词组 e.g.域名=20,域=18,名=15)
					# 主词出现次数<min因子出现次数 = 该因子已被其他词占用
					# 主词出现次数>max因子出现次数*阈值 = 防止频度极高的常用词成为词组(e.g.域名的=15,域名=20,的=200)
					if min(A_times,B_times)*moreThanMin <= wordTimes and wordTimes <= min(A_times,B_times) \
					and max(A_times,B_times)*moreThanMax <= wordTimes:

						if word in combineDict: #如果因子已在排除周边词时被使用过，先退还被使用的次数。
							if A_word in combineDict[word]: #因子是否有登记过
								contentDict[len(A_word)][A_word] += combineDict[word][A_word] #退回
								# print u'退回 %s=(%s->%s)'%(A_word,A_times,contentDict[len(A_word)][A_word])
								A_times = contentDict[len(A_word)][A_word] #刷新A词出现次数

							if B_word in combineDict[word]: #因子是否有登记过
								contentDict[len(B_word)][B_word] += combineDict[word][B_word] #退回
								# print u'退回 %s=(%s->%s)'%(B_word,B_times,contentDict[len(B_word)][B_word])
								B_times = contentDict[len(B_word)][B_word] #刷新B词出现次数

						combineDict[word] = {A_word:wordTimes,B_word:wordTimes} #如果没有，直接登记

						contentDict[len(A_word)][A_word] -= wordTimes
						contentDict[len(B_word)][B_word] -= wordTimes

						# print '> %s=%s, %s=(%s->%s), %s=(%s->%s)'%(word,wordTimes,A_word,A_times,contentDict[len(A_word)][A_word],B_word,B_times,contentDict[len(B_word)][B_word])

						# for key in combineDict[word]: #打印已登记字典
						# 	print '%s > %s=%s'%(word,key,combineDict[word][key])

						combineSuccess = True
						break #合体成功一次即完结
				if combineSuccess:
					break

			if combineSuccess==0:
				# print u'# 合体失败'
				contentDict[len(word)][word] = 0
			else:
				# print u'==合体成功=='
				# 排除非因子的占用(e.g.美国政府=7,美国=20,政府=17,因子排除成立,但剩余,美=0,国政府=8,需要把国政府-7)
				contentDict = reduceUnusedWords(contentDict,word,combineDict)
				# 排除连续情况 e.g.'的推荐算法'找到了'推荐'，要排除'的推'和'荐算'
				contentDict = excludeAroundWords(word,contentDict,content,combineDict)

	return contentDict



"""
获得一个长度组的有效词组之后
重新计算下级词组的使用频次
防止重复扣除次数
"""
def reduceUnusedWords(contentDict,word,combineDict):
	wordTimes = contentDict[len(word)][word] #动态更新词出现的次数
	for devidePoint in range(1,len(word)): #取得包含的词的词长
		for subWord in (word[:devidePoint],word[devidePoint:]): #取出因子

			wordUsed = False
			for usedWord in combineDict[word]:
				if subWord in usedWord: #如果因子已使用则跳过
					wordUsed = True
					break 
			if wordUsed:
				continue

			if subWord not in contentDict[len(subWord)]:
				continue #如果因子已不存在则跳过

			subWordTimes = contentDict[len(subWord)][subWord] #因子出现次数
			if subWordTimes >= wordTimes:
				contentDict[len(subWord)][subWord] -= wordTimes #扣除因子剩余数

				# 例如 甚至整个=1,甚至=3->2,整个=3->2;整个科技圈=1,整个=2->1,科技圈=1->0
				# 但 甚至整个科技圈=1,甚至整个=1->0,整个科技圈=1->0 这里整个就被扣了两次
				for usedWord in combineDict[word].keys(): #取出用过的词
					if usedWord not in subWord:
						if word.find(subWord)==0:
							A_word,B_word=subWord,usedWord
						else:
							A_word,B_word=usedWord,subWord
						for length in range(1,min(len(A_word),len(B_word)))[::-1]:
							A_part=A_word[len(A_word)-length:]
							B_part=B_word[:length]
							if A_part==B_part:
								contentDict[len(A_part)][A_part]+=wordTimes #新因子退回重叠的部分
								# print u'退回重复部分 %s=(%s->%s) from:(%s,%s)'%(A_part,contentDict[len(A_part)][A_part]-wordTimes,contentDict[len(A_part)][A_part],A_word,B_word)
					else:
						contentDict[len(usedWord)][usedWord]+=wordTimes #新因子退回重叠的部分
						# print u'退回重复部分 %s=(%s->%s) from:(%s,%s)'%(usedWord,contentDict[len(usedWord)][usedWord]-wordTimes,contentDict[len(usedWord)][usedWord],usedWord,subWord)
						combineDict[word][usedWord] -= wordTimes

				combineDict[word][subWord] = wordTimes #添加因子使用数
				# print u'排除已使用 %s=(%s->%s) from: %s'%(subWord,subWordTimes,subWordTimes-wordTimes,word)
	return contentDict



"""
去除有效词组前后相连的非重要词
"""
def excludeAroundWords(word,contentDict,content,combineDict):
	for searchWord in content: #设定范围
		wordStart = searchWord.find(word)
		# print 'wordStart:%s'%wordStart
		if wordStart>=0:
			# print 'form:%s - %s'%(searchWord,word)
			# print 'searchin:%s,start:%s'%(searchWord,wordStart)
			for start in range(wordStart-len(word)+1,wordStart+len(word)):
				if start>=0 and start+len(word)<=len(searchWord) and start!=wordStart:
					excludeWord = searchWord[start:start+len(word)] #要排除的词
					if excludeWord in contentDict[len(excludeWord)]: #要排除的词存在
						excludeWordTimes = contentDict[len(excludeWord)][excludeWord] #要排除的词出现次数
						searchInWord = searchWord[min(start,wordStart):max(start,wordStart)+len(word)] #找出合词 e.g.美国的
						contentDict[len(excludeWord)][excludeWord] -= 1
						# print u'# %s - %s=(%s->%s)'%(searchInWord,excludeWord,excludeWordTimes,contentDict[len(excludeWord)][excludeWord])

						if searchInWord not in combineDict: #如果主词无任何因子
							combineDict[searchInWord] = {excludeWord:1} #添加因子
						elif excludeWord not in combineDict[searchInWord]: #如果主词未包含目标因子
							combineDict[searchInWord][excludeWord] = 1 #添加因子
						else: #如果主词已含目标因子
							combineDict[searchInWord][excludeWord] += 1 #使用数+1

						# for key in combineDict[searchInWord]: #打印combineDict
						# 	print u'%s 已含 %s=%s'%(searchInWord,key,combineDict[searchInWord][key])

	return contentDict



"""
打印结果
"""
def printResult(asciiDict,contentDict,appearTimeLimit=1,top=999):
	# drawTitle('RESULT')
	result = [i for i in asciiDict.items() if i[1]>=appearTimeLimit] #取出英数

	for length in range(2,max(contentDict)+1)[::-1]: #优先长词组
		result += sorted([i for i in contentDict[length].items() if i[1]>=appearTimeLimit],key=lambda x:x[1],reverse=True) #正常统计
		# result += sorted([(i,j*length) for (i,j) in contentDict[length].items()],key=lambda x:x[1],reverse=True) #字数加成
	result = sorted(result,key=lambda x:x[1],reverse=True)

	for i in result[:top]: #打印前XX位
		print i[0],i[1]



"""
主入口
"""
filename = 'test/text1.txt'
commonList = [i for i in u'是的一些'] #常用字(避免这些字开头或结尾)
content = loadFile(filename)
asciiDict = getAsciiDict(content)
splitContent,baseContentDict = getChineseDict(content,5) #最长词长度
globalTimes = 5 #最小出现次数
newContentDict = combineWords(splitContent,baseContentDict,globalTimes,0.5,0.2) #(只处理>=X次出现的词),(越小越容易选到非词组),(越大越容易选到常用字)
printResult(asciiDict,newContentDict,globalTimes) #最小出现次数