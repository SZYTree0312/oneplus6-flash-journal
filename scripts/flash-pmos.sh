#!/usr/bin/env bash
# 刷 postmarketOS v26.06 (gnome-mobile) 到 一加6 (enchilada)
#
# 说明：本项目最终方案是 Mobian，pmOS 因 musl libc 兼容性问题已放弃，
#       本脚本作过程存档保留，供参考。
# 前置：bootloader 已解锁（见 unlock-bootloader.sh）
# 工具：Google 官方 Android SDK platform-tools（fastboot）
set -e

PT="C:/Users/DELL/Downloads/Compressed/platform-tools-latest-windows/platform-tools"
IMG="C:/Users/DELL/Downloads/pmos-flash"
FB="$PT/fastboot.exe"
BOOT="$IMG/pmos-enchilada-boot.img"
ROOTFS="$IMG/pmos-enchilada-rootfs.img"

echo "== 当前 fastboot 设备 =="
"$FB" devices

echo "== 1/4 擦除 dtbo =="
echo "   注意：这会让当前槽上原有的安卓彻底无法启动（含 TWRP / Ubuntu Touch）"
"$FB" erase dtbo

echo "== 2/4 刷 boot（28MB，raw ANDR boot image）=="
"$FB" flash boot "$BOOT"

echo "== 3/4 刷 rootfs（2.2G，Android sparse，fastboot 原生支持，约 100s）=="
echo "   提示 skip copying userdata image avb footer due to sparse image 属正常"
"$FB" flash userdata "$ROOTFS"

echo "== 4/4 重启 =="
echo "   务必用 fastboot reboot，不要按电源键"
"$FB" reboot

echo
echo "验证：ping 172.16.42.1 —— pmOS 的 USB gadget 默认地址，通了就说明起来了"
echo "sshd 默认不开，需在手机终端执行：sudo systemctl start sshd && sudo systemctl enable sshd"
