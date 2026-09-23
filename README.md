# 一加6 (enchilada / sdm845) 刷 Linux 实录

把一台一加6 从氢OS 刷成真正可用的 Linux 小机器 —— 解锁 bootloader → postmarketOS → 改刷 Mobian（Debian ARM64），含全部踩坑与修复。

## 结论先说

- 一加6 成功解锁 bootloader，刷入 Linux，**可正常开机使用**
- 先上 **postmarketOS v26.06**（Alpine / musl），后因 musl 原生构建兼容性差，**改刷 Mobian**（Debian 13 trixie / ARM64 / glibc）
- 现状：Mobian + Phosh，中文环境、apt 国内源、sshd、编译工具链全部就位

## 设备

| 项 | 值 |
|---|---|
| 机型 | 一加6（OnePlus 6），codename `enchilada` |
| SoC | Qualcomm `sdm845` |
| 分区 | A/B 双槽（当前 active = a） |
| 原始系统 | HydrogenOS 10.0.11（国行氢OS，Android 10） |
| 解锁后 | `unlocked: yes`，`verifiedbootstate = orange` |

---

## 一、解锁 bootloader

`fastboot flashing unlock` 返回 **`Flashing Unlock is not allowed`** 时，原因只有一个：开发者选项里的 **「OEM 解锁」开关没开**。这个开关**只能在安卓系统里打开**，进了 fastboot 就没有补救机会了。

```bash
adb shell am start -a com.android.settings.APPLICATION_DEVELOPMENT_SETTINGS   # 把设置页推到手机屏幕
# → 手动勾选「OEM 解锁」
adb reboot bootloader
fastboot flashing unlock       # 返回 OKAY，此时手机屏幕出现确认页
# → 手机上：音量键选 UNLOCK THE BOOTLOADER，电源键确认
```

**坑**：命令返回 OKAY 时解锁**还没完成**，必须等人在手机上按键确认。确认后手机自动清空数据并重启，3–5 分钟内 adb/fastboot 都看不到设备 —— 属正常，轮询等待，别拔线、别重启。

验证：`fastboot getvar unlocked` → `yes`

---

## 二、postmarketOS v26.06（已放弃，但过程有价值）

### 镜像

Windows 上通常没装 xz/7z，直接用 Python 解：

```python
import lzma, shutil
with lzma.open(SRC_XZ, 'rb') as fi, open(DST_IMG, 'wb') as fo:
    shutil.copyfileobj(fi, fo, 1024*1024)
```

- `pmos-enchilada-boot.img` 28 MB，raw ANDR boot image
- `pmos-enchilada-rootfs.img` 2.2 GB，**Android sparse image**（magic `3aff26ed`），展开 3.24 GiB，fastboot 原生支持

### 刷入

```bash
fastboot erase dtbo
fastboot flash boot     pmos-enchilada-boot.img
fastboot flash userdata pmos-enchilada-rootfs.img
fastboot reboot
```

实测耗时：`erase dtbo` 0.004s / `flash boot` 1.086s / `flash userdata` 约 100s。

- `Warning: skip copying userdata image avb footer due to sparse image` 是**正常提示，不是错误**
- **不要用电源键重启**，一律 `fastboot reboot`

### 验证

`ping 172.16.42.1` 通（TTL=64）—— 这是 pmOS 的 USB gadget 默认地址，安卓不会配它，能 ping 通就说明内核和用户空间都起来了。

**sshd 默认不开**（22 端口 Connection refused 是预期行为，不是刷坏了）。需在手机终端执行：

```bash
sudo systemctl start sshd      # pmOS 这台是 systemd，不是 OpenRC
sudo systemctl enable sshd
```

### 为什么放弃 pmOS

底层 Alpine + **musl libc**，编译器和原生构建兼容性差。最典型的是中文 locale：

- Alpine 用 musl，不走 glibc 的 `locale.gen`
- `musl-locales` 包只带 16 个欧洲语言，**没有中文**
- 直接 `localectl set-locale zh_CN.UTF-8` 会报 `Locale zh_CN.UTF-8 not installed, refusing`

当时的土办法：装 `gettext`，用 `en_US.mo` 反编译出 po，改 43 条（日期格式 / 12 个月份 / 7 个星期 / AM-PM），再 `msgfmt` 编回 `zh_CN.UTF-8` 装进 musl locales 目录。能用，但这套 hack 本身就说明 musl 不适合当主力开发环境。

---

## 三、Mobian（最终方案）

Mobian = 纯 Debian ARM64 + glibc，apt / 工具链 / 行为与桌面 Debian 完全一致，编译原生软件零摩擦。

### 镜像

`mobian-sdm845-phosh-13.0.tar.xz`（1.4 GB），包内 5 个机型 boot + 1 个共用 rootfs：

- 一加6 用 `mobian-sdm845-phosh-20251002.boot-enchilada.img`（29,798,400 B，magic `ANDROID!`）
- `mobian-sdm845-phosh-20251002.rootfs.img`（4,221,440,856 B，magic `3aff26ed`，Android sparse）

### 刷入（slot A）

```bash
fastboot --set-active=a
fastboot flash boot     mobian-...-phosh-20251002.boot-enchilada.img
fastboot erase userdata
fastboot -S 100M flash userdata mobian-...-phosh-20251002.rootfs.img
fastboot erase dtbo
fastboot reboot
```

- rootfs 分 41 段 sparse，耗时 264.6s
- `fastboot erase userdata` 提示 "Did you mean to format this ext4?" 属正常（上一版 pmOS 残留的 ext4）
- bootloader 早在 pmOS 那次就解锁了，本次无需再解锁；**vendor 分区未动**，原厂 Wi-Fi / modem 固件仍在，Mobian 直接复用

### A/B 槽保护

装完要把 active slot 的 retry 计数重置为 7，否则每次启动递减到 0 会拒启动。
**实测 qbootctl 0.2.2-1 已预装且 enabled**，这个坑不存在。

### 系统配置

- Debian GNU/Linux 13 (trixie)，aarch64，glibc，rootfs 226 GB
- apt 换 **USTC** 源（合肥本地，实测 4 MB/s）；`repo.mobian.org` 国内连不上，改名 `mobian.sources.disabled` 停用（原文件保留，可还原）
- 中文：glibc 下就是一句话的事 —— `apt install locales` → `locale-gen zh_CN.UTF-8` → `update-locale`。pmOS 那套 .mo hack 完全不需要
- 装了 130 个包：build-essential / gcc 14.2 / g++ / cmake 3.31 / gdb / git、Noto CJK + 文泉驿、firefox-esr-l10n-zh-cn
- `localectl set-locale` 报 "Access denied"（shell 不在 systemd 会话总线）→ 直接写 `/etc/default/locale`、`/etc/locale.conf`、`/etc/environment` 绕开

---

## 四、踩坑清单（最有价值的部分）

| # | 坑 | 正解 |
|---|---|---|
| 1 | 把 `ro.build.display.id` 的 `A6000_22` 当成 OxygenOS 11 | 看 **`persist.sys.version.ota`**（`OnePlus6Hydrogen_...`）和 `ro.rom.version`，这台实际是氢OS 10.0.11 |
| 2 | `fastboot flashing unlock` 被拒 | 只能在系统里开「OEM 解锁」，与用 `oem unlock` 还是 `flashing unlock` 无关 |
| 3 | 刷官方 OxygenOS 底包 | **会把 bootloader 重新锁回去**，别刷 |
| 4 | sparse 镜像的 avb footer 警告 | 正常提示，不是错误 |
| 5 | 用电源键重启 | 一律 `fastboot reboot` |
| 6 | pmOS 上用 `rc-service` / `service` | 这台 pmOS 是 **systemd**，用 `systemctl` |
| 7 | USB gadget `172.16.42.1` 息屏即断 | 长期通道走 **Wi-Fi**，USB 不可靠 |
| 8 | `localectl` 报 Access denied | 直接写 locale 配置文件 |
| 9 | **`apt purge` 不杀正在运行的守护进程** | 卸载完必须再 `kill -9`，否则进程还占着资源 |

---

## 五、事故：fcitx5 顶掉屏幕键盘（本次最折腾的一个）

### 现象

重启后**锁屏能输密码，但桌面所有文本框（含终端）都输不了字**。

### 根因

Phosh 0.46 的屏幕键盘是 **`phosh-osk-stub`**（不是 squeekboard，后者根本没装也不用装），以 `--allow-replacement` 运行。
fcitx5 作为 Wayland input-method 客户端把 osk-stub **顶替掉**，但 fcitx5 只提供输入法引擎、**不画屏幕键盘** → 没有任何键盘 UI。

**判别特征**：锁屏界面用自己的键盘、不走 input-method 协议，所以「锁屏能输、桌面不能输」就是输入法被抢占的典型症状。

### 修复

```bash
dpkg --configure -a                      # 先修被中断的 dpkg
apt --fix-broken install -y              # 再修 libfdisk1 依赖断裂
apt purge -y $(dpkg -l | awk '/fcitx|libime/{print $2}')
apt autoremove -y --purge                # 共清掉 35 + 27 个包
kill -9 <fcitx5_pid>                     # 卸载不杀进程，这步必须补
pkill -f phosh-osk-stub                  # Phosh 会自动重新拉起一个干净的
```

结果：`fcitx` 包数 0，`/usr/bin/fcitx5` 不存在，osk-stub 重新接管，键盘恢复。

**教训**：Phosh/Wayland 下别照搬桌面 Linux 那套 `GTK_IM_MODULE=fcitx` + fcitx5 autostart。触屏中文输入在 Phosh 46 上仍是痛点 —— fcitx5 只在有**物理键盘**（蓝牙 / OTG）时才安全。

---

## 六、解决息屏断 Wi-Fi

手机息屏就断 Wi-Fi，导致 SSH 只能在亮屏那几秒的窗口里抢着连。解决：

```bash
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
printf '[connection]\nwifi.powersave = 2\n' > /etc/NetworkManager/conf.d/wifi-powersave-off.conf
```

现在息屏后 Wi-Fi 不再断，SSH 随时可连。

---

## 七、远程控制工具

`mobian_ctl.py` —— paramiko 远程执行器，自动应答 sudo 密码。

```bash
python mobian_ctl.py --host <内网IP> --password <Mobian默认密码> --file step.txt
python mobian_ctl.py --host <内网IP> --cmd "uname -a"
```

两个关键坑：

1. 必须 `invoke_shell`（pty），`exec_command` 喂不了 sudo 密码
2. 拿到 root 后要 `stty -echo`，否则 pty 回显的命令行会让结束哨兵被提前匹配（踩过，导致 apt 被误判结束）

常用参数：`--idle`（无输出多少秒判定该命令结束）、`--max-wait`（总超时）、`--tries` / `--connect-timeout` / `--retry-wait`（连接重试）。

---

## 八、刷机脚本

`scripts/` 下的脚本全部基于 **Google 官方 Android SDK platform-tools**（adb / fastboot）：

- `unlock-bootloader.sh` —— 解锁 bootloader，含手机端手动确认的步骤提示
- `flash-mobian.sh` —— 刷 Mobian（slot A，最终方案）
- `flash-pmos.sh` —— 刷 postmarketOS（过程存档）
- `extract-images.py` —— 解压镜像（Windows 没装 xz / 7z 时用，纯标准库，零依赖）

系统镜像均为官方发布包（899 MB / 1.4 GB），**不收录进仓库** —— 单文件已超 GitHub 100 MB 上限，且官方源随时可下。下载地址见上文第一、三节。

## 当前状态

- ✅ Mobian + Phosh 正常运行，解锁 → 开机 → 桌面完整可用
- ✅ 中文界面与 locale，时区 Asia/Shanghai
- ✅ apt 国内源（USTC），sshd enabled + active
- ✅ 编译工具链（gcc 14.2 / g++ / cmake / gdb / git）
- ✅ 息屏不再断网，SSH 稳定
- ⚠️ 触屏中文拼音输入暂缺（fcitx5 会抢键盘，已卸）

## 待办

1. 改掉默认密码 `<Mobian默认密码>`
2. 触屏中文输入方案待定（接物理键盘时可重新装 fcitx5，但要把自启隔离好）
