
def get_ts(l):
    return int(l.split(',')[0])

f = open('metrics.csv','r')
ls = f.readlines()
f.close()

t1 = get_ts(ls[1])
cnt = 0
cnt_con = 0
cnt_con_all = 0
max_xx = 0
for i in range(len(ls)-3):
    t2 = get_ts(ls[i+2])
    t1 += 5
    flag = 0
    xx = 0
    while t1 < t2:
        t1 += 5
        if flag == 0:
            flag = 1
            cnt += 1
        elif flag == 1:
            cnt_con += 1
            flag = 2
        cnt_con_all += 1
        xx += 1
    if xx > max_xx:
        max_xx = xx

print('missing:', cnt_con_all)
print('total:', len(ls)-3)
print('rate:', cnt_con_all/(len(ls)-3))
print('con:', cnt_con)
print('average con:', cnt_con_all / cnt)
print('max con:', max_xx)

