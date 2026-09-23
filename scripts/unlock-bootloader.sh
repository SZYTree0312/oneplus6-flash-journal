#!/usr/bin/env bash
# 解锁 一加6 (OnePlus 6 / enchilada) 的 bootloader
#
# 警告：解锁会清空手机全部数据，且不可逆。
# 工具：Google 官方 Android SDK platform-tools（adb / fastboot）
#
# 用法：手机开机进系统、USB 调试已打开、连好线，然后执行本脚本
set -e

PT="C:/Users/<用户名>/Downloads/Compressed/platform-tools-latest-windows/platform-tools"
ADB="$PT/adb.exe"
FB="$PT/fastboot.exe"

echo "== 1/4 把开发者选项页面推到手机屏幕 =="
"$ADB" shell am start -a com.android.settings.APPLICATION_DEVELOPMENT_SETTINGS
echo
echo ">>> 在手机上：找到「OEM 解锁」并勾选"
echo ">>> （这一步只能在系统里做，进了 fastboot 就没机会了）"
read -p ">>> 勾好后按回车继续..."

echo
echo "== 2/4 重启进 fastboot =="
"$ADB" reboot bootloader
sleep 15
"$FB" devices

echo
echo "== 3/4 发送解锁命令 =="
"$FB" flashing unlock
echo
echo ">>> 命令返回 OKAY 不代表解锁完成！"
echo ">>> 手机屏幕上会出现确认页：音量键选 UNLOCK THE BOOTLOADER，电源键确认"
read -p ">>> 确认后手机会自动清空数据并重启。等屏幕亮起后按回车..."

echo
echo "== 4/4 验证 =="
"$FB" getvar unlocked 2>&1 | grep -i unlocked
echo
echo "看到 unlocked: yes 即成功。之后 3-5 分钟内 adb/fastboot 可能看不到设备，属正常，等即可。"
