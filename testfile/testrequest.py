import urequests

url = "www.example.com"  # 替换为您要请求的URL

# 发送GET请求
response = urequests.get(url)

# 检查响应状态码
if response.status_code == 200:
    # 获取响应内容
    content = response.text
    print("Response:", content)
else:
    print("Error:", response.status_code)

# 关闭响应连接
response.close()
