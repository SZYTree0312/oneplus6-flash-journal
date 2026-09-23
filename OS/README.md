# OS 镜像包

本目录收录本次刷机**实际使用**的两个系统安装包（仅限该版本）。

> **为什么这里只有一个文件？**
> GitHub 单个文件上限 **100 MB**，Git LFS 免费额度也只有 1 GB。
> 所以只有 pmOS 的 boot 包（28 MB）能直接进仓库；899 MB 和 1.4 GB 两个包
> 改为记录**官方下载地址 + SHA256 校验值**，自行下载后核对即可 —— 镜像是官方发布的，
> 传一份到 GitHub 既没必要也放不下。

---

## 1. postmarketOS v26.06（gnome-mobile）— 最终放弃

| 文件 | 大小 | SHA256 |
|---|---|---|
| `20260911-0728-postmarketOS-v26.06-gnome-mobile-4-oneplus-enchilada-boot.img.xz` | 28 MB | `6f03fe8c99faa498f02245c4c390c084147f2142f57e03112c1b79b2b02c1ef7` |
| `20260911-0728-postmarketOS-v26.06-gnome-mobile-4-oneplus-enchilada.img.xz` | 899 MB | `56c372314ab197403d36928796f7999cc139bd56ac4cfe2dc8395aabb993087e` |

- 官方下载：<https://postmarketos.org/download/> → Device 选 **OnePlus 6 (`enchilada`)**，UI 选 **gnome-mobile**
- 28 MB 的 boot 包已入库：`postmarketos/` 目录
- 解压产物：
  - `pmos-enchilada-boot.img` —— 28 MB，raw ANDR boot image
  - `pmos-enchilada-rootfs.img` —— 2.2 GB，**Android sparse image**（magic `3aff26ed`），展开 3.24 GiB
- **放弃原因**：底层 Alpine + **musl libc**，编译器与原生构建兼容性差（典型症状：连 `zh_CN` locale 都要手工造）

## 2. Mobian 13.0（Phosh）— 最终方案

| 文件 | 大小 | SHA256 |
|---|---|---|
| `mobian-sdm845-phosh-13.0.tar.xz` | 1.4 GB | `32236dc00d75be10f6cb8077138305174452d9f129dc595b89f9df0d36b678f0` |

- 官方下载：<https://images.mobian.org/qcom/weekly/>（旧 `sdm845` 路径仍会重定向到 `qcom`）
- 包内是 **5 个机型的 boot + 1 个共用 rootfs**，一加6 只需要这两个：
  - `mobian-sdm845-phosh-20251002.boot-enchilada.img` —— 29,798,400 B，magic `ANDROID!`
  - `mobian-sdm845-phosh-20251002.rootfs.img` —— 4,221,440,856 B，Android sparse

---

## 校验

下载完先核对再刷，别拿坏镜像去写分区：

```bash
sha256sum -c <<'EOF'
6f03fe8c99faa498f02245c4c390c084147f2142f57e03112c1b79b2b02c1ef7 *20260911-0728-postmarketOS-v26.06-gnome-mobile-4-oneplus-enchilada-boot.img.xz
56c372314ab197403d36928796f7999cc139bd56ac4cfe2dc8395aabb993087e *20260911-0728-postmarketOS-v26.06-gnome-mobile-4-oneplus-enchilada.img.xz
32236dc00d75be10f6cb8077138305174452d9f129dc595b89f9df0d36b678f0 *mobian-sdm845-phosh-13.0.tar.xz
EOF
```

## 解压

Windows 上通常没装 xz / 7z，用仓库里的 `scripts/extract-images.py`（纯 Python 标准库，零依赖）：

```bash
python scripts/extract-images.py pmos      # 解 postmarketOS 的 boot + rootfs
python scripts/extract-images.py mobian    # 解 Mobian tar.xz（只解一加6 需要的两个，别全解）
```

脚本解压完会打印每个镜像的 magic 头，顺手确认一下：
boot 应是 `ANDROID!`，rootfs 应是 Android sparse（`3aff26ed`）。
