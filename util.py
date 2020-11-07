#----------------------------------------------------------#
# 유틸 함수들

def calcRate(origin, now):
    return (now - origin) / origin
    
def checkRange(start, now, end):
    return min(end, max(now, start))
    
def isRange(start, now, end):
    if now == checkRange(start, now, end):
        return True
    return False
