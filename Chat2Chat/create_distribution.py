import zipfile
import os
import shutil

# 定义分发目录和文件
dist_dir = r"dist\AI Talking"
output_zip = "AI_Talking_Distribution.zip"

# 创建 zip 文件
with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
    # 添加主程序文件
    exe_path = os.path.join(dist_dir, "AI Talking.exe")
    if os.path.exists(exe_path):
        zf.write(exe_path, "AI Talking.exe")
        print(f"添加文件: {exe_path}")
    else:
        print(f"警告: 文件不存在: {exe_path}")
    
    # 添加 _internal 目录
    internal_dir = os.path.join(dist_dir, "_internal")
    if os.path.exists(internal_dir):
        for root, _, files in os.walk(internal_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zf.write(file_path, arcname)
                print(f"添加文件: {file_path}")
    else:
        print(f"警告: 目录不存在: {internal_dir}")

print(f"\n分发包创建成功: {output_zip}")
print(f"包大小: {os.path.getsize(output_zip) / (1024 * 1024):.2f} MB")