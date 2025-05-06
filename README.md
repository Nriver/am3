# am3

AM3 = Application Manager written with python 3

English | [中文](README_zh.md)

A command-line tool for managing and monitoring applications.

## 🦮 Table of Contents

<!--ts-->
* [am3](#am3)
   * [🦮 Table of Contents](#-table-of-contents)
   * [🔧 Installation](#-installation)
   * [📖 Basic Usage](#-basic-usage)
      * [List Applications](#list-applications)
      * [Start an Application](#start-an-application)
      * [Stop an Application](#stop-an-application)
      * [Restart an Application](#restart-an-application)
      * [Delete an Application](#delete-an-application)
      * [View Logs](#view-logs)
      * [Save and Load Application List](#save-and-load-application-list)
   * [⚙️ Advanced Features](#️-advanced-features)
      * [Configuration Files](#configuration-files)
      * [Auto Restart](#auto-restart)
      * [API Service](#api-service)
      * [Startup on Boot](#startup-on-boot)
   * [🔄 Command Reference](#-command-reference)
      * [Global Commands](#global-commands)
      * [Application Management Commands](#application-management-commands)
      * [API Service Commands](#api-service-commands)
* [🙏 Acknowledgements](#-acknowledgements)
<!--te-->


## 🔧 Installation

Python 3 is required, which should be available on most modern Linux distributions.

Install am3 with this command:

```bash
pip install am3
```

After installation, you can use either the `am` or `am3` command.

---

## 📖 Basic Usage

### List Applications

Retrieve and display information about running applications, including their name, ID, and other details.

```bash
am list
# or use the shorthand
am ls
```

Display more detailed information:

```bash
am list --all
```

---

### Start an Application

There are multiple ways to start an application:

**1. Start a registered application by ID**

```bash
am start 0
```

**2. Start a new application**

```bash
am start --start "ping" --params "127.0.0.1"
```

**3. Start using a configuration file**

```bash
am start --conf example/counter_config.json
```

**4. Start all applications**

```bash
am start all
```

**Start options:**

- `--start` or `-s`: Specify the target path
- `--interpreter` or `-i`: Specify the interpreter path
- `--working-directory` or `-d`: Specify the working directory
- `--params` or `-p`: Specify command parameters
- `--name` or `-n`: Specify application name
- `--restart-control/--no-restart-control`: Control whether to restart the program

---

### Stop an Application

Stop a running application by ID:

```bash
am stop 0
```

Stop all applications:

```bash
am stop all
```

---

### Restart an Application

Restart a specific application by ID:

```bash
am restart 0
```

Restart all applications:

```bash
am restart all
```

---

### Delete an Application

Remove an application from the management list:

```bash
am delete 0
```

Delete all applications (will prompt for confirmation):

```bash
am delete all
```

---

### View Logs

View AM3's own logs:

```bash
am log
```

View logs for a specific application:

```bash
am log 0
```

Continuously view logs (similar to `tail -f`):

```bash
am log 0 --follow
```

Specify the number of lines to display:

```bash
am log 0 --lines 100
```

---

### Save and Load Application List

Save the current application list configuration:

```bash
am save
```

Load application list from saved configuration:

```bash
am load
```

---

## ⚙️ Advanced Features

### Configuration Files

You can save application configurations to a file for reuse:

```bash
am start --start example/counter.py --interpreter python3 --generate example/counter_config.json
```

Then start the application using the configuration file:

```bash
am start --conf example/counter_config.json
```

### Auto Restart

AM3 supports automatic restart based on keywords or regular expressions:

```bash
am start --start example/counter.py --restart-keyword "Exception" --restart-keyword-regex "Error.*"
```

Set restart wait time:

```bash
am start --start example/counter.py --restart-wait-time 3
```

### API Service

Initialize the API service:

```bash
am api init
```

Start the API service:

```bash
am api start
```

Stop the API service:

```bash
am api stop
```

### Startup on Boot

Set AM3 to start on system boot:

```bash
am startup
```

---

## 🔄 Command Reference

### Global Commands

- `am --version`: Display version information
- `am --help`: Display help information

### Application Management Commands

- `am list`: List applications
- `am start`: Start an application
- `am stop`: Stop an application
- `am restart`: Restart an application
- `am delete`: Delete an application
- `am log`: View logs
- `am save`: Save application list
- `am load`: Load application list
- `am startup`: Set startup on boot

### API Service Commands

- `am api init`: Initialize API service
- `am api start`: Start API service
- `am api stop`: Stop API service

---

# 🙏 Acknowledgements

Thanks for the great IDE Pycharm from Jetbrains.

[![Jetbrains](docs/jetbrains.svg)](https://jb.gg/OpenSource)
