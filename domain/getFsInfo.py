import uos

# 获取文件系统统计信息
fs = uos.statvfs('/')
total = fs[0] * fs[2]  # 块大小 * 总块数
free = fs[0] * fs[3]   # 块大小 * 空闲块数

print(f"总空间: {total/1024:.0f} KB")
print(f"空闲: {free/1024:.0f} KB")