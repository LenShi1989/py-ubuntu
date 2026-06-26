# 安裝及虛擬環境

```sh
py -0p                                  # 查看電腦裡Python所有版本
py -3.10 -m venv venv310                # 現有的 Python 版本Python 3.10建立環境
venv310\Scripts\activate                # 建立虛擬環境
python --version                        # 確定python安裝版本
python -m pip install --upgrade pip     # 升級pip
deactivate                              # 關閉虛擬環境
pip install -r requirements.txt         # 安裝txt裡面的所有套件
```
