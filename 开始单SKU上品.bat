@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo 未找到 Python 启动器 py，请先安装 Python 3.11 或更高版本。
  pause
  exit /b 2
)
set /p SKU=请输入货号：
if "%SKU%"=="" (
  echo 货号不能为空。
  pause
  exit /b 1
)
set /p RECORD=请输入商品资料 JSON 或 Excel 路径：
if "%RECORD%"=="" (
  echo 商品资料路径不能为空。
  pause
  exit /b 1
)
set "RECORD=%RECORD:"=%"
if not exist "%RECORD%" (
  echo 找不到商品资料文件：%RECORD%
  pause
  exit /b 2
)
set /p SOURCE_ROOT=请输入货盘根目录：
if "%SOURCE_ROOT%"=="" (
  echo 货盘根目录不能为空。
  pause
  exit /b 1
)
set /p REVIEW_ROOT=请输入可写的复审和备份根目录：
if "%REVIEW_ROOT%"=="" (
  echo 复审和备份根目录不能为空。
  pause
  exit /b 1
)
py -3 "%~dp0tools\auto_listing.py" "%SKU%" --record "%RECORD%" --source-root "%SOURCE_ROOT%" --review-root "%REVIEW_ROOT%"
if errorlevel 1 echo 程序执行失败，请查看上面的错误信息。
echo.
pause
