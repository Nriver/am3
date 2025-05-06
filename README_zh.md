# am3

AM3 = Application Manager written with python 3

[English](README.md) | 中文

一个用于管理和监控应用程序的命令行工具。

## 🦮 目录

<!--ts-->
* [am3](#am3)
   * [🦮 目录](#-目录)
   * [🔧 安装](#-安装)
   * [📖 基本用法](#-基本用法)
      * [列出应用](#列出应用)
      * [启动应用](#启动应用)
      * [停止应用](#停止应用)
      * [重启应用](#重启应用)
      * [删除应用](#删除应用)
      * [查看日志](#查看日志)
      * [保存和加载应用列表](#保存和加载应用列表)
   * [⚙️ 高级功能](#️-高级功能)
      * [配置文件](#配置文件)
      * [自动重启](#自动重启)
      * [API服务](#api服务)
      * [开机自启动](#开机自启动)
   * [🔄 命令参考](#-命令参考)
      * [全局命令](#全局命令)
      * [应用管理命令](#应用管理命令)
      * [API服务命令](#api服务命令)
* [🙏 致谢](#-致谢)
<!--te-->


## 🔧 安装

需要 Python 3，大多数现代 Linux 发行版都应该可用。

使用以下命令安装 am3：

```bash
pip install am3
```

安装后，您可以使用 `am` 或 `am3` 命令。

---

## 📖 基本用法

### 列出应用

获取并显示有关运行中应用程序的信息，包括名称、ID 和其他详细信息。

```bash
am list
# 或使用简写
am ls
```

显示更详细的信息：

```bash
am list --all
```

---

### 启动应用

有多种方式启动应用：

**1. 通过应用 ID 启动已注册的应用**

```bash
am start 0
```

**2. 启动新应用**

```bash
am start --start "ping" --params "127.0.0.1"
```

**3. 使用配置文件启动应用**

```bash
am start --conf example/counter_config.json
```

**4. 启动所有应用**

```bash
am start all
```

**启动选项说明：**

- `--start` 或 `-s`: 指定启动路径
- `--interpreter` 或 `-i`: 指定解释器路径
- `--working-directory` 或 `-d`: 指定工作目录
- `--params` 或 `-p`: 指定命令参数
- `--name` 或 `-n`: 指定应用名称
- `--restart-control/--no-restart-control`: 是否控制程序的重启

---

### 停止应用

通过 ID 停止运行中的应用：

```bash
am stop 0
```

停止所有应用：

```bash
am stop all
```

---

### 重启应用

重启指定 ID 的应用：

```bash
am restart 0
```

重启所有应用：

```bash
am restart all
```

---

### 删除应用

从管理列表中删除应用：

```bash
am delete 0
```

删除所有应用（会提示确认）：

```bash
am delete all
```

---

### 查看日志

查看 AM3 自身的日志：

```bash
am log
```

查看指定应用的日志：

```bash
am log 0
```

持续查看日志（类似 `tail -f`）：

```bash
am log 0 --follow
```

指定显示的行数：

```bash
am log 0 --lines 100
```

---

### 保存和加载应用列表

保存当前应用列表配置：

```bash
am save
```

从保存的配置加载应用列表：

```bash
am load
```

---

## ⚙️ 高级功能

### 配置文件

您可以将应用配置保存到文件中，以便重复使用：

```bash
am start --start example/counter.py --interpreter python3 --generate example/counter_config.json
```

然后使用配置文件启动应用：

```bash
am start --conf example/counter_config.json
```

### 自动重启

AM3 支持基于关键字或正则表达式的自动重启功能：

```bash
am start --start example/counter.py --restart-keyword "Exception" --restart-keyword-regex "Error.*"
```

设置重启等待时间：

```bash
am start --start example/counter.py --restart-wait-time 3
```

### API服务

初始化 API 服务：

```bash
am api init
```

启动 API 服务：

```bash
am api start
```

停止 API 服务：

```bash
am api stop
```

### 开机自启动

设置 AM3 开机自启动：

```bash
am startup
```

---

## 🔄 命令参考

### 全局命令

- `am --version`: 显示版本信息
- `am --help`: 显示帮助信息

### 应用管理命令

- `am list`: 列出应用
- `am start`: 启动应用
- `am stop`: 停止应用
- `am restart`: 重启应用
- `am delete`: 删除应用
- `am log`: 查看日志
- `am save`: 保存应用列表
- `am load`: 加载应用列表
- `am startup`: 设置开机自启动

### API服务命令

- `am api init`: 初始化 API 服务
- `am api start`: 启动 API 服务
- `am api stop`: 停止 API 服务

---

# 🙏 致谢

感谢 Jetbrains 提供的优秀 IDE Pycharm。

[![Jetbrains](docs/jetbrains.svg)](https://jb.gg/OpenSource)
