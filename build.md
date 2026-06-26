# 在 Windows 上打包成 Ubuntu 可執行檔 SOP

> **原則**：PyInstaller 不支援跨平台編譯，必須借助 **Docker** 或 **WSL** 在 Linux 環境內打包，才能產出 Ubuntu 可執行檔。

---

## 方法一：Docker（推薦，不需安裝 WSL）

### 前置需求
- 安裝 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- 確認 Docker 已啟動（系統匣有鯨魚圖示）

### 步驟

**1. 開啟 PowerShell，進入專案資料夾**

```powershell
cd C:\Users\Len\Desktop\py-ubuntu
```

**2. 產出 requirements.txt**

```powershell
pip freeze | Select-String "ntplib" | Out-File -Encoding utf8 requirements.txt
```

或手動建立 `requirements.txt`，內容：

```
ntplib==0.4.0
```

**3. 在 Linux 容器內打包（一行指令）**

```powershell
docker run --rm -v "${PWD}:/app" -w /app python:3.10-slim `
  bash -c "pip install -r requirements.txt pyinstaller && pyinstaller --onefile test.py"
```

**4. 等待完成，執行檔產出在：**

```
dist\test          ← 這就是 Ubuntu 可執行檔
```

---

## 方法二：WSL（已有 WSL 的用戶）

### 步驟

**1. 開啟 WSL Ubuntu 終端機**

```powershell
wsl
```

**2. 進入專案資料夾**

```bash
cd /mnt/c/Users/Len/Desktop/py-ubuntu
```

**3. 安裝工具並打包**

```bash
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install ntplib pyinstaller
pyinstaller --onefile test.py
```

**4. 執行檔產出在：**

```
dist/test
```

---

## 部署到 Ubuntu 並執行

### 複製執行檔到 Ubuntu 機器

```powershell
# 用 scp（需要 OpenSSH）
scp dist\test user@192.168.x.x:/home/user/

# 或透過 SFTP / USB / 共用資料夾傳送
```

### 在 Ubuntu 上執行

```bash
chmod +x ~/test
./test
```

預期輸出：

```
NTP 時間: 2026-06-27 08:30:00 UTC
```

---

## 輸出目錄結構

```
py-ubuntu/
├── dist/
│   └── test        ← 複製這個到 Ubuntu
├── build/          ← 暫存，可刪除
├── test.spec       ← PyInstaller 設定檔
├── requirements.txt
└── test.py
```

---

## 常見問題

| 問題 | 解法 |
|------|------|
| `docker: command not found` | 確認 Docker Desktop 已安裝並啟動 |
| `Permission denied` 無法執行 | `chmod +x test` |
| 在舊 Ubuntu 上跑不起來 | 改用 `python:3.8-slim` image 打包 |
| 想指定執行檔名稱 | 加上 `--name ntp_tool` 參數 |
