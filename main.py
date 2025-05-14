import os
from pathlib import Path
from flask import Flask, request, render_template_string
from openai import OpenAI, AuthenticationError

app = Flask(__name__)

# 带样式的 HTML 模板，支持 Markdown 渲染
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>合同分析助手</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { padding: 40px; background-color: #f9f9f9; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        pre { background-color: #f4f4f4; padding: 15px; border-radius: 8px; }
        .spinner-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 60px;
        }
    </style>
</head>
<body>
<div class="container">
    <h1 class="mb-4">📄 合同分析助手</h1>
    <form method="post" enctype="multipart/form-data" class="mb-4" id="uploadForm">
        <input type="file" name="file" class="form-control" required>
        <button type="submit" class="btn btn-primary mt-2">上传并分析</button>
    </form>

    <!-- 加载动画 -->
    <div id="loading" class="spinner-container" style="display: none;">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">加载中...</span>
        </div>
    </div>

    <!-- 分析结果 -->
    {% if message_content %}
        <h2 class="mt-5">🔍 分析结果:</h2>
        <div id="markdown-content" class="markdown-body" style="white-space: pre-wrap;">{{ message_content }}</div>
        <script>
            // 使用 marked.js 将 Markdown 转换为 HTML
            const content = document.getElementById('markdown-content');
            content.innerHTML = marked.parse(content.textContent);
        </script>
    {% endif %}
</div>

<script>
    document.getElementById('uploadForm').addEventListener('submit', function () {
        document.getElementById('loading').style.display = 'flex';
    });
</script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    message_content = None
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            file_path = Path(uploaded_file.filename)
            uploaded_file.save(file_path)

            client = OpenAI(
                api_key="sk-c61ccca1f2cb4501826ab86d57b69e04",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

            try:
                file_object = client.files.create(file=file_path, purpose="file-extract")

                completion = client.chat.completions.create(
                    model="qwen-long",
                    messages=[
                        {"role": "system", "content": f"fileid://{file_object.id}"},
                        {
                            "role": "user",
                            "content": "阅读这份文档,自动抓取本合同的甲乙方以及金额，统计各方作为甲方和乙方的次数，从而判定双方承担的风险和收益是否一致",
                        },
                    ],
                )
                message_content = completion.choices[0].message.content
            except Exception as e:
                # 其他异常处理（可选）
                message_content = f"发生错误"
            finally:
                # 删除临时文件
                if file_path.exists():
                    os.remove(file_path)

    return render_template_string(HTML_TEMPLATE, message_content=message_content)


if __name__ == "__main__":
    app.run(debug=True)










