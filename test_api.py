import os
from openai import OpenAI

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    print("[错误] 请设置环境变量 DASHSCOPE_API_KEY")
    print("[提示] PowerShell: $env:DASHSCOPE_API_KEY = \"你的API Key\"")
    raise SystemExit(1)

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

try:
    res = client.chat.completions.create(
        model="qwen-vl-max",
        messages=[{"role": "user", "content": "你好，回复'连接成功'"}]
    )
    print("✅ 连接成功：", res.choices[0].message.content)
except Exception as e:
    print("❌ 连接失败：", e)