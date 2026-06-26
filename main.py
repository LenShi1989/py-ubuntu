import ntplib
from datetime import datetime, timezone

c = ntplib.NTPClient()
response = c.request('pool.ntp.org', version=3)
ntp_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
print("NTP 時間:", ntp_time.strftime('%Y-%m-%d %H:%M:%S UTC'))
