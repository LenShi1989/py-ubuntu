# Ubuntu Nginx 部署 SOP

## 建立部屬目錄 /JQuan

```sh
sudo mkdir -p /JQuan/nx_assistant_web/dist
sudo mkdir -p /JQuan/nx_coreapi/publish
sudo mkdir -p /JQuan/nx_aiagentapi
sudo chmod -R 777 JQuan/
```

更新系統並安裝 Nginx

```sh
sudo apt update
sudo apt install -y nginx
```

檢查 Nginx 狀態：

```sh
sudo systemctl status nginx
```

設定開機自動啟動：

```sh
sudo systemctl enable nginx
```

檢查設定：

```sh
sudo nginx -t
```

重新載入：

```sh
sudo systemctl reload nginx
```

## 防火牆設定

只需要對外開 80 / 443，不要開 PostgreSQL 5432。

```sh
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 建立 Nginx 設定

本專案以 **3001 埠為唯一對外入口**：前端、`.NET Core API`、`FastAPI` 全部走這個站台轉發，
應用程式流量不使用 Nginx 預設的 80 埠站台（該站台維持保留，不刪除）。下面把這個 server block 設為
`default_server`，讓任何打到本機 3001 的請求（不論用 IP 或網域）都落到這裡。

> ⚠️ **先在 `http {}` context 加 WebSocket upgrade 對應（全站只需做一次，SignalR 需要）。**
> 下面 `/notificationHub/` 那段若把 `Connection` 寫死成固定字串 `"upgrade"`，會連同
> negotiate 完成後的實際連線請求（可能是一般 GET，不是真的要升級 WebSocket）一起被打上
> `Connection: upgrade`，導致後端 Kestrel 回 `400 Bad Request`。正確做法是依請求是否
> 真的帶 `Upgrade` header 動態決定：
>
> ```sh
> sudo nano /etc/nginx/nginx.conf
> ```
>
> 在 `http { ... }` 區塊內加入：
>
> ```nginx
> map $http_upgrade $connection_upgrade {
>     default upgrade;
>     ''      close;
> }
> ```
>
> 存檔後 `sudo nginx -t && sudo systemctl reload nginx`。下面 location 內的
> `proxy_set_header Connection` 一律改用 `$connection_upgrade`，不要寫死 `"upgrade"`。

建立站台設定：

```sh
sudo nano /etc/nginx/sites-available/nx_assistant_web
```

內容如下：

```sh
server {
    # 3001 設為預設站台（主入口），IPv4 / IPv6 皆然
    listen 3001 default_server;
    listen [::]:3001 default_server;
    server_name _;

    root /JQuan/nx_assistant_web/dist;
    index index.html;

    client_max_body_size 2000M;

    # Vue3 前端
    location / {
        try_files $uri $uri/ /index.html;
    }

    # .NET Core API
    location /api/ {
        proxy_pass http://127.0.0.1:5252/api/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 通知中心 SignalR Hub（CoreApi 掛在根路徑 /notificationHub，不在 /api/ 底下）
    # 需額外帶 Upgrade/Connection 才能升級成 WebSocket；SignalR 不同 transport 對同一個 hub
    # 用的路徑有沒有結尾斜線不一致（/notificationHub、/notificationHub/negotiate、
    # /notificationHub/?id=... 都會出現），location 不加結尾斜線才能全部匹配到，
    # proxy_pass 也不能帶路徑，否則 nginx 前綴改寫後的路徑會跟 Kestrel 實際註冊的
    # /notificationHub 對不上，導致 400。
    location /notificationHub {
        proxy_pass http://127.0.0.1:5252;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # FastAPI
    location /data-maintenance/ {
        proxy_pass http://127.0.0.1:8001/data-maintenance/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /repair-assistant/ {
        proxy_pass http://127.0.0.1:8001/repair-assistant/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

啟用站台：

```sh
sudo ln -s /etc/nginx/sites-available/nx_assistant_web /etc/nginx/sites-enabled/nx_assistant_web
```

> 保留 Nginx 預設站台（`/etc/nginx/sites-enabled/default`，監聽 80 埠）：與 3001 站台互不影響，可並存，
> 不刪除。防火牆已在前面「防火牆設定」節以 `sudo ufw allow 'Nginx Full'` 開放 80/443，不需額外處理。

檢查 Nginx 設定：

```sh
sudo nginx -t
```

重新載入：

```sh
sudo systemctl reload nginx
```

## 防火牆開放 3001

如果 Ubuntu 有開 UFW：

```sh
sudo ufw allow 3001/tcp
sudo ufw status
```

不建議開放後端 port：

```sh
5252
8001
5432
```

## 常用維護指令

檢查 Nginx 設定：

```sh
sudo nginx -t
```

重新載入 Nginx：

```sh
sudo systemctl reload nginx
```

重啟 Nginx：

```sh
sudo systemctl restart nginx
```

看錯誤 log：

```sh
sudo tail -f /var/log/nginx/error.log
```

看存取 log：

```sh
sudo tail -f /var/log/nginx/access.log
```

看 port 是否有啟動：

```sh
sudo ss -lntp
```

---

## 重新安裝 Nginx

移除及安裝 Nginx

```sh
sudo apt purge nginx nginx-common -y       # 完全移除（含設定檔）
sudo apt autoremove -y                     # 清除不需要的套件
sudo rm -rf /etc/nginx                     # 手動刪除殘留資料
sudo rm -rf /var/log/nginx                 # 手動刪除殘留資料
sudo rm -rf /var/www/html                  # 手動刪除殘留資料
sudo apt update                            # 更新apt
sudo apt install nginx -y                  # 安裝Nginx
```

---

## 部署前端 Web

傳送dist資料夾

```sh
cd /JQuan/nx_assistant_web/dist
```

## 部屬 .NET Core API

傳送publish資料夾

```sh
cd /JQuan/nx_coreapi
```

安裝 .NET Runtime

```sh
sudo apt update
sudo apt install -y aspnetcore-runtime-10.0
```

```sh
sudo nano /etc/systemd/system/nx_coreapi.service
```

內容如下：

```ini
[Unit]
Description=NX Core API
After=network.target

[Service]
WorkingDirectory=/JQuan/nx_coreapi/publish
ExecStart=/usr/bin/dotnet /JQuan/nx_coreapi/publish/CoreApi.dll
Restart=always
RestartSec=10
KillSignal=SIGINT
SyslogIdentifier=nx_coreapi
User=www-data
Environment=ASPNETCORE_ENVIRONMENT=Production
Environment=ASPNETCORE_URLS=http://127.0.0.1:5252

[Install]
WantedBy=multi-user.target
```

啟動服務：

```sh
sudo systemctl daemon-reload
sudo systemctl enable nx_coreapi
sudo systemctl start nx_coreapi
sudo systemctl status nx_coreapi
```

測試：

```sh
sudo apt update
sudo apt install -y curl
curl http://127.0.0.1:3001             # 轉跳至port:5252
curl http://127.0.0.1:3001/swagger     # 轉跳至port:5252
```

看 log：

```sh
sudo journalctl -u nx_coreapi -f
```

## 部屬 FastAPI

安裝python

```sh
# 更新套件
sudo apt update

# 安裝必要工具
sudo apt install -y software-properties-common

# 加入 PPA
sudo add-apt-repository ppa:deadsnakes/ppa

# 更新套件清單
sudo apt update

# 安裝 Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 設定 pip
sudo apt install -y python3-pip
```

驗證安裝

```sh
python3.12 --version
```

> 本專案 FastAPI 採用 **Nuitka 編譯保護原始碼**：把自己寫的 `.py` 編成 `.so`（放 `dist/`），
> 再搭配執行用 venv，由 systemd 啟動編譯版。第三方套件（fastapi、uvicorn…）一律不編、留在 venv。
> 編譯產物不可跨平台，必須在 Ubuntu 本機重新編譯。

#### 動手前先確認

1. 進入點：`main.py` 的 `app`（即 `main:app`）。
2. 自己寫的 `.py` 清單與資料夾結構：`main.py`、`config/`、`models/`、`routers/`、`schemas/`、`services/`、`utils/`（完整清單見下方編譯指令）。`test_*.py` 與 `analyze_pending.py`、`cleanup_dirty_board_documents.py`、`gen_classification_sql.py`、`organize.py` 等開發／一次性工具**不需**編譯部署。
3. 執行期資料目錄：`storage/`（內含 `repair_pdf` 等 PDF 實體檔），程式以相對於 `.py`／`.so` 的路徑存取，部署時 `dist/` 下必須能找到它。
4. 監聽埠：`8001`；Python 版本：`3.12`。

#### 安裝編譯相依

Nuitka 編譯需要 `python3.12-dev`（Python.h 標頭檔）與 `build-essential`、`patchelf`：

```sh
sudo apt install -y python3.12-dev build-essential patchelf
```

複製更新專案目錄:

```sh
cd /home/ai-assistant/nx_assistant
git pull
sudo cp -r nx_aiagentapi /JQuan/nx_aiagentapi
```

進入 FastAPI 專案目錄：

```sh
cd /JQuan/nx_aiagentapi
```

#### 建立 `.env` 設定檔

`.env` 已列入 `.gitignore`（不會進版控），所以**從 git 取得的程式碼不含 `.env`**，
需在伺服器上手動建立。缺少 `.env` 會在啟動時噴 `RuntimeError: DATABASE_URL 未設定，請檢查 .env`。

用 `nano` 在專案根目錄建立 `.env`：

```sh
sudo nano /JQuan/nx_aiagentapi/.env
```

把以下內容貼進去（資料庫指向本機 PostgreSQL，密碼／金鑰請依實際環境調整）：

```ini
DATABASE_URL=postgresql+asyncpg://postgres:St923420!@localhost:5432/nx_assistant
JWT_SIGN_KEY=NxAssistantJwtSignKey_2026_Development_Only_ChangeMe
JWT_ISSUER=NxAssistant
JWT_AUDIENCE=NxAssistantClient

# GPU 推論服務（AI server 10.30.2.200 經 nginx 轉發：11434->8100 DocLayout、11435->8200 VLM）
GPU_SERVICE_URL=http://10.30.2.200:11434
VLM_SERVICE_URL=http://10.30.2.200:11435
```

貼好後存檔離開：按 `Ctrl + O`、`Enter` 存檔，再按 `Ctrl + X` 離開。

> - `DATABASE_URL` 必用 `postgresql+asyncpg://`（本專案採非同步 SQLAlchemy 驅動）。
> - 連本機 DB 用 `localhost`；若 DB 在其他主機才改成該主機 IP（需先依「設定 TCP/IP 連線」開放）。
> - 正式環境請**更換 `JWT_SIGN_KEY`** 並確認與 `nx_coreapi` 的設定一致。

確認內容無誤：

```sh
cat /JQuan/nx_aiagentapi/.env
```

> 之後編譯／打包都會把這份 `.env` 複製到 `dist/`（見後續步驟）。日後只改 `.env` 內容
> 不需重編譯，覆寫 `dist/` 內的 `.env` 後重啟服務即可（見「更新部屬流程」）。

#### 建立「執行用」venv（跑服務用）

```sh
sudo python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

如果 requirements.txt 沒有 uvicorn，要補：

```sh
source venv/bin/activate
pip install uvicorn
deactivate
```

#### 建立「編譯用」venv 並安裝 Nuitka（與執行 venv 分開，避免污染）

```sh
python3.12 -m venv /JQuan/nx_aiagentapi/buildenv
/JQuan/nx_aiagentapi/buildenv/bin/pip install --upgrade pip
/JQuan/nx_aiagentapi/buildenv/bin/pip install nuitka
/JQuan/nx_aiagentapi/buildenv/bin/python -m nuitka --version   # 確認可用
```

#### 用 Nuitka 把原始碼編成 .so（核心步驟）

> ⚠️ **`.env` 讀取必須用明確路徑，不能用 `load_dotenv()` 裸呼叫。**
> `python-dotenv` 的 `load_dotenv()` 不帶參數時，是用 `sys._getframe()` 回溯呼叫堆疊找呼叫者所在目錄；
> 但 Nuitka 編譯後的模組**不會在直譯器堆疊上留下真正的 frame**（這是 Nuitka 的效能優化手段），
> 導致 `find_dotenv()` 直接跳過所有 Nuitka 編譯的中間層、落到堆疊裡最近的「真正 Python frame」
> （例如 uvicorn／importlib 那一層），從一個八竿子打不著的目錄開始往上找，永遠找不到 `dist/.env`，
> 啟動時噴 `RuntimeError: DATABASE_URL 未設定，請檢查 .env`——即使 `dist/.env` 檔案本身存在、內容正確也一樣。
>
> 注意這**不影響** `Path(__file__)` 這種模組層級直接取屬性的用法（`.so` 的 `__file__` 仍精準指向自己
> 實際位置，本 SOP 「連結執行期資料目錄 storage/」那段能正常運作就是靠這個機制）；只有像
> `load_dotenv()` 這種**主動回溯呼叫堆疊**的寫法才會壞。
>
> 本專案 `config/db_conf.py`、`utils/security.py` 已經改用：
>
> ```python
> load_dotenv(Path(__file__).resolve().parent.parent / ".env")
> ```
>
> 之後若新增任何要讀取 `.env` 的模組，一律照這個寫法，不要用裸的 `load_dotenv()`。

對**每一個自己寫的 `.py`** 執行，輸出到 `dist/` 並**保持資料夾結構**。
以下清單對應 `nx_aiagentapi` 實際的應用程式模組：

> ⚠️ **請把以下整段存成腳本檔（例如 `build.sh`）用 `bash build.sh` 一次執行完，不要逐行複製貼上到終端機。**
> 逐行貼上時若漏貼了 `BUILD`/`SRC`/`OUT` 變數宣告那幾行（例如中途換了新的 SSH session、
> 或只選取貼上部分指令），`$OUT` 會被展開成空字串，`--output-dir=$OUT/config` 就變成絕對路徑
> `/config`，Nuitka 會嘗試在檔案系統根目錄建資料夾，因權限不足而報
> `PermissionError: [Errno 13] Permission denied: '/config'`。
> 開頭加 `set -euo pipefail`，變數未設定時會立即中止並報錯，而不是靜默寫到非預期路徑。

```sh
set -euo pipefail

BUILD=/JQuan/nx_aiagentapi/buildenv/bin/python
SRC=/JQuan/nx_aiagentapi          # 原始碼根目錄
OUT=/JQuan/nx_aiagentapi/dist     # 輸出目錄
COMMON="-m nuitka --module --remove-output --no-pyi-file"

# 先建立與原始碼相同的資料夾結構
mkdir -p $OUT \
  $OUT/config \
  $OUT/models \
  $OUT/routers/data_maintenance \
  $OUT/routers/repair_assistant \
  $OUT/schemas/data_maintenance \
  $OUT/schemas/rag \
  $OUT/schemas/repair_assistant \
  $OUT/services/data_maintenance \
  $OUT/services/gpu_client \
  $OUT/services/rag \
  $OUT/services/repair_assistant/first_repair_work/image_pdf \
  $OUT/services/repair_assistant/first_repair_work/text_pdf \
  $OUT/utils

# 進入點
$BUILD $COMMON --output-dir=$OUT $SRC/main.py

# config
$BUILD $COMMON --output-dir=$OUT/config $SRC/config/db_conf.py

# models
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/auth_models.py
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/generated_models.py
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/repair_models.py

# routers
$BUILD $COMMON --output-dir=$OUT/routers                  $SRC/routers/db_test.py
$BUILD $COMMON --output-dir=$OUT/routers/data_maintenance $SRC/routers/data_maintenance/board_document_upload_router.py
$BUILD $COMMON --output-dir=$OUT/routers/data_maintenance $SRC/routers/data_maintenance/repair_data_import_router.py
$BUILD $COMMON --output-dir=$OUT/routers/repair_assistant $SRC/routers/repair_assistant/first_repair_work_router.py

# schemas
$BUILD $COMMON --output-dir=$OUT/schemas/data_maintenance $SRC/schemas/data_maintenance/board_document_upload_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/data_maintenance $SRC/schemas/data_maintenance/repair_data_import_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/rag              $SRC/schemas/rag/rag_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/repair_assistant $SRC/schemas/repair_assistant/first_repair_work_schema.py

# services
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/board_document_upload_service.py
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/model_classification_query.py
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/repair_data_import_service.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/_auth.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/layout_client.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/vlm_client.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/chunk_service.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/embedding_service.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/repair_case_service.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant $SRC/services/repair_assistant/group_pdf_query.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/first_repair_work_query.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/first_repair_work_service.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/hotspot_result.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/pdf_type_detector.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work/image_pdf $SRC/services/repair_assistant/first_repair_work/image_pdf/image_pdf_hotspot_processor.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work/text_pdf  $SRC/services/repair_assistant/first_repair_work/text_pdf/text_pdf_hotspot_processor.py

# utils
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/exception.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/exception_handlers.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/logging_config.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/response.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/security.py
```

複製空的 `__init__.py`（本專案僅 `gpu_client` 與 `image_pdf` 兩個套件有，且皆為空檔，原樣複製即可）與 `.env`：

```sh
cp $SRC/services/gpu_client/__init__.py \
   $OUT/services/gpu_client/__init__.py
cp $SRC/services/repair_assistant/first_repair_work/image_pdf/__init__.py \
   $OUT/services/repair_assistant/first_repair_work/image_pdf/__init__.py
cp $SRC/.env $OUT/.env
ls -l $OUT/.env   # 確認檔案在、不是 0 bytes，否則啟動會噴 DATABASE_URL 未設定
```

> 其餘資料夾（`routers/`、`schemas/`、`services/` …）在原始碼中即以 namespace package 形式運作（無 `__init__.py`），編譯後的 `.so` 放在相同結構下即可被 import，毋須額外補建 `__init__.py`。

連結執行期資料目錄 `storage/`。程式以 `Path(__file__)` 往上推算專案根目錄再找 `storage/repair_pdf`，因此 `dist/` 下必須有 `storage/`。建議把 PDF 資料留在 dist 外的穩定位置，再以 symlink 連入，這樣重新編譯（`rm -rf dist`）時資料不會被一起刪除：

```sh
# 實體資料目錄（與 dist 分開）
mkdir -p /JQuan/nx_aiagentapi/storage
# dist/storage 連到實體資料目錄（-f 覆寫舊連結、-n 不跟進既有目錄）
ln -sfn /JQuan/nx_aiagentapi/storage $OUT/storage
```

說明：

- `--module`：編成可被 import 的模組（產出 `xxx.cpython-312-x86_64-linux-gnu.so`），不是單一執行檔。
- 第一次編譯 Nuitka 可能自動下載/使用 gcc，正常。
- 編完 `dist/` 內應**只有 `.so` + 兩個空的 `__init__.py` + `.env`**（外加 `storage` symlink），沒有可讀的 `.py`。

驗證 dist 沒有殘留原始碼：

```sh
find $OUT -name "*.py"   # 預期只列出兩個 __init__.py
```

#### 自測：用「執行 venv」從 dist 啟動（換臨時埠，別撞線上）

```sh
cd /JQuan/nx_aiagentapi/dist
/JQuan/nx_aiagentapi/venv/bin/uvicorn main:app --host 127.0.0.1 --port 18001
```

另一個終端測試（測完 Ctrl+C 關掉）：

```sh
curl http://127.0.0.1:18001/docs
```

> ⚠️ **若這不是第一次自測**（例如服務已經跑過一輪、`dist/` 早已被下方「啟動前務必把
> `dist/` 擁有者改成 `www-data`」那步 `chown` 過），`dist/logs/` 底下的檔案會是
> `www-data` 所有。這時用一般帳號（例如 `ai-assistant`）重新執行上面的自測指令，
> 會在 `setup_logging()` 開檔時噴：
>
> ```text
> PermissionError: [Errno 13] Permission denied: '/JQuan/nx_aiagentapi/dist/logs/log.txt'
> ```
>
> 先把 `dist/logs` 擁有者改回目前帳號才能自測，測完、正式用 systemd 啟動前再照下方指令
> 改回 `www-data`：
>
> ```sh
> sudo chown -R ai-assistant:ai-assistant /JQuan/nx_aiagentapi/dist/logs
> ```

#### 建立 systemd service

```sh
sudo nano /etc/systemd/system/nx_aiagentapi.service
```

內容如下（`WorkingDirectory` 指向**編譯版 dist**，`ExecStart` 用**執行 venv** 的 uvicorn）：

```ini
[Unit]
Description=NX AI Agent FastAPI
After=network.target

[Service]
WorkingDirectory=/JQuan/nx_aiagentapi/dist
ExecStart=/JQuan/nx_aiagentapi/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=10
User=www-data
SyslogIdentifier=nx_aiagentapi

[Install]
WantedBy=multi-user.target
```

> ⚠️ **啟動前務必把 `dist/` 擁有者改成 `www-data`。** 前面編譯／自測都是用一般帳號（例如
> `ai-assistant`）執行，`dist/` 底下的檔案（含自測時 `setup_logging()` 建出來的 `dist/logs/`）
> 都是該帳號的，但 service 設定 `User=www-data`。owner 不一致會導致 `www-data` 寫不了
> `dist/logs/log.txt`，噴 `PermissionError: [Errno 13] Permission denied`，服務不斷重啟失敗。

```sh
sudo chown -R www-data:www-data /JQuan/nx_aiagentapi/dist
```

啟動服務：

```sh
sudo systemctl daemon-reload
sudo systemctl enable nx_aiagentapi
sudo systemctl start nx_aiagentapi
sudo systemctl status nx_aiagentapi
```

測試：

```sh
curl http://127.0.0.1:8001/docs
```

看 log：

```sh
sudo journalctl -u nx_aiagentapi -f
```

#### 收尾（完成原始碼保護）

確認編譯版在線上跑穩後，把 `/JQuan/nx_aiagentapi` 正式路徑下的原始 `.py` 移走或刪除，
否則原始碼還在硬碟上看得到，`dist/` 用 Nuitka 保護原始碼就沒有意義。**動手刪除前務必先備份**。

先備份完整原始碼（含 `config/`、`models/`、`routers/`、`schemas/`、`services/`、`utils/`
與開發／一次性工具腳本），存放於 `/JQuan/backup`（與 `nx_aiagentapi` 服務目錄分開，重編／
重部署都不會誤刪這份備份）：

```sh
sudo mkdir -p /JQuan/backup/nx_aiagentapi_src
sudo tar -czf /JQuan/backup/nx_aiagentapi_src/nx_aiagentapi_src_$(date +%Y-%m-%d).tar.gz \
  --exclude='venv' --exclude='buildenv' --exclude='dist' --exclude='storage' \
  -C /JQuan nx_aiagentapi
```

確認備份檔存在、內容非空：

```sh
ls -l /JQuan/backup/nx_aiagentapi_src/
tar -tzf /JQuan/backup/nx_aiagentapi_src/nx_aiagentapi_src_$(date +%Y-%m-%d).tar.gz | head
```

備份確認無誤後，刪除正式路徑下的原始碼（保留 `dist/`、`venv/`、`buildenv/`、`storage/`、`.env`）：

```sh
sudo find /JQuan/nx_aiagentapi -maxdepth 1 -name "*.py" -delete
sudo rm -rf /JQuan/nx_aiagentapi/config \
            /JQuan/nx_aiagentapi/models \
            /JQuan/nx_aiagentapi/routers \
            /JQuan/nx_aiagentapi/schemas \
            /JQuan/nx_aiagentapi/services \
            /JQuan/nx_aiagentapi/utils
```

驗證正式路徑已無可讀原始碼（`dist/` 內仍會列出兩個空的 `__init__.py`，屬預期，見前述編譯步驟）：

```sh
find /JQuan/nx_aiagentapi -name "*.py" -not -path "*/dist/*"   # 預期無任何輸出
```

> ⚠️ 「更新部屬流程」的 FastAPI 更新步驟會用 `git pull` + `cp -r` 把原始碼重新複製回
> `/JQuan/nx_aiagentapi`，每次更新完成、確認新版本跑穩後，都要重新執行本節刪除步驟，
> 否則原始碼又會留在正式路徑上。

## Windows 開發機使用 Nuitka 打包並部署至 Ubuntu

> Nuitka **不支援跨平台編譯**：在 Windows 上編譯只能產生 Windows `.pyd`，
> Ubuntu 需要的 `.so` 必須在 Linux 環境編譯。
> 推薦流程：Windows 安裝好開發環境 → 透過 **WSL2**（方法 A）或 **SSH 到 Ubuntu 伺服器**（方法 B）執行打包 → 服務跑在 Ubuntu。

### 1. 安裝 Nuitka（Windows）

確認 Python 版本（需 3.12）：

```powershell
python --version
```

安裝 Nuitka：

```powershell
pip install nuitka
python -m nuitka --version   # 確認可用
```

Nuitka 在 Windows 需要 C 編譯器（擇一）：

| 選項                                  | 安裝方式                                                                   |
| ------------------------------------- | -------------------------------------------------------------------------- |
| **Visual Studio Build Tools**（建議） | 下載 Visual Studio Build Tools，選「使用 C++ 的桌面開發」工作負載          |
| **MinGW-w64**                         | 至 winlibs.com 下載，將 `bin` 目錄加入系統 PATH，確認 `gcc --version` 可用 |

### 2. 執行打包指令 SOP

#### 方法 A：WSL2 打包（本機 Linux 環境）

安裝 WSL2 Ubuntu 22.04（若尚未安裝）：

```powershell
wsl --install -d Ubuntu-22.04
wsl --list --verbose   # 確認已安裝並為預設
```

進入 WSL2 並切換至原始碼目錄（WSL2 可直接存取 Windows 磁碟）：

```sh
wsl
cd /mnt/c/Users/Len/Documents/GitHub/nx_assistant/nx_aiagentapi
```

#### 方法 B：SSH 到 Ubuntu 伺服器編譯

從 Windows 上傳原始碼（PowerShell，排除 venv / buildenv / dist）：

```powershell
scp -r .\nx_aiagentapi user@10.90.1.47:/JQuan/nx_aiagentapi
```

若使用 rsync（需 WSL2 執行）：

```sh
rsync -av --exclude 'venv' --exclude 'buildenv' --exclude 'dist' \
  --exclude '__pycache__' --exclude 'test_*.py' \
  /mnt/c/Users/Len/Documents/GitHub/nx_assistant/nx_aiagentapi/ \
  user@10.90.1.47:/JQuan/nx_aiagentapi/
```

SSH 進入伺服器：

```powershell
ssh user@10.90.1.47
```

### 3. Ubuntu 可執行檔案（在 WSL2 或 SSH 環境執行）

以下步驟在 Ubuntu 環境（WSL2 終端或 SSH session）內執行，產出 Ubuntu 用的 `.so` 模組。

安裝編譯相依：

```sh
sudo apt install -y python3.12-dev build-essential patchelf
```

進入專案目錄：

```sh
cd /JQuan/nx_aiagentapi
```

建立 `.env`（若尚未存在，內容詳見「建立 .env 設定檔」一節）：

```sh
nano /JQuan/nx_aiagentapi/.env
```

建立執行用 venv：

```sh
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install uvicorn
deactivate
```

建立編譯用 venv 並安裝 Nuitka：

```sh
python3.12 -m venv /JQuan/nx_aiagentapi/buildenv
/JQuan/nx_aiagentapi/buildenv/bin/pip install --upgrade pip
/JQuan/nx_aiagentapi/buildenv/bin/pip install nuitka
/JQuan/nx_aiagentapi/buildenv/bin/python -m nuitka --version   # 確認可用
```

執行 Nuitka 打包（完整指令，產出 Ubuntu `.so`）：

> ⚠️ 同樣請整段存成腳本檔一次執行，不要逐行貼上（原因與注意事項見前一節「用 Nuitka 把原始碼編成 .so」）。

```sh
set -euo pipefail

BUILD=/JQuan/nx_aiagentapi/buildenv/bin/python
SRC=/JQuan/nx_aiagentapi
OUT=/JQuan/nx_aiagentapi/dist
COMMON="-m nuitka --module --remove-output --no-pyi-file"

# 建立輸出資料夾結構
mkdir -p $OUT \
  $OUT/config \
  $OUT/models \
  $OUT/routers/data_maintenance \
  $OUT/routers/repair_assistant \
  $OUT/schemas/data_maintenance \
  $OUT/schemas/rag \
  $OUT/schemas/repair_assistant \
  $OUT/services/data_maintenance \
  $OUT/services/gpu_client \
  $OUT/services/rag \
  $OUT/services/repair_assistant/first_repair_work/image_pdf \
  $OUT/services/repair_assistant/first_repair_work/text_pdf \
  $OUT/utils

# 進入點
$BUILD $COMMON --output-dir=$OUT $SRC/main.py

# config
$BUILD $COMMON --output-dir=$OUT/config $SRC/config/db_conf.py

# models
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/auth_models.py
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/generated_models.py
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/repair_models.py

# routers
$BUILD $COMMON --output-dir=$OUT/routers                  $SRC/routers/db_test.py
$BUILD $COMMON --output-dir=$OUT/routers/data_maintenance $SRC/routers/data_maintenance/board_document_upload_router.py
$BUILD $COMMON --output-dir=$OUT/routers/data_maintenance $SRC/routers/data_maintenance/repair_data_import_router.py
$BUILD $COMMON --output-dir=$OUT/routers/repair_assistant $SRC/routers/repair_assistant/first_repair_work_router.py

# schemas
$BUILD $COMMON --output-dir=$OUT/schemas/data_maintenance $SRC/schemas/data_maintenance/board_document_upload_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/data_maintenance $SRC/schemas/data_maintenance/repair_data_import_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/rag              $SRC/schemas/rag/rag_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/repair_assistant $SRC/schemas/repair_assistant/first_repair_work_schema.py

# services
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/board_document_upload_service.py
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/model_classification_query.py
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/repair_data_import_service.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/_auth.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/layout_client.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/vlm_client.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/chunk_service.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/embedding_service.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/repair_case_service.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant $SRC/services/repair_assistant/group_pdf_query.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/first_repair_work_query.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/first_repair_work_service.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/hotspot_result.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/pdf_type_detector.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work/image_pdf $SRC/services/repair_assistant/first_repair_work/image_pdf/image_pdf_hotspot_processor.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work/text_pdf  $SRC/services/repair_assistant/first_repair_work/text_pdf/text_pdf_hotspot_processor.py

# utils
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/exception.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/exception_handlers.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/logging_config.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/response.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/security.py

# 複製 __init__.py 與 .env，建立 storage symlink
cp $SRC/services/gpu_client/__init__.py $OUT/services/gpu_client/__init__.py
cp $SRC/services/repair_assistant/first_repair_work/image_pdf/__init__.py \
   $OUT/services/repair_assistant/first_repair_work/image_pdf/__init__.py
cp $SRC/.env $OUT/.env
ls -l $OUT/.env   # 確認檔案在、不是 0 bytes，否則啟動會噴 DATABASE_URL 未設定
mkdir -p /JQuan/nx_aiagentapi/storage
ln -sfn /JQuan/nx_aiagentapi/storage $OUT/storage
```

驗證 dist 沒有殘留原始碼：

```sh
find $OUT -name "*.py"   # 預期只列出兩個 __init__.py
```

### 4. 啟動服務

建立 systemd service：

```sh
sudo nano /etc/systemd/system/nx_aiagentapi.service
```

內容：

```ini
[Unit]
Description=NX AI Agent FastAPI
After=network.target

[Service]
WorkingDirectory=/JQuan/nx_aiagentapi/dist
ExecStart=/JQuan/nx_aiagentapi/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=10
User=www-data
SyslogIdentifier=nx_aiagentapi

[Install]
WantedBy=multi-user.target
```

> ⚠️ 啟動前務必把 `dist/` 擁有者改成 `www-data`（原因見「用 Nuitka 把原始碼編成 .so」一節的
> 同名警告：編譯／自測用一般帳號執行，`dist/` 檔案 owner 跟 `User=www-data` 不一致會導致
> `dist/logs/` 寫入被拒、服務起不來）：

```sh
sudo chown -R www-data:www-data /JQuan/nx_aiagentapi/dist
```

啟動服務：

```sh
sudo systemctl daemon-reload
sudo systemctl enable nx_aiagentapi
sudo systemctl start nx_aiagentapi
sudo systemctl status nx_aiagentapi
```

測試：

```sh
curl http://127.0.0.1:8001/docs
```

看 log：

```sh
sudo journalctl -u nx_aiagentapi -f
```

### 5. Nginx 部屬

> ⚠️ **先在 `http {}` context 加 WebSocket upgrade 對應（全站只需做一次，SignalR 需要）。**
> 下面 `/notificationHub/` 那段若把 `Connection` 寫死成固定字串 `"upgrade"`，會連同
> negotiate 完成後的實際連線請求（可能是一般 GET，不是真的要升級 WebSocket）一起被打上
> `Connection: upgrade`，導致後端 Kestrel 回 `400 Bad Request`。正確做法是依請求是否
> 真的帶 `Upgrade` header 動態決定：
>
> ```sh
> sudo nano /etc/nginx/nginx.conf
> ```
>
> 在 `http { ... }` 區塊內加入：
>
> ```nginx
> map $http_upgrade $connection_upgrade {
>     default upgrade;
>     ''      close;
> }
> ```
>
> 存檔後 `sudo nginx -t && sudo systemctl reload nginx`。下面 location 內的
> `proxy_set_header Connection` 一律改用 `$connection_upgrade`，不要寫死 `"upgrade"`。

> ⚠️ **先確認 `.mjs` 的 MIME type 有正確對應到 JavaScript（全站只需做一次）。**
> 前端瀏覽 PDF 線路圖用的 `pdfjs-dist` 會以 ES module 動態載入 `pdf.worker.min.mjs`；
> Nginx 預設 `/etc/nginx/mime.types` 常常沒把 `.mjs` 對應到 JS 類型，會 fallback 成
> `default_type application/octet-stream`，瀏覽器對 module script 做嚴格 MIME 檢查而拒絕載入，
> 導致「線路圖載入失敗」（console 會看到 `Failed to load module script ... MIME type of
"application/octet-stream"`）。修法：
>
> ```sh
> sudo nano /etc/nginx/mime.types
> ```
>
> 找到 `js;` 那一行，補上 `mjs`：
>
> ```
> application/javascript                           js mjs;
> ```
>
> 存檔後 `sudo nginx -t && sudo systemctl reload nginx`。

建立站台設定（3001 為對外入口）：

```sh
sudo nano /etc/nginx/sites-available/nx_assistant_web
```

內容：

```nginx
server {
    listen 3001 default_server;
    listen [::]:3001 default_server;
    server_name _;

    root /JQuan/nx_assistant_web/dist;
    index index.html;

    client_max_body_size 2000M;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5252/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 通知中心 SignalR Hub（CoreApi 掛在根路徑 /notificationHub，不在 /api/ 底下）
    # 需額外帶 Upgrade/Connection 才能升級成 WebSocket；SignalR 不同 transport 對同一個 hub
    # 用的路徑有沒有結尾斜線不一致（/notificationHub、/notificationHub/negotiate、
    # /notificationHub/?id=... 都會出現），location 不加結尾斜線才能全部匹配到，
    # proxy_pass 也不能帶路徑，否則 nginx 前綴改寫後的路徑會跟 Kestrel 實際註冊的
    # /notificationHub 對不上，導致 400。
    location /notificationHub {
        proxy_pass http://127.0.0.1:5252;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /data-maintenance/ {
        proxy_pass http://127.0.0.1:8001/data-maintenance/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /repair-assistant/ {
        proxy_pass http://127.0.0.1:8001/repair-assistant/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

啟用站台並重新載入（保留 Nginx 預設 80 埠站台，不刪除）：

```sh
sudo ln -s /etc/nginx/sites-available/nx_assistant_web /etc/nginx/sites-enabled/nx_assistant_web
sudo nginx -t
sudo systemctl reload nginx
```

開放防火牆：

```sh
sudo ufw allow 3001/tcp
sudo ufw status
```

## 安裝 PostgreSQL 及向量資料庫 (pgvector)

更新系統並安裝 PostgreSQL：

```sh
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

檢查 PostgreSQL 狀態：

```sh
sudo systemctl status postgresql
```

啟動 PostgreSQL：

```sh
sudo systemctl start postgresql
```

設定開機自動啟動：

```sh
sudo systemctl enable postgresql
```

確認版本（後續安裝 pgvector 會用到）：

```sh
psql --version
```

# 資料庫錯誤處理

檢查 port:

```sh
sudo ss -plnt | grep 5432
```

啟動 PostgreSQL cluster:

```sh
sudo pg_ctlcluster 16 main start
```

確認連線狀態:

```sh
pg_lsclusters
```

權限錯誤修正:

```sh
sudo chown -R postgres:postgres /var/lib/postgresql/16/main
sudo chmod 700 /var/lib/postgresql/16/main
```

### 安裝 pgvector 向量擴充套件

安裝對應 PostgreSQL 版本的 pgvector（將 `16` 換成實際版本號）：

```sh
sudo apt install -y postgresql-16-pgvector
```

如果套件庫沒有 pgvector，改用原始碼編譯安裝：

```sh
# 安裝編譯工具
sudo apt install -y build-essential git postgresql-server-dev-16

# 取得原始碼並編譯
cd /tmp
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 設定密碼並啟用 pgvector

切換到 postgres 系統帳號：

```sh
sudo -u postgres psql
```

設定 postgres 使用者密碼，並在 postgres 資料庫啟用 pgvector：

```sql
-- 設定 postgres 使用者密碼
ALTER USER postgres WITH PASSWORD 'St923420!';

-- 啟用 pgvector 擴充套件（預設連線的就是 postgres 資料庫）
CREATE EXTENSION IF NOT EXISTS vector;

-- 確認擴充套件已安裝
\dx

-- 離開
\q
```

### 修改使用者密碼

切換到 postgres 系統帳號進入 psql：

```sh
sudo -u postgres psql
```

修改 postgres 使用者密碼：

```sql
ALTER USER postgres WITH PASSWORD 'St923420!';
\q
```

或直接用單行指令修改（不需進入 psql）：

```sh
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'St923420!';"
```

### 驗證向量功能

以 postgres 使用者連線並測試（會要求輸入密碼 `St923420!`）：

```sh
psql -h 127.0.0.1 -U postgres -d postgres
```

在 psql 中測試向量型別：

```sql
-- 建立含向量欄位的測試表
CREATE TABLE items (
    id bigserial PRIMARY KEY,
    embedding vector(3)
);

-- 插入測試資料
INSERT INTO items (embedding) VALUES ('[1,2,3]'), ('[4,5,6]');

-- 以 L2 距離排序查詢
SELECT * FROM items ORDER BY embedding <-> '[3,1,2]' LIMIT 1;

-- 清除測試表
DROP TABLE items;
\q
```

### 安全性設定

PostgreSQL 只開放本機連線即可，不要對外開放 5432。
確認 `listen_addresses` 設定（檔案路徑依版本而定）：

```sh
sudo nano /etc/postgresql/16/main/postgresql.conf
```

確認以下設定為本機監聽：

```ini
listen_addresses = 'localhost'
```

修改後重啟服務：

```sh
sudo systemctl restart postgresql
```

確認防火牆未開放 5432：

```sh
sudo ufw status
```

### 設定 TCP/IP 連線（允許遠端連線）

> ⚠️ 預設建議只開放本機連線（見上節）。**僅在確實需要從其他主機連入時**才開放 TCP/IP，
> 並務必限制來源 IP、使用強密碼與 `scram-sha-256` 加密驗證，避免將 5432 直接曝露於公網。

PostgreSQL 開放網路連線需設定兩個檔案：`postgresql.conf`（監聽位址）與 `pg_hba.conf`（連線授權）。

#### 1. 設定監聽位址 (postgresql.conf)

```sh
sudo nano /etc/postgresql/16/main/postgresql.conf
```

將 `listen_addresses` 改為監聽所有網卡（或指定特定內網 IP）：

```ini
# 監聽全部網卡
listen_addresses = '*'

# 或只監聽特定內網位址（較安全）
# listen_addresses = 'localhost,192.168.1.10'

port = 5432
```

#### 2. 設定連線授權 (pg_hba.conf)

```sh
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

在檔案最後加入允許的來源網段（**務必限制 CIDR 範圍，勿用 `0.0.0.0/0`**），使用 `scram-sha-256` 加密驗證：

```conf
# TYPE  DATABASE  USER      ADDRESS           METHOD
host    all       all       192.168.1.0/24    scram-sha-256
```

> 欄位說明：來源限定 `192.168.1.0/24` 內網網段；`scram-sha-256` 為加密密碼驗證
> （需 PostgreSQL 預設 `password_encryption = scram-sha-256`，PG14+ 為預設值）。
>
> **`ADDRESS` 必須涵蓋用戶端實際 IP**，否則連線會出現
> `FATAL: no pg_hba.conf entry for host "x.x.x.x"`。
> 例如用戶端為 `10.90.1.47`，網段就要寫 `10.90.1.0/24`（請依實際網段調整）。

#### 3. 重啟（或重新載入）服務套用設定

只改 `pg_hba.conf` 時用 `reload` 即可（不中斷連線）；改了 `postgresql.conf` 的 `listen_addresses`／`port` 才需 `restart`：

```sh
sudo systemctl reload postgresql    # 只改 pg_hba.conf
sudo systemctl restart postgresql   # 改了 listen_addresses / port
```

確認 PostgreSQL 已監聽對外埠：

```sh
sudo ss -lntp | grep 5432
```

#### 4. 防火牆只放行指定來源

僅允許特定內網網段連入 5432，不對全網開放：

```sh
sudo ufw allow from 192.168.1.0/24 to any port 5432 proto tcp
sudo ufw status
```

#### 5. 從用戶端連線

在其他主機用 `psql` 連線（`10.90.1.47` 換成 Ubuntu 主機 IP，會要求輸入密碼）：

```sh
psql -h 10.90.1.47 -p 5432 -U postgres -d postgres
```

免互動輸入密碼（Linux / macOS 用 `PGPASSWORD`，僅限當前 session）：

```sh
PGPASSWORD='St923420!' psql -h 10.90.1.47 -p 5432 -U postgres -d postgres
```

應用程式連線字串（connection string）範例：

```text
postgresql://postgres:St923420!@10.90.1.47:5432/postgres
```

驗證連線是否成功：

```sh
psql -h 10.90.1.47 -p 5432 -U postgres -d postgres -c "SELECT version();"
```

## 資料庫備份及還原

> 本專案備份檔統一存放於 `/JQuan/backup`，目標資料庫為 `nx_assistant`。

### 備份 (pg_dump)

建立備份目錄：

```sh
sudo mkdir -p /JQuan/backup
sudo chown postgres:postgres /JQuan/backup
```

備份單一資料庫（自訂格式，含結構 + 資料，建議用於還原，可平行還原與選擇性還原）：

```sh
sudo -u postgres pg_dump -Fc -d nx_assistant -f /JQuan/backup/nx_assistant.dump
```

備份單一資料庫（純 SQL 文字格式，含結構 + 資料，可直接檢視）：

```sh
sudo -u postgres pg_dump -d nx_assistant -f /JQuan/backup/nx_assistant.sql
```

> 不加 `-s` / `-a` 時，`pg_dump` 預設即會同時備份「結構 + 資料」，為完整備份。

備份所有資料庫（含角色與權限）：

```sh
sudo -u postgres pg_dumpall -f /JQuan/backup/all.sql
```

只備份資料表結構（不含資料）：

```sh
sudo -u postgres pg_dump -s -d nx_assistant -f /JQuan/backup/nx_assistant_schema.sql
```

只備份資料（不含結構）：

```sh
sudo -u postgres pg_dump -a -d nx_assistant -f /JQuan/backup/nx_assistant_data.sql
```

### 還原 (pg_restore / psql)

還原前目標資料庫需已存在，若尚未建立先建立空白資料庫：

```sh
sudo -u postgres psql -c "CREATE DATABASE nx_assistant;"
```

還原自訂格式 `.dump`：

```sh
sudo -u postgres pg_restore -d nx_assistant /JQuan/backup/nx_assistant.dump
```

還原純 SQL 文字格式（`.sql`）：

```sh
sudo -u postgres psql -d nx_assistant -f /JQuan/backup/nx_assistant.sql
```

還原 pg_dumpall 備份（含所有資料庫與角色）：

```sh
sudo -u postgres psql -f /JQuan/backup/all.sql
```

若要乾淨還原，可在 pg_restore 加上 `--clean` 先清除現有物件再還原：

```sh
sudo -u postgres pg_restore --clean -d nx_assistant /JQuan/backup/nx_assistant.dump
```

還原後記得重新啟用 pgvector 擴充套件（若還原的是不含擴充的純資料）：

```sh
sudo -u postgres psql -d nx_assistant -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Windows 備份 → Ubuntu 還原

適用於將 Windows 上的 PostgreSQL 資料庫遷移到 Ubuntu 伺服器。

#### 在 Windows 端備份

先建立備份資料夾（PowerShell）：

```powershell
New-Item -ItemType Directory -Force C:\backup
```

開啟「PowerShell」，切換到 PostgreSQL 安裝路徑的 `bin` 目錄
（路徑與版本依實際安裝為準，例如 `C:\Program Files\PostgreSQL\18\bin`）。
注意：PowerShell 不會搜尋目前目錄，執行程式要加 `.\` 前綴：

```powershell
cd "C:\Program Files\PostgreSQL\18\bin"

.\pg_dump -U postgres -h 127.0.0.1 -Fc -d nx_assistant -f C:\backup\nx_assistant.dump
```

備份純 SQL 文字格式（含結構 + 資料，跨版本相容性較佳）：

```powershell
.\pg_dump -U postgres -h 127.0.0.1 -d nx_assistant -f C:\backup\nx_assistant.sql
```

> 以上指令未加 `-s` / `-a`，預設即為完整備份（結構 + 資料）。
> 若只要結構加 `-s`，只要資料加 `-a`。

或不切換目錄，直接用完整路徑搭配呼叫運算子 `&`：

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -h 127.0.0.1 -Fc -d nx_assistant -f C:\backup\nx_assistant.dump
```

> 執行時會要求輸入 postgres 密碼 `St923420!`。

#### 將備份檔上傳到 Ubuntu

在 Windows 端用 `scp` 上傳（或用 WinSCP、FileZilla 等工具）：

```bat
scp C:\backup\nx_assistant.dump user@10.90.1.47:/tmp/nx_assistant.dump
```

#### 在 Ubuntu 端還原

將檔案移到備份目錄並調整擁有者：

```sh
sudo mv /tmp/nx_assistant.dump /JQuan/backup/nx_assistant.dump
sudo chown postgres:postgres /JQuan/backup/nx_assistant.dump
```

若目標資料庫尚未建立，先建立空白資料庫：

```sh
sudo -u postgres psql -c "CREATE DATABASE nx_assistant;"
```

還原（自訂格式 `.dump`）：

```sh
sudo -u postgres pg_restore --clean -d nx_assistant /JQuan/backup/nx_assistant.dump
```

若為純 SQL 文字格式（`.sql`）：

```sh
sudo -u postgres psql -d nx_assistant -f /JQuan/backup/nx_assistant.sql
```

還原後重新啟用 pgvector 擴充套件並確認：

```sh
sudo -u postgres psql -d nx_assistant -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d nx_assistant -c "\dx"
```

> 注意：Windows 與 Ubuntu 的 PostgreSQL 大版本盡量一致（例如同為 16），
> 跨大版本還原時建議使用純 SQL 文字格式，相容性較佳。

### 使用 SSH / SFTP 傳輸 SQL 檔案

在不同主機間傳送 `.sql` / `.dump` 備份檔，可用 `scp`（單次複製）或 `sftp`（互動式）。
Ubuntu 端需先安裝並啟動 SSH 服務：

```sh
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh
```

> 若有啟用 UFW，需放行 SSH（預設 22 埠）：
>
> ```sh
> sudo ufw allow OpenSSH
> ```

#### 使用 scp 傳輸（單次複製）

從本機（Windows / 其他主機）**上傳**到 Ubuntu：

```sh
scp C:\backup\nx_assistant.sql user@10.90.1.47:/tmp/nx_assistant.sql
```

從 Ubuntu **下載**備份檔到本機：

```sh
scp user@10.90.1.47:/JQuan/backup/nx_assistant.sql C:\backup\nx_assistant.sql
```

在 Ubuntu 端**主動**從另一台主機抓取（拉取）SQL 檔：

```sh
scp user@other-host:/path/to/nx_assistant.sql /JQuan/backup/nx_assistant.sql
```

> 若 SSH 不是預設 22 埠，`scp` 用大寫 `-P` 指定埠號，例如 `scp -P 2222 ...`。
> 傳整個資料夾加 `-r`，例如 `scp -r ./backups user@10.90.1.47:/tmp/`。

#### 使用 sftp 傳輸（互動式）

連線到 Ubuntu：

```sh
sftp user@10.90.1.47
```

連線後常用指令（`l` 開頭為本機端，無 `l` 為遠端）：

```sh
pwd            # 顯示遠端目前目錄
lpwd           # 顯示本機目前目錄
cd /tmp        # 切換遠端目錄
lcd C:\backup  # 切換本機目錄
put nx_assistant.sql              # 上傳：本機 → 遠端
get /tmp/nx_assistant.sql         # 下載：遠端 → 本機
put -r dist                       # 上傳整個資料夾
bye            # 離開
```

> `sftp` 同樣可用 `-P` 指定非預設埠：`sftp -P 2222 user@10.90.1.47`。

#### 傳輸後在 Ubuntu 端還原

上傳到 `/tmp` 的檔案，移到備份目錄並調整擁有者後還原：

```sh
sudo mv /tmp/nx_assistant.sql /JQuan/backup/nx_assistant.sql
sudo chown postgres:postgres /JQuan/backup/nx_assistant.sql
sudo -u postgres psql -d nx_assistant -f /JQuan/backup/nx_assistant.sql
```

### 定時自動備份 (cron)

備份腳本存放於 `/JQuan/backup/backup_db.sh`，備份檔命名 `backupDB_年-月-日.sql`
（例如 `backupDB_2026-07-10.sql`），保留 30 天內的備份、超過 30 天自動刪除（循環覆蓋）。

建立備份腳本：

```sh
sudo nano /JQuan/backup/backup_db.sh
```

內容如下：

```sh
#!/bin/bash
set -euo pipefail

BACKUP_DIR=/JQuan/backup
DB_NAME=nx_assistant
RETENTION_DAYS=30

FILE="$BACKUP_DIR/backupDB_$(date +%Y-%m-%d).sql"

pg_dump -d "$DB_NAME" -f "$FILE"

find "$BACKUP_DIR" -name "backupDB_*.sql" -mtime +$RETENTION_DAYS -delete
```

賦予執行權限並設定擁有者（腳本由 postgres 使用者的 cron 執行，`pg_dump` 才能以
peer authentication 連上資料庫）：

```sh
sudo chmod +x /JQuan/backup/backup_db.sh
sudo chown postgres:postgres /JQuan/backup/backup_db.sh
```

手動執行一次自測：

```sh
sudo -u postgres /JQuan/backup/backup_db.sh
ls -l /JQuan/backup/backupDB_*.sql
```

編輯 postgres 使用者的排程：

```sh
sudo crontab -u postgres -e
```

加入以下這行，設定每天 01:00 執行（stdout/stderr 一併記到 log，方便排查失敗原因）：

```sh
0 1 * * * /JQuan/backup/backup_db.sh >> /JQuan/backup/backup_db.log 2>&1
```

確認 cron 服務開機自動啟動（Ubuntu 預設已啟用，仍建議確認一次）：

```sh
sudo systemctl enable cron
sudo systemctl status cron
```

確認排程已寫入：

```sh
sudo crontab -u postgres -l
```

## 更新部屬流程

更新前端

先備份舊檔案（`dist_日期`，與 `dist` 同層），再清空覆寫：

```sh
sudo cp -r /JQuan/nx_assistant_web/dist /JQuan/nx_assistant_web/dist_$(date +%Y-%m-%d)

sudo rm -rf /JQuan/nx_assistant_web/dist/*
sudo cp -r dist/* /JQuan/nx_assistant_web/dist/
sudo chown -R www-data:www-data /JQuan/nx_assistant_web/dist
sudo systemctl reload nginx
```

更新 .NET API

先備份舊檔案（`publish_日期`，與 `publish` 同層），再清空覆寫：

```sh
sudo systemctl stop nx_coreapi

sudo cp -r /JQuan/nx_coreapi/publish /JQuan/nx_coreapi/publish_$(date +%Y-%m-%d)

sudo rm -rf /JQuan/nx_coreapi/publish/*
sudo cp -r publish/* /JQuan/nx_coreapi/publish/
sudo chown -R www-data:www-data /JQuan/nx_coreapi/publish

sudo systemctl start nx_coreapi
sudo systemctl status nx_coreapi
```

更新 FastAPI（採 Nuitka 編譯版，更新程式碼須重新編譯 `.so`）

複製更新專案目錄:

```sh
cd /home/ai-assistant/nx_assistant
git pull
sudo cp -r nx_aiagentapi /JQuan/nx_aiagentapi
```

進入 FastAPI 專案目錄：

```sh
cd /JQuan/nx_aiagentapi
```

```sh
sudo nano /JQuan/nx_aiagentapi/.env
```

新增.env
把以下內容貼進去（資料庫指向本機 PostgreSQL，密碼／金鑰請依實際環境調整）：

```ini
DATABASE_URL=postgresql+asyncpg://postgres:St923420!@localhost:5432/nx_assistant
JWT_SIGN_KEY=NxAssistantJwtSignKey_2026_Development_Only_ChangeMe
JWT_ISSUER=NxAssistant
JWT_AUDIENCE=NxAssistantClient

# GPU 推論服務（AI server 10.30.2.200 經 nginx 轉發：11434->8100 DocLayout、11435->8200 VLM）
GPU_SERVICE_URL=http://10.30.2.200:11434
VLM_SERVICE_URL=http://10.30.2.200:11435
```

開始使用 Nuitka 封裝

```sh
sudo systemctl stop nx_aiagentapi

cd /JQuan/nx_aiagentapi

# 若 requirements.txt 有變動才需更新套件
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 重新編譯原始碼到 dist（完整指令清單見「用 Nuitka 把原始碼編成 .so」一節）
# 同樣請整段存成腳本檔一次執行，不要逐行貼上，否則變數宣告行漏貼會導致 $OUT 展開成空字串，
# --output-dir=$OUT/config 變成絕對路徑 /config，Nuitka 會因權限不足報 PermissionError
set -euo pipefail

BUILD=/JQuan/nx_aiagentapi/buildenv/bin/python
SRC=/JQuan/nx_aiagentapi
OUT=/JQuan/nx_aiagentapi/dist
COMMON="-m nuitka --module --remove-output --no-pyi-file"

# 備份舊 dist（dist_日期，與 dist 同層），再清空並重建資料夾結構
if [ -d $OUT ]; then
  cp -r $OUT ${OUT}_$(date +%Y-%m-%d)
fi
sudo rm -rf $OUT
mkdir -p $OUT \
  $OUT/config $OUT/models \
  $OUT/routers/data_maintenance $OUT/routers/repair_assistant \
  $OUT/schemas/data_maintenance $OUT/schemas/rag $OUT/schemas/repair_assistant \
  $OUT/services/data_maintenance $OUT/services/gpu_client $OUT/services/rag \
  $OUT/services/repair_assistant/first_repair_work/image_pdf \
  $OUT/services/repair_assistant/first_repair_work/text_pdf \
  $OUT/utils

# 進入點
$BUILD $COMMON --output-dir=$OUT $SRC/main.py
# config
$BUILD $COMMON --output-dir=$OUT/config $SRC/config/db_conf.py
# models
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/auth_models.py
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/generated_models.py
$BUILD $COMMON --output-dir=$OUT/models $SRC/models/repair_models.py
# routers
$BUILD $COMMON --output-dir=$OUT/routers                  $SRC/routers/db_test.py
$BUILD $COMMON --output-dir=$OUT/routers/data_maintenance $SRC/routers/data_maintenance/board_document_upload_router.py
$BUILD $COMMON --output-dir=$OUT/routers/data_maintenance $SRC/routers/data_maintenance/repair_data_import_router.py
$BUILD $COMMON --output-dir=$OUT/routers/repair_assistant $SRC/routers/repair_assistant/first_repair_work_router.py
# schemas
$BUILD $COMMON --output-dir=$OUT/schemas/data_maintenance $SRC/schemas/data_maintenance/board_document_upload_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/data_maintenance $SRC/schemas/data_maintenance/repair_data_import_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/rag              $SRC/schemas/rag/rag_schema.py
$BUILD $COMMON --output-dir=$OUT/schemas/repair_assistant $SRC/schemas/repair_assistant/first_repair_work_schema.py
# services
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/board_document_upload_service.py
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/model_classification_query.py
$BUILD $COMMON --output-dir=$OUT/services/data_maintenance $SRC/services/data_maintenance/repair_data_import_service.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/_auth.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/layout_client.py
$BUILD $COMMON --output-dir=$OUT/services/gpu_client       $SRC/services/gpu_client/vlm_client.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/chunk_service.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/embedding_service.py
$BUILD $COMMON --output-dir=$OUT/services/rag              $SRC/services/rag/repair_case_service.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant $SRC/services/repair_assistant/group_pdf_query.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/first_repair_work_query.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/first_repair_work_service.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/hotspot_result.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work       $SRC/services/repair_assistant/first_repair_work/pdf_type_detector.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work/image_pdf $SRC/services/repair_assistant/first_repair_work/image_pdf/image_pdf_hotspot_processor.py
$BUILD $COMMON --output-dir=$OUT/services/repair_assistant/first_repair_work/text_pdf  $SRC/services/repair_assistant/first_repair_work/text_pdf/text_pdf_hotspot_processor.py
# utils
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/exception.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/exception_handlers.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/logging_config.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/response.py
$BUILD $COMMON --output-dir=$OUT/utils $SRC/utils/security.py

# 複製空的 __init__.py 與 .env，並重建 storage symlink
cp $SRC/services/gpu_client/__init__.py $OUT/services/gpu_client/__init__.py 2>/dev/null || true
cp $SRC/services/repair_assistant/first_repair_work/image_pdf/__init__.py \
   $OUT/services/repair_assistant/first_repair_work/image_pdf/__init__.py 2>/dev/null || true
cp $SRC/.env $OUT/.env
ls -l $OUT/.env   # 確認檔案在、不是 0 bytes，否則啟動會噴 DATABASE_URL 未設定
ln -sfn /JQuan/nx_aiagentapi/storage $OUT/storage

sudo chown -R www-data:www-data /JQuan/nx_aiagentapi/dist

sudo systemctl start nx_aiagentapi
sudo systemctl status nx_aiagentapi
```

只改 `.env`（例如換資料庫密碼）不需重新編譯，更新後覆寫 `dist/.env` 再重啟即可：

```sh
nano /JQuan/nx_aiagentapi/.env
sudo cp /JQuan/nx_aiagentapi/.env /JQuan/nx_aiagentapi/dist/.env
sudo chown www-data :www-data /JQuan/nx_aiagentapi/dist/.env
sudo systemctl restart nx_aiagentapi
```

## 疑難排解

### 板件文件匯入一直失敗（正式路徑已有檔案）

**症狀**：`POST /data-maintenance/board-document-upload/import` 回應一律是 `201`，
但匯入結果 `status` 為 `failed` 或 `partial_failed`，`success_count` 為 0；
`GET /data-maintenance/board-document-upload` 查不到任何已匯入文件。

> `/import` 這支 API 設計上即使全部文件都沒匯入成功，HTTP 狀態碼仍回 `201`，
> 要看 Response Body 內的 `status`／`items[].message` 才知道實際有沒有成功。
> 若要回頭查歷史匯入紀錄，可在已登入系統的分頁用瀏覽器 Console 執行（自己的 token，安全）：
>
> ```js
> fetch("/data-maintenance/board-document-upload/batch?page=1&page_size=20", {
>   headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
> })
>   .then((r) => r.json())
>   .then((data) => console.log(JSON.stringify(data, null, 2)));
> ```

**根因**：`_save_document_item_async`（`services/data_maintenance/board_document_upload_service.py`）
在正式寫檔前，會先檢查正式路徑 `storage/repair_pdf/{group_code}/{model_part_no_pcb}_TOP-RD.pdf` 等
是否已存在檔案，存在就直接失敗回「正式路徑已有檔案」。若該路徑下已經有**與資料庫脫鉤的孤兒 PDF**
（例如手動搬移、舊流程留下、或測試殘留——資料庫裡完全沒有對應的 `b_repair_board_document` 紀錄），
就會形成死結：匯入永遠失敗，也永遠無法觸發「覆蓋匯入」邏輯去清掉舊檔（覆蓋判斷需要先在資料庫查到
既有紀錄）。

**確認方式**：檢查該機型資料夾底下實際檔案，跟 API 回應的 `model_part_no_pcb` 對照：

```sh
ls -la /JQuan/nx_aiagentapi/storage/repair_pdf/{group_code}/
```

若看到檔名對得上、但系統裡從未有任何一次成功匯入紀錄，即為孤兒檔案。

**處理方式**：先搬開（不要直接刪，以防萬一該檔案其實有其他用途），確認搬移對象後再重新匯入：

```sh
mkdir -p /JQuan/nx_aiagentapi/storage/repair_pdf_orphan_backup/{group_code}
mv /JQuan/nx_aiagentapi/storage/repair_pdf/{group_code}/{有問題的檔案}.pdf \
   /JQuan/nx_aiagentapi/storage/repair_pdf_orphan_backup/{group_code}/
```

> 這支 `cleanup_dirty_board_documents.py`（開發用一次性腳本，不需編譯部署）處理的是**另一種**情況：
> 資料庫裡已有紀錄、但 `model_part_no_pcb` 含非英數字元的髒資料，跟這裡「檔案孤兒、資料庫完全沒紀錄」
> 不是同一個問題，遇到孤兒檔案時這支腳本幫不上忙。

### 機型機種對照匯入 500：production 資料庫缺欄位（schema drift）

**症狀**：`POST /api/datamaintenance/modelpcbmapping/import` 回應 `500 Internal Server Error`。

**確認方式**：在服務器上執行後重現一次匯入動作：

```sh
sudo journalctl -u nx_coreapi -n 80 --no-pager
```

看到類似訊息即為此問題：

```text
Npgsql.PostgresException (0x80004005): 42703: column b.model_type does not exist
   at CoreApi.Services.DataMaintenance.ModelPcbMappingMaintenanceService.ImportWorkOrderAsync(IFormFile file)
```

**根因**：`repair.b_repair_model_board_document_map` 表的 `model_type` 欄位是 2026-06-29
commit `2d798850`（機型機種維護：匯入 BOM 品名建立機種分類）新增的功能，但當時只寫了
C# entity model（`Models/b_repair_model_board_document_map.cs`）與文件
（`analysis/資料庫/repair_table.md`），**從未產生對應的 SQL 腳本**去真的對資料庫下
`ALTER TABLE`。這個欄位應該只在開發環境手動用 psql 加過，production 從未同步執行，
才會在存取時噴 `column ... does not exist`。

> 本專案 Database First，資料表以資料庫為準，遇到這類「文件/程式碼定義了欄位、
> 但資料庫沒有」的落差，不可擅自執行 DDL，須先回報並等待使用者確認再處理。

**處理方式**：依 `analysis/資料庫/repair_table.md` 記載的定義補上欄位：

```sh
sudo -u postgres psql -d nx_assistant -c "
ALTER TABLE repair.b_repair_model_board_document_map
    ADD COLUMN IF NOT EXISTS model_type VARCHAR(100) DEFAULT NULL;
COMMENT ON COLUMN repair.b_repair_model_board_document_map.model_type IS
    '機型品名（匯入 BOM 單階材料用途明細一併帶入），例如 ASSY ICES-3610ME-nROK5300 SMD；供機種主檔同步作為機型／分類規則來源，純 BOM 板（未進維修歷史）才靠它分類';
"
```

執行完用 `\d repair.b_repair_model_board_document_map` 確認欄位已存在，再重新測試匯入功能。

> 這種「文件寫了欄位、卻沒留下可執行的 SQL 腳本」的模式容易重演，建議之後新增欄位時
> 順手在 `analysis/資料庫/` 對應文件旁一併留一份可重放的 `.sql`，並在部署到新環境時
> 核對開發環境與 production 資料庫結構是否一致。

## 最終架構

```sh
Browser
  |
  | http://10.90.1.47:3001
  |
Nginx nx_assistant_web
  |
  |-- /              -> /JQuan/nx_assistant_web/dist/index.html
  |
  |-- /api/          -> http://127.0.0.1:5252/api/
  |
  |-- /ai/           -> http://127.0.0.1:8001/
  |
  |-- PostgreSQL     -> 不對外，由後端自己連 127.0.0.1:5432
```
