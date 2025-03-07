import os, sys, shutil
sys.path.insert(1,"./COMTool/")     # # 在系统路径中插入"./COMTool/"目录，这样Python就能在这个目录下查找模块
from COMTool import version, i18n
import zipfile
import shutil
import re


if sys.version_info < (3, 7):
    print("only support python >= 3.7, but now is {}".format(sys.version_info))
    sys.exit(1)

# when execute packed executable program(./dist/comtool) warning missing package, add here to resolve
# 这些模块在运行时被动态加载，而 PyInstaller 默认的分析可能无法检测到它们
hidden_imports = [
    # "pyqtgraph.graphicsItems.PlotItem.plotConfigTemplate_pyqt5", # fixed in latest pyinstaller-hooks-contrib
    # "pyqtgraph.graphicsItems.ViewBox.axisCtrlTemplate_pyqt5",
    # "pyqtgraph.imageview.ImageViewTemplate_pyqt5",
    "babel.numbers"     # Babel 是一个用于国际化的库，它支持多种语言和地区，提供了日期、时间、数字、货币等的本地化格式化和解析功能
]

# windows_out = "robotool_windows_v{}.7z".format(version.__version__)   # 二选一
windows_out = "robotool_windows_v{}.rar".format(version.__version__)

# def zip_7z(out, path):
#     out = os.path.abspath(out)
#     cwd = os.getcwd()
#     os.chdir(os.path.dirname(path))
#     ret = os.system(f"7z a -t7z -mx=9 {out} {os.path.basename(path)}")
#     if ret != 0:
#         raise Exception("7z compress failed")
#     os.chdir(cwd)

# ''' 更新一个规范文件（spec 文件），该文件中包含用于构建软件包的 BUNDLE 函数调用
# spec_path：规范文件的路径。 items：一个字典，包含要更新到 BUNDLE 函数的关键字参数。 plist_items：一个字典，包含要更新到 info_plist 的项。'''
# def update_spec_bundle(spec_path, items = {}, plist_items={}):
#     with open(spec_path) as f:
#         spec = f.read()         # 打开并读取规范文件的内容到变量 spec

#     ''' 定义内部函数 BUNDLE，它接受任意数量的位置参数和关键字参数。这个函数用于生成更新后的 BUNDLE 函数调用字符串。
#     它首先更新传入的关键字参数 kw_args，然后检查是否有 info_plist 参数，如果有则更新，否则添加。
#     接着，它构造一个包含所有参数的字符串 bundle_str_args '''
#     def BUNDLE(*args, **kw_args):
#         kw_args.update(items)
#         if "info_plist" in kw_args:
#             kw_args["info_plist"].update(plist_items)
#         else:
#             kw_args["info_plist"] = plist_items
#         bundle_str_args = ""
#         for arg in args:
#             if type(arg) == str and arg != "exe" and arg != "coll":
#                 bundle_str_args += f'"{arg}", \n'
#             else:
#                 bundle_str_args += f'{arg}, \n'
#         for k, v in kw_args.items():
#             if type(v) == str:
#                 bundle_str_args += f'{k}="{v}",\n'
#             else:
#                 bundle_str_args += f'{k}={v},\n'
#         return bundle_str_args
#     # 使用正则表达式 re.findall 查找规范文件中所有的 BUNDLE 函数调用，并将匹配的结果存储在 match 中
#     match = re.findall(r'BUNDLE\((.*?)\)', spec, flags=re.MULTILINE|re.DOTALL)
#     if len(match) <= 0:
#         raise Exception("no BUNDLE found in spec, please check code")
#     # 构造一个新的 BUNDLE 函数调用字符串 code，并使用 exec 函数执行这段代码。这里使用 exec 是为了动态地创建一个 app 变量，该变量包含了更新后的 BUNDLE 调用
#     code =f'app = BUNDLE({match[0]})'
#     vars = {
#         "BUNDLE": BUNDLE,
#         "exe": "exe",
#         "coll": "coll"
#     }
#     exec(code, vars)
#     final_str = vars["app"]
#     #  使用 re.sub 函数和 re_replace 函数替换规范文件中的 BUNDLE 调用
#     def re_replace(c):
#         print(c[0])
#         return f'BUNDLE({final_str})'
#     # 生成最终的字符串 final_str
#     final_str = re.sub(r'BUNDLE\((.*)\)', re_replace, spec, flags=re.I|re.MULTILINE|re.DOTALL)
#     print(final_str)
#     # 将更新后的规范文件内容写回到文件中
#     with open(spec_path, "w") as f:
#         f.write(spec)

def zip(out, path):
    out = os.path.abspath(out)      # 将 out 参数转换为绝对路径，确保生成的 ZIP 文件路径是绝对路径
    cwd = os.getcwd()               # 保存当前工作目录的路径到变量 cwd，以便在压缩完成后可以返回到原来的工作目录
    os.chdir(os.path.dirname(path)) # 改变当前工作目录到 path 参数指定的目录的父目录，这样在后续的操作中可以相对简洁地处理文件路径
    # 创建一个新的 ZIP 文件，文件名为 out 参数指定的路径，模式为写入模式 'w'，压缩方式为 zipfile.ZIP_DEFLATED（即使用 zlib 库进行压缩）。
    # with 语句确保 ZIP 文件在使用完毕后会被正确关闭
    with zipfile.ZipFile(out,'w', zipfile.ZIP_DEFLATED) as target:
        # 使用 os.walk 函数遍历 path 参数指定的目录及其所有子目录。os.path.basename(path) 获取目录的基名称，即不包含路径的部分
        for i in os.walk(os.path.basename(path)):
            for n in i[2]:          # os.walk 返回的每个 i 是一个三元组，其中 i[2] 是当前遍历到的目录下的文件列表。
                # 将当前遍历到的文件添加到 ZIP 文件中。os.path.join(i[0],n) 构造文件的完整路径，target.write 方法将文件写入 ZIP 文件。
                target.write(os.path.join(i[0],n))
    os.chdir(cwd)                   # 将当前工作目录改回到之前保存的 cwd，即函数执行前的工作目录

def pack():
    # update translate
    i18n.main("finish")             # 调用 i18n 模块的 main 函数来完成翻译文件的更新
    # 如果存在 COMTool 目录下的 __pycache__ 文件夹，则删除它，以清理缓存文件
    if os.path.exists("COMTool/__pycache__"):
        shutil.rmtree("COMTool/__pycache__")
    hidden_imports_str = ""
    for item in hidden_imports:     # 遍历列表，构建 PyInstaller 的隐藏导入参数
        hidden_imports_str += f'--hidden-import {item} '

    # 构建适用于 Windows 平台的 PyInstaller 命令，包括添加数据文件、图标等
    if sys.platform.startswith("win32"):
        cmd = (
            f'pyinstaller {hidden_imports_str} '        # 隐藏导入的模块字符串，确保所有依赖都被包含
            '-p "COMTool" '                             # 指定 Python 路径，添加 COMTool 目录到搜索路径
            '--add-data="COMTool/assets;assets" '       # 添加 assets 目录到打包后的程序中
            '--add-data="COMTool/locales;locales" '     # 添加 locales 目录到打包后的程序中
            '--add-data="COMTool/protocols;protocols" ' # 添加 protocols 目录到打包后的程序中
            '--add-data="README.MD;./" '                # 添加 README.MD 到打包后的程序中
            '--add-data="README_ZH.MD;./" '             # 添加 README_ZH.MD 到打包后的程序中
            '-i="COMTool/assets/logo.ico" '             # 设置应用程序图标
            '-w COMTool/Main.py -n robotool'            # 指定主脚本文件，并以窗口模式运行。设置生成的可执行文件的名称
        )
    # 打印并执行构建好的打包命令，如果命令执行失败，则抛出异常
    print("-- execute:", cmd)
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("pack failed")

    # 处理不同操作系统的打包结果
    # if sys.platform.startswith("win32"):
    #     zip(windows_out, "dist/robotool")   # 将打包后的应用程序压缩成 ZIP 文件。
    #     zip_7z(windows_out, "dist/robotool")

# 根据用户在命令行传递的操作系统名称参数来重命名输出目录，并打印出新的输出目录路径。如果没有提供参数，则调用 pack() 函数执行打包操作
if __name__ == "__main__":
    if len(sys.argv) > 1:
        os_name = sys.argv[1]                       # 获取用户在命令行传递的操作系统名称参数
        if os_name.startswith("windows"):
            if os_name != "windows-latest":
                windows_out_new = windows_out.replace("windows", os_name.replace("-", "_"))
                os.rename(windows_out, windows_out_new)
                windows_out = windows_out_new
            print(windows_out)
        else:
            sys.exit(1)
    else:
        pack()


