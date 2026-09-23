#!/usr/bin/env bash
# 刷 Mobian 到 一加6 (OnePlus 6 / enchilada)，slot A
# 用法：先把手机切到 fastboot 模式并连好线，再执行本脚本
#   手机进 fastboot：关机后按住【音量上 + 电源】不放，出现绿色 START 即到
set -e

PT="C:/Users/DELL/Downloads/Compressed/platform-tools-latest-windows/platform-tools"
IMG="C:/Users/DELL/Downloads/mobian-flash"
FB="$PT/fastboot.exe"
BOOT="$IMG/mobian-sdm845-phosh-20251002.boot-enchilada.img"
ROOTFS="$IMG/mobian-sdm845-phosh-20251002.rootfs.img"

echo "== 当前 fastboot 设备 =="
"$FB" devices

echo "== 1/6 选择 slot A =="
"$FB" --set-active=a

echo "== 2/6 刷 boot (enchilada) =="
"$FB" flash boot "$BOOT"

echo "== 3/6 擦除 userdata (会清空手机数据) =="
"$FB" erase userdata

echo "== 4/6 刷 rootfs (4.2G sparse, 100M 分块) =="
"$FB" -S 100M flash userdata "$ROOTFS"

echo "== 5/6 擦除 dtbo =="
"$FB" erase dtbo

echo "== 6/6 重启进系统 =="
"$FB" reboot

echo "全部完成。首次开机 Mobian 会扩展文件系统，可能等 5-10 分钟。登录 mobian / <Mobian默认密码>"
