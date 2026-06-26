# Ubuntu 安裝 Python

先更新套件

```sh
sudo apt update
```

查看目前版本

```sh
python3 --version
```

安裝其他版本（以 Ubuntu 軟體庫提供的版本為準）：

```sh
sudo apt install python3.10
sudo apt install python3.12
```

查看已安裝：

```sh
/usr/bin/python3.10
/usr/bin/python3.12
```

# 步驟

**1. 進入專案資料夾**

```bash
cd /Download/project
```

**2. 安裝工具並打包**

工具

```sh
pip install pyinstaller
```

打包

```bash
python3.12 -m venv venv312
source venv312/bin/activate
pip install -r requirements.txt
pyinstaller --onefile main.py
```

**3. 執行檔產出在：**

```
dist/main
```

## 部署到 Ubuntu 並執行

```bash
./main
```

預期輸出：

```
NTP 時間: 2026-06-27 08:30:00 UTC
```

## 輸出目錄結構

```sh
project/
├── dist/
│   └── main        ← 可執行檔
├── build/          ← 暫存，可刪除
├── main.spec       ← PyInstaller 設定檔
├── requirements.txt
└── main.py
```

---

# 多個 .py 檔打包

## 原則

PyInstaller 只需指定**入口檔案**（main.py），它會自動追蹤所有 `import` 並將相依的 .py 一起打包進去。

## 專案結構範例

```
project/
├── main.py          ← 入口，指定這個給 PyInstaller
├── utils.py
├── config.py
└── service/
    ├── __init__.py
    └── ntp.py
```

`main.py` 範例：

```python
from utils import helper
from service.ntp import get_time

print(get_time())
```

## 打包指令（與單檔相同）

```bash
pyinstaller --onefile main.py
```

PyInstaller 會自動將 `utils.py`、`config.py`、`service/ntp.py` 全部打入執行檔。

## 若有模組未被自動偵測

動態 import（如 `importlib.import_module('xxx')`）PyInstaller 無法靜態分析，需手動加入：

```bash
pyinstaller --onefile --hidden-import utils --hidden-import service.ntp main.py
```

## 若需附帶非 .py 資源檔（圖片、設定檔等）

```bash
pyinstaller --onefile --add-data "config.json:." main.py
```

> 格式：`來源路徑:執行檔內的目標資料夾`，Linux 用 `:` 分隔。

在程式碼中讀取資源檔需使用：

```python
import sys, os

def resource_path(name):
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, name)

with open(resource_path('config.json')) as f:
    ...
```

## 常見問題

| 問題 | 解法 |
|------|------|
| `ModuleNotFoundError` 執行時找不到模組 | 加上 `--hidden-import 模組名` |
| 資源檔找不到 | 改用 `resource_path()` 讀取 |
| 想確認哪些檔案被打包 | 檢查 `main.spec` 內的 `Analysis` 區塊 |
