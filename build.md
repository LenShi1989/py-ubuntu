# 打包 Python 腳本為 Ubuntu 可執行檔 SOP

> **重要**：PyInstaller 只能產生與執行環境相同 OS 的執行檔。
> 要產出 Ubuntu (Linux x86_64) 執行檔，**必須在 Linux 環境下執行打包**。

---

## 前置確認

| 項目 | 說明 |
|------|------|
| 目標腳本 | `test.py` |
| 相依套件 | `ntplib` |
| 目標平台 | Ubuntu (Linux x86_64) |
| 打包工具 | PyInstaller |

---

## 方法一：使用 WSL (Windows Subsystem for Linux) — 推薦

### 步驟 1：開啟 WSL Ubuntu 終端機

```bash
wsl
```

### 步驟 2：安裝 Python 與相依工具

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 步驟 3：進入專案目錄

```bash
cd /mnt/c/Users/Len/Desktop/py-ubuntu
```

### 步驟 4：建立虛擬環境並安裝套件

```bash
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install ntplib pyinstaller
```

### 步驟 5：打包

```bash
pyinstaller --onefile test.py
```

### 步驟 6：取得執行檔

打包完成後，執行檔位於：

```
dist/test
```

驗證：

```bash
./dist/test
```

---

## 方法二：使用 Docker

### 步驟 1：確認 Docker Desktop 已安裝並啟動

### 步驟 2：在專案根目錄執行一次性容器打包

```bash
docker run --rm \
  -v "$(pwd):/app" \
  -w /app \
  python:3.10-slim \
  bash -c "pip install ntplib pyinstaller && pyinstaller --onefile test.py"
```

Windows PowerShell 版：

```powershell
docker run --rm `
  -v "${PWD}:/app" `
  -w /app `
  python:3.10-slim `
  bash -c "pip install ntplib pyinstaller && pyinstaller --onefile test.py"
```

### 步驟 3：取得執行檔

```
dist/test
```

---

## 方法三：在實體 Ubuntu 機器上執行

### 步驟 1：將專案複製到 Ubuntu

```bash
scp -r /path/to/py-ubuntu user@ubuntu-host:~/py-ubuntu
```

或用 USB / Git 傳送。

### 步驟 2：安裝環境

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

### 步驟 3：打包

```bash
cd ~/py-ubuntu
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install ntplib pyinstaller
pyinstaller --onefile test.py
```

---

## 常用 PyInstaller 參數

| 參數 | 說明 |
|------|------|
| `--onefile` | 打包成單一執行檔 |
| `--onedir` | 打包成資料夾（啟動較快） |
| `--name myapp` | 指定輸出執行檔名稱 |
| `--hidden-import ntplib` | 手動加入未被偵測到的套件 |
| `--strip` | 移除符號表，縮小檔案 |

範例（指定名稱）：

```bash
pyinstaller --onefile --name ntp_tool test.py
```

---

## 輸出目錄說明

```
py-ubuntu/
├── dist/
│   └── test          ← Ubuntu 可執行檔（此檔案即可複製到目標機器）
├── build/            ← 暫存檔，可刪除
├── test.spec         ← PyInstaller 設定檔（可重複使用）
└── test.py
```

---

## 部署到目標 Ubuntu 機器

```bash
scp dist/test user@target-host:/usr/local/bin/ntp_tool
ssh user@target-host "chmod +x /usr/local/bin/ntp_tool && ntp_tool"
```

---

## 常見問題排除

| 問題 | 解法 |
|------|------|
| `ModuleNotFoundError: ntplib` | 加上 `--hidden-import ntplib` |
| 執行檔無法執行 (`Permission denied`) | `chmod +x dist/test` |
| 執行檔在舊版 Ubuntu 上跑不起來 | 改用較舊的 Python Docker image，如 `python:3.8-slim` |
| 檔案太大 | 改用 `--onedir` 模式或加上 `--strip` |
