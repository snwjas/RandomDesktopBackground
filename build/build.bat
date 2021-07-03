chcp 65001
@echo off

title Python项目打包.EXE


@REM 打包依赖 pyinstaller
@REM pip install pyinstaller

pyinstaller -D application.spec --clean -y


echo.&&echo 打包完成！程序位于当前目录的dist文件夹下。

echo.&&set /p tips=按任意键退出...