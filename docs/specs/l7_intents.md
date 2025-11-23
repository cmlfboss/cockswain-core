# L7 Intent 對照表 (v0.2)

本文件定義第七層（L7）目前允許調度的意圖（intent），對應的腳本路徑、可接受的參數，以及是否需要上層審核。  
所有未在此清單中的 intent，L7 一律以 `noop` 回應，並於 action log 中記錄，供後續擴充。

## 1. 通用規格

- L7 從決策物件中取得欄位：
  - `intent`: 要執行的意圖名稱（必填）
  - `params`: 參數字典，會被轉成環境變數 `L7_ARG_<KEY>` 傳入腳本（選填）
- 腳本放置位置：`/srv/cockswain-core/scripts/`
- 行為日誌位置：`/srv/cockswain-core/logs/actions/`
- 反射日誌位置：`/srv/cockswain-core/logs/reflection/`

## 2. Intent 白名單

### 2.1 `record_progress`
- 目的：記錄建設/系統當前時間點
- 腳本：`/srv/cockswain-core/scripts/record_progress.sh`
- 參數：無
- 審核：`requires_approval: false`

### 2.2 `check_node_state`
- 目的：檢查母機/核心服務是否在線
- 腳本：`/srv/cockswain-core/scripts/health_check.sh`
- 參數：
  - `service` (選填)：要檢查的服務名稱，預設為 `cockswain-core.service`
- 審核：`requires_approval: false`

### 2.3 `core_status`
- 目的：取得核心狀態但不嘗試啟動
- 腳本：`/srv/cockswain-core/scripts/core_status.sh`
- 參數：無
- 審核：`requires_approval: false`

### 2.4 `sync_docs`
- 目的：同步/重建文件索引
- 腳本：`/srv/cockswain-core/scripts/reindex_docs.sh`
- 參數：
  - `mode`: `full` | `fast` （預設 `full`）
  - `source`: `specs` | `wiki` | `all` （預設 `specs`）
- 審核：`requires_approval: false`

### 2.5 `start_core`
- 目的：啟動/重啟核心服務
- 腳本：`/srv/cockswain-core/scripts/start_core.sh`
- 參數：無
- 審核：`requires_approval: true`
- 備註：目前腳本為「失敗也 exit 0」，請以 stdout 為準

## 3. 未註冊意圖
- 行為：回傳 `noop`
- 用途：記錄前端/其他層級丟上來但尚未實作的指令，作為下次擴充的依據

## 4. 版本
- v0.1：初版，僅動作說明
- v0.2：加入參數與審核欄位（本文件）
