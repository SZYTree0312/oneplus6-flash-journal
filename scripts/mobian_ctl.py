#!/usr/bin/env python3
"""mobian_ctl.py - 远程执行 Mobian（一加6）命令

用法:
  python mobian_ctl.py --file <命令文件>  [--idle 15] [--max-wait 900]
  python mobian_ctl.py --cmd "id"        [--idle 8]  [--max-wait 120]

说明:
  - 命令文件每行一条命令，全部在 **sudo -i 的 root shell** 里顺序执行（自动输入 sudo 密码，无需逐条 sudo）
  - 必须 invoke_shell(pty)，exec_command 输不了 sudo 密码
  - apt 这类慢命令要把 --idle / --max-wait 调大
"""
import argparse, time, socket, sys, re

ap = argparse.ArgumentParser()
ap.add_argument('--host', default='<内网IP>')
ap.add_argument('--user', default='mobian')
ap.add_argument('--password', default='')
ap.add_argument('--cmd', help='单条命令')
ap.add_argument('--file', help='命令文件，每行一条')
ap.add_argument('--idle', type=float, default=15.0, help='无输出持续多少秒判定该命令结束')
ap.add_argument('--max-wait', type=float, default=900.0, help='全部命令总超时')
ap.add_argument('--tries', type=int, default=3, help='连接重试次数')
ap.add_argument('--connect-timeout', type=float, default=45.0, help='单次连接超时秒数')
ap.add_argument('--retry-wait', type=float, default=3.0, help='重试间隔秒数')
a = ap.parse_args()

if not a.cmd and not a.file:
    ap.error('需要 --cmd 或 --file')

cmds = []
if a.file:
    with open(a.file, encoding='utf-8') as f:
        cmds = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
else:
    cmds = [a.cmd]

import paramiko

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ok = False
for attempt in range(a.tries):
    try:
        cli.connect(a.host, username=a.user, password=a.password,
                    timeout=a.connect_timeout, look_for_keys=False, allow_agent=False)
        ok = True
        break
    except Exception as e:
        print('[连接失败 %d/%d] %s' % (attempt + 1, a.tries, e))
        if attempt + 1 < a.tries:
            time.sleep(a.retry_wait)
if not ok:
    print('连不上，放弃')
    sys.exit(1)

ch = cli.invoke_shell(width=200, height=60)
ch.settimeout(0.3)


def pump(wait_sec=0.0):
    """读取当前可读的输出"""
    data = b''
    end = time.time() + wait_sec
    while True:
        try:
            d = ch.recv(65536)
        except socket.timeout:
            break
        except Exception:
            break
        if not d:
            break
        data += d
        if time.time() > end:
            break
    return data


def wait_for(pattern, timeout=20.0):
    """等待输出中出现 pattern（正则），返回累计字节"""
    acc = b''
    end = time.time() + timeout
    while time.time() < end:
        d = pump(0.2)
        if d:
            acc += d
            if re.search(pattern, acc.decode('utf-8', 'replace')):
                return acc
        time.sleep(0.1)
    return acc


time.sleep(0.6)
pump()  # 丢弃登录 banner

# ---- 提权到 root ----
ch.send('sudo -i\n')
time.sleep(1.0)
pump()
ch.send(a.password + '\n')
time.sleep(1.5)
pump()

ch.send('echo ROOTOK id=$(id -u)\n')
check = wait_for(r'ROOTOK id=0', timeout=25.0)
if not re.search(r'ROOTOK id=0', check.decode('utf-8', 'replace')):
    print('[!!] 提权失败，以下是实际输出：')
    print(check.decode('utf-8', 'replace'))
    cli.close()
    sys.exit(1)

# 关闭终端回显：否则输入的命令行会被 pty 回显，导致哨兵被"回显"提前匹配
ch.send('stty -echo\n')
time.sleep(0.3)
pump()

# 免除 apt 交互询问
ch.send('export DEBIAN_FRONTEND=noninteractive\n')
time.sleep(0.3)
pump()

# ---- 顺序执行 ----
started_all = time.time()
for idx, cmd in enumerate(cmds, 1):
    print(f'\n===== [{idx}/{len(cmds)}] $ {cmd} =====', flush=True)
    sentinel = f'__MBDONE{idx}_{int(time.time())}__'
    ch.send(cmd + '\n')
    time.sleep(0.15)
    out = pump()          # 注意：这里要保留输出，不能丢弃
    ch.send(f'echo {sentinel}\n')
    last = time.time()
    while True:
        d = pump(0.3)
        if d:
            out += d
            last = time.time()
            if sentinel.encode() in out:
                break
        else:
            if time.time() - last > a.idle:
                print('[... 超时退出等待，命令可能仍在后台跑]', flush=True)
                break
        if time.time() - started_all > a.max_wait:
            print('[... 总超时]', flush=True)
            break

    txt = out.decode('utf-8', 'replace')
    txt = txt.replace(f'echo {sentinel}', '')
    txt = txt.replace(sentinel, '')
    sys.stdout.write(txt)
    sys.stdout.flush()

print('\n===== 全部执行完毕 =====')
cli.close()
