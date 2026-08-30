import paramiko
import hashlib

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("localhost", port=2222, username="bearpi", password="bearpi",
            timeout=15, banner_timeout=15, auth_timeout=15,
            allow_agent=False, look_for_keys=False)

BASE = "/home/bearpi/project/bearpi-hm_nano/applications/BearPi/BearPi-HM_Nano/sample/E_farm_mqtt"
LOCAL_FILES = [
    (r"C:\Users\王小丫\Desktop\软件实训\数据模拟\farm_mqtt.c", f"{BASE}/farm_mqtt.c"),
    (r"C:\Users\王小丫\Desktop\软件实训\数据模拟\wifi_connect.c", f"{BASE}/src/wifi_connect.c"),
]

def run(cmd, t=600):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=t)
    return stdout.read().decode("utf-8", "replace") + stderr.read().decode("utf-8", "replace")

# 1) upload both
sftp = ssh.open_sftp()
for local, remote in LOCAL_FILES:
    sftp.put(local, remote)
    print(f"uploaded {remote}", flush=True)
sftp.close()

# 2) verify md5 match
for local, remote in LOCAL_FILES:
    loc_md5 = hashlib.md5(open(local, "rb").read()).hexdigest()
    rem_md5 = run(f"md5sum {remote}").split()[0]
    print(remote.split("/")[-1], "md5 match:", loc_md5 == rem_md5, flush=True)

# 3) build
build = 'export PATH=/home/bearpi/.local/bin:/home/bearpi/.hpm/global/gcc_riscv32/bin:$PATH && cd /home/bearpi/project/bearpi-hm_nano && python build.py BearPi-HM_Nano'
out = run(build)
print(out[-2500:], flush=True)

print("BIN:", run("ls -la /home/bearpi/project/bearpi-hm_nano/out/BearPi-HM_Nano/Hi3861_wifiiot_app_allinone.bin"), flush=True)

ssh.close()
print("=== build2 done ===", flush=True)
