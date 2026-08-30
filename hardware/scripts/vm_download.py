import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("localhost", port=2222, username="bearpi", password="bearpi",
            timeout=15, banner_timeout=15, auth_timeout=15,
            allow_agent=False, look_for_keys=False)

sftp = ssh.open_sftp()
remote = "/home/bearpi/project/bearpi-hm_nano/out/BearPi-HM_Nano/Hi3861_wifiiot_app_allinone.bin"
local = r"D:\bearpi\firmware\Hi3861_wifiiot_app_allinone.bin"
sftp.get(remote, local)
sftp.close()
ssh.close()

import hashlib, os
h = hashlib.md5(open(local, "rb").read()).hexdigest()
print("downloaded", local)
print("size:", os.path.getsize(local))
print("md5 :", h)
