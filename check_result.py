
f = open('result.txt','r')
ls = f.readlines()
f.close()

cnt = 0
for l in ls:
    if 'Missing' in l:
        cnt += 1

print('missing:', cnt)


