#!/usr/bin/env python3
"""解压刷机镜像

Windows 上通常没装 xz / 7z，用 Python 标准库解决，无需额外依赖。

用法:
  python extract-images.py pmos     # 解 postmarketOS 的 boot + rootfs
  python extract-images.py mobian   # 解 Mobian 的 tar.xz（只解一加6 需要的两个文件）
"""
import os
import sys
import lzma
import shutil
import tarfile

BASE = r'C:\Users\<用户名>\Downloads'


def unxz(src, dst):
    """解 .xz 单文件镜像"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print('解压 %s -> %s' % (os.path.basename(src), dst))
    with lzma.open(src, 'rb') as fi, open(dst, 'wb') as fo:
        shutil.copyfileobj(fi, fo, 1024 * 1024)
    print('  完成：%d bytes' % os.path.getsize(dst))


def untarxz(src, outdir, wanted):
    """从 tar.xz 里只解需要的文件（包内有 5 个机型 boot，全解浪费时间）"""
    os.makedirs(outdir, exist_ok=True)
    print('解压 %s -> %s' % (os.path.basename(src), outdir))
    with tarfile.open(src, 'r:xz') as t:
        for m in t.getmembers():
            if any(w in m.name for w in wanted):
                print('  解出 %s' % m.name)
                t.extract(m, outdir)
    print('  完成')


def magic_head(path, n=8):
    with open(path, 'rb') as f:
        return f.read(n)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''

    if mode == 'pmos':
        src_dir = os.path.join(BASE)
        out = os.path.join(BASE, 'pmos-flash')
        unxz(os.path.join(src_dir, '20260911-0728-postmarketOS-v26.06-gnome-mobile-4-oneplus-enchilada-boot.img.xz'),
             os.path.join(out, 'pmos-enchilada-boot.img'))
        unxz(os.path.join(src_dir, '20260911-0728-postmarketOS-v26.06-gnome-mobile-4-oneplus-enchilada.img.xz'),
             os.path.join(out, 'pmos-enchilada-rootfs.img'))

    elif mode == 'mobian':
        untarxz(os.path.join(BASE, 'mobian-sdm845-phosh-13.0.tar.xz'),
                os.path.join(BASE, 'mobian-flash'),
                wanted=['boot-enchilada.img', 'rootfs.img'])

    else:
        print(__doc__)
        sys.exit(1)

    # 校验 magic：boot 应为 ANDROID!，rootfs 应为 Android sparse (3aff26ed)
    print()
    for p in [os.path.join(BASE, 'pmos-flash', 'pmos-enchilada-boot.img'),
              os.path.join(BASE, 'pmos-flash', 'pmos-enchilada-rootfs.img'),
              os.path.join(BASE, 'mobian-flash', 'mobian-sdm845-phosh-20251002.boot-enchilada.img'),
              os.path.join(BASE, 'mobian-flash', 'mobian-sdm845-phosh-20251002.rootfs.img')]:
        if os.path.exists(p):
            print('%s -> %r' % (os.path.basename(p), magic_head(p)))
