# Windows 10 PostgreSQL 安裝與使用

## PostgreSQL 安裝步驟

### 下載安裝程式

至官方網站下載 Windows 版安裝程式（EDB 提供的安裝包）：

- 下載頁面：<https://www.postgresql.org/download/windows/>
- 或直接到 EDB：<https://www.enterprisedb.com/downloads/postgres-postgresql-downloads>

下載對應版本（例如 PostgreSQL 18）的 `.exe` 安裝檔。

### 執行安裝精靈

雙擊安裝檔，依精靈步驟設定：

1. **Installation Directory**：預設 `C:\Program Files\PostgreSQL\18`。
2. **Select Components**：勾選
   - PostgreSQL Server
   - pgAdmin 4（圖形管理工具）
   - Command Line Tools（`psql`、`pg_dump` 等指令）
   - Stack Builder（可選，用於安裝額外擴充）
3. **Data Directory**：預設 `C:\Program Files\PostgreSQL\18\data`。
4. **Password**：設定 `postgres` 超級使用者密碼，本專案統一使用 `St923420!`。
5. **Port**：預設 `5432`。
6. **Locale**：預設即可。

完成後安裝程式會註冊 Windows 服務 `postgresql-x64-18` 並設為開機自動啟動。

### 設定環境變數（讓 PowerShell 可直接呼叫 psql / pg_dump）

將安裝路徑的 `bin` 加入 `Path`（PowerShell，需以系統管理員身分執行）：

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\Program Files\PostgreSQL\18\bin",
    "Machine"
)
```

重新開啟 PowerShell 後驗證：

```powershell
psql --version
```

### 確認服務狀態

```powershell
Get-Service postgresql*
```

啟動 / 停止 / 重啟服務：

```powershell
Start-Service postgresql-x64-18
Stop-Service postgresql-x64-18
Restart-Service postgresql-x64-18
```

### 安裝 pgvector 向量擴充套件

本專案使用 pgvector。Windows 沒有官方安裝包，常見作法有兩種：**從原始碼編譯** 或 **使用預編譯檔案**。

#### 方法一：從原始碼編譯（官方建議）

需先安裝 **Visual Studio**，並務必勾選 **「使用 C++ 的桌面開發」(Desktop development with C++)** 工作負載；
此工作負載才會提供編譯所需的 `nmake` 與 MSVC 編譯器（若缺少會出現 `nmake : 無法辨識...` 錯誤）。

確認或補裝 C++ 工作負載（以系統管理員執行 PowerShell，`--installPath` 依實際安裝路徑調整）：

```powershell
# 用 vswhere 找出 VS 安裝路徑
$vswhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
$vsPath = & $vswhere -all -products Microsoft.VisualStudio.Product.Community -property installationPath

# 補裝 C++ 桌面開發工作負載
& "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" modify `
  --installPath $vsPath `
  --add Microsoft.VisualStudio.Workload.NativeDesktop --includeRecommended --norestart
```

在 PowerShell（以系統管理員執行）操作：

1. 先載入 x64 編譯環境（用 vswhere 動態尋找路徑，不需手動指定 VS 版本）：

```powershell
$vswhere = "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
$vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
& "$vsPath\Common7\Tools\Launch-VsDevShell.ps1" -Arch amd64 -HostArch amd64
```

> 載入成功後，執行 `Get-Command nmake` 應能找到 `nmake.exe`，再繼續下一步。

2. 設定 PostgreSQL 安裝路徑並編譯安裝：

```powershell
$env:PGROOT = "C:\Program Files\PostgreSQL\18"
Set-Location $env:TEMP
Remove-Item -Recurse -Force pgvector -ErrorAction SilentlyContinue
git clone --branch v0.8.3 https://github.com/pgvector/pgvector.git
Set-Location pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

> **版本務必對應 PostgreSQL 版本**：pgvector 自 **v0.8.1** 起才支援 PostgreSQL 18，
> 舊版（如 v0.8.0）在 PG18 編譯會出現 `error C2198: 'void vacuum_delay_point(bool)': 呼叫的引數太少`。
> PostgreSQL 18 請使用 **v0.8.1 以上**（本文件以最新穩定版 v0.8.3 為例）。
> 重新編譯前先刪除舊的 `pgvector` 目錄，避免殘留先前失敗的建置檔。

3. 編譯安裝成功後，重啟服務再啟用擴充：

```powershell
Restart-Service postgresql-x64-18
```

> `nmake install` 會將 `vector.dll` 複製到 `%PGROOT%\lib`，並把 `vector.control`
> 與 SQL 檔複製到 `%PGROOT%\share\extension`。需有該目錄寫入權限（以系統管理員執行）。

#### 方法二：使用預編譯檔案

若有對應 PostgreSQL 版本的預編譯檔（`vector.dll`、`vector.control`、`vector--*.sql`），
直接複製到以下位置即可，免編譯：

- `vector.dll` → `C:\Program Files\PostgreSQL\18\lib`
- `vector.control` 與 `vector--*.sql` → `C:\Program Files\PostgreSQL\18\share\extension`

複製後重啟服務：

```powershell
Restart-Service postgresql-x64-18
```

#### 啟用擴充

安裝完成後，在目標資料庫啟用擴充：

```powershell
psql -U postgres -h 127.0.0.1 -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

確認擴充已啟用：

```powershell
psql -U postgres -h 127.0.0.1 -d postgres -c "\dx"
```

## 連線資料庫

連線資訊：

| 項目   | 值               |
| ------ | ---------------- |
| 主機   | `220.135.135.29` |
| 連接埠 | `5432`           |
| 帳號   | `postgres`       |
| 密碼   | `St923420!`      |

用 `psql` 連線（執行後會要求輸入密碼 `St923420!`）：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres
```

> PowerShell 不會搜尋目前目錄，若未設定環境變數，需先切換到 `bin` 目錄並加 `.\` 前綴，
> 或用呼叫運算子 `&` 搭配完整路徑：
>
> ```powershell
> cd "C:\Program Files\PostgreSQL\18\bin"
> .\psql -h 220.135.135.29 -p 5432 -U postgres -d postgres
> ```

也可免互動輸入密碼，使用 `PGPASSWORD` 環境變數（僅限當前 session）：

```powershell
$env:PGPASSWORD = "St923420!"
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres
```

常用 psql 指令：

```sql
\l          -- 列出所有資料庫
\c dbname   -- 切換資料庫
\dn         -- 列出所有 schema
\dt         -- 列出目前 schema 的資料表
\dx         -- 列出已安裝擴充套件
\q          -- 離開
```

## 資料庫基本操作（新增 / 刪除資料庫）

以下指令在 PowerShell 執行，先設定密碼免互動輸入：

```powershell
$env:PGPASSWORD = "St923420!"
```

### 新增資料庫

建立資料庫（以 `mydb` 為例）：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "CREATE DATABASE mydb;"
```

建立資料庫並指定編碼與擁有者（可選）：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "CREATE DATABASE mydb WITH OWNER = postgres ENCODING = 'UTF8';"
```

確認資料庫已建立（列出所有資料庫）：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "\l"
```

### 刪除資料庫

刪除資料庫（以 `mydb` 為例，此操作無法復原，請先確認已備份）：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "DROP DATABASE mydb;"
```

若資料庫不存在時不報錯，加 `IF EXISTS`：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "DROP DATABASE IF EXISTS mydb;"
```

> 刪除時若出現 `database "mydb" is being accessed by other users`，表示仍有連線占用。
> PostgreSQL 13+ 可強制中斷現有連線後刪除：
>
> ```powershell
> psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "DROP DATABASE mydb WITH (FORCE);"
> ```
>
> 注意：不能刪除目前連線中的資料庫，需連到其他資料庫（如 `-d postgres`）再執行刪除。

## 資料庫備份還原指令

以下指令在 PowerShell 執行。若已設定環境變數可直接呼叫，否則切換到 `bin` 目錄並加 `.\` 前綴。

先建立備份資料夾：

```powershell
New-Item -ItemType Directory -Force C:\backup
```

### 備份 (pg_dump)

備份單一資料庫（自訂格式 `.dump`，含結構 + 資料，建議用於還原，可平行還原與選擇性還原）：

```powershell
pg_dump -h 220.135.135.29 -p 5432 -U postgres -Fc -d postgres -f C:\backup\postgres.dump
```

備份單一資料庫（純 SQL 文字格式，含結構 + 資料，可直接檢視、跨版本相容性較佳）：

```powershell
$env:PGPASSWORD = "St923420!"
pg_dump -h 220.135.135.29 -p 5432 -U postgres -d postgres -f C:\backup\postgres.sql
```

> 不加 `-s` / `-a` 時，`pg_dump` 預設即會同時備份「結構 + 資料」，為完整備份。
> 只要結構加 `-s`，只要資料加 `-a`。

備份所有資料庫（含角色與權限）：

```powershell
$env:PGPASSWORD = "St923420!"
pg_dumpall -h 220.135.135.29 -p 5432 -U postgres -f C:\backup\all.sql
```

#### 備份指定資料庫

將上述指令的 `-d postgres` 改為目標資料庫名稱即可（以下以 `mydb` 為例）。

備份指定資料庫（自訂格式 `.dump`，建議用於還原）：

```powershell
$env:PGPASSWORD = "St923420!"
pg_dump -h 220.135.135.29 -p 5432 -U postgres -Fc -d mydb -f C:\backup\mydb.dump
```

備份指定資料庫（純 SQL 文字格式）：

```powershell
$env:PGPASSWORD = "St923420!"
pg_dump -h 220.135.135.29 -p 5432 -U postgres -d mydb -f C:\backup\mydb.sql
```

> 還原指定資料庫前，目標資料庫需已存在；可先建立空白資料庫：
>
> ```powershell
> psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "CREATE DATABASE mydb;"
> ```
>
> 再以對應格式還原（`.dump` 用 `pg_restore -d mydb`、`.sql` 用 `psql -d mydb -f`）。

### 還原 (pg_restore / psql)

還原自訂格式 `.dump`（目標資料庫需已存在）：

```powershell
pg_restore -h 220.135.135.29 -p 5432 -U postgres -d postgres C:\backup\postgres.dump
```

若要乾淨還原，加 `--clean` 先清除現有物件再還原：

```powershell
pg_restore -h 220.135.135.29 -p 5432 -U postgres --clean -d postgres C:\backup\postgres.dump
```

還原純 SQL 文字格式 `.sql`：

```powershell
$env:PGPASSWORD = "St923420!"
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -f C:\backup\postgres.sql
```

還原 `pg_dumpall` 備份（含所有資料庫與角色）：

```powershell
$env:PGPASSWORD = "St923420!"
psql -h 220.135.135.29 -p 5432 -U postgres -f C:\backup\all.sql
```

還原後若使用 pgvector，重新啟用擴充套件：

```powershell
psql -h 220.135.135.29 -p 5432 -U postgres -d postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 備份指定 Schema 範例

只備份指定 schema（以 `public` 為例，`-n` 可指定多個）：
修改備份

```powershell
pg_dump -h 220.135.135.29 -p 5432 -U postgres -Fc -n public -d postgres -f C:\backup\postgres_public.dump
```

備份多個指定 schema：

```powershell
pg_dump -h 220.135.135.29 -p 5432 -U postgres -Fc -n public -n sales -d postgres -f C:\backup\postgres_schemas.dump
```

排除特定 schema（`-N`）：

```powershell
pg_dump -h 220.135.135.29 -p 5432 -U postgres -Fc -N temp -d postgres -f C:\backup\postgres_no_temp.dump
```

只備份指定 schema 的結構（不含資料，加 `-s`）：

```powershell
pg_dump -h 220.135.135.29 -p 5432 -U postgres -s -n public -d postgres -f C:\backup\public_schema.sql
```

還原指定 schema 的 `.dump`：

```powershell
pg_restore -h 220.135.135.29 -p 5432 -U postgres -n public -d postgres C:\backup\postgres_public.dump
```

> `-n schema` 可同時用於 `pg_dump`（備份）與 `pg_restore`（選擇性還原）。
> 還原前請確認目標 schema 不存在衝突物件，必要時搭配 `--clean`。
