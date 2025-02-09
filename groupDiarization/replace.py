import os
import re

# 代码库的安装路径
library_path = "/opt/homebrew/lib/python3.9/site-packages/pyannote"

# 遍历所有 .py 文件
for root, dirs, files in os.walk(library_path):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 替换 np.complex 为 complex 或 np.complex128
            content = re.sub(r"np\.complex", "complex", content)  # 或者替换为 np.complex128
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)