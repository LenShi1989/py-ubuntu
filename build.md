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
