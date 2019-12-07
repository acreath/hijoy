import string
count = 0
doc = {}
max = {}
with open('./test.txt','r') as f:
    data = f.read()
    for word in data:
        for w in data:
            if w == word:
                count+=1
        doc[word]=count
        count =0
        #print('word:{} \n'.format(word))
    list=sorted(doc.items(),key=lambda item: item[1],reverse=True)
    for l in list:
        print('{} \n'.format(l))
    
                




