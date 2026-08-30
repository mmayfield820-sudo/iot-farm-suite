import paramiko

HOST = "localhost"
PORT = 2222
USER = "bearpi"
PWD = "bearpi"
LOCAL = r"C:\Users\王小丫\Desktop\软件实训\数据模拟\farm_mqtt.c"
REMOTE = "/home/bearpi/project/bearpi-hm_nano/applications/BearPi/BearPi-HM_Nano/sample/E_farm_mqtt/farm_mqtt.c"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PWD,
            timeout=15, banner_timeout=15, auth_timeout=15,
            allow_agent=False, look_for_keys=False)

# 1) upload
sftp = ssh.open_sftp()
sftp.put(LOCAL, REMOTE)
sftp.close()
print("uploaded OK", flush=True)

# 2) verify checksum
def run(cmd, t=600):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=t)
    return stdout.read().decode("utf-8", "replace") + stderr.read().decode("utf-8", "replace")

print("remote wc:", run("wc -l %s && md5sum %s" % (REMOTE, REMOTE)), flush=True)
import hashlib
md5 = hashlib.md5(open(LOCAL, "rb").read()).hexdigest()
print("local md5:", md5, flush=True)
print("check:", run("md5sum %s" % REMOTE).split()[0] == md5 and "MATCH" or "MISMATCH", flush=True)

# 3) build
build = 'export PATH=/home/bearpi/.local/bin:/home/bearpi/.hpm/global/gcc_riscv32/bin:$PATH && cd /home/bearpi/project/bearpi-hm_nano && python build.py BearPi-HM_Nano'
out = run(build)
print(out[-3000:], flush=True)

# 4) locate bin
print("BIN:", run("ls -la /home/bearpi/project/bearpi-hm_nano/out/BearPi-HM_Nano/Hi3861_wifiiot_app_allinone.bin"), flush=True)

ssh.close()
print("=== build script done ===", flush=True)
