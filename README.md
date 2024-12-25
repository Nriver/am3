# am3

AM3 = Application Manager written with python 3


## 🦮 Table of Contents

<!--ts-->
* [am3](#am3)
   * [🦮 Table of Contents](#-table-of-contents)
   * [🔧 Installation](#-installation)
   * [📖 (Basic) Usage](#-basic-usage)
      * [List Applications](#list-applications)
      * [Start an Application](#start-an-application)
         * [Specify the main script or file](#specify-the-main-script-or-file)
         * [Specify a custom interpreter](#specify-a-custom-interpreter)
         * [Start executable files directly](#start-executable-files-directly)
      * [Stop an Application](#stop-an-application)
   * [⚙️ Advanced Parameters](#️-advanced-parameters)
      * [Generate Configuration](#generate-configuration)
      * [Load Configuration](#load-configuration)
      * [Restart Keywords](#restart-keywords)
      * [Set Working Directory](#set-working-directory)
      * [Set Restart Delay](#set-restart-delay)
      * [Use Regular Expressions for Restart Keywords](#use-regular-expressions-for-restart-keywords)
      * [Restart Check Delay](#restart-check-delay)
      * [Pre-Execution Environment Check](#pre-execution-environment-check)
      * [Assign Application Name](#assign-application-name)
* [🙏 Thanks](#-thanks)
<!--te-->


## 🔧 Installation

Python3 is required, which should be available on most of the modern Linux distributions.

Install am3 with this command:

```bash
pip install am3
```

Then you can use it with `am` or `am3`.

---

## 📖 (Basic) Usage

### List Applications

Retrieve and display information about running applications, including their name, ID, and other details.

```bash
am3 ls
```

---

### Start an Application

Launch an application by specifying a command and parameters:

```bash
am --start "ping" --params "127.0.0.1 -c 5"
```

By default, **am3** will automatically restart the application if it exits unexpectedly. Each application is assigned a
unique ID, which can be used to manage or interact with the application.

#### Specify the main script or file

Use the `-s` option to specify the main script or file. If the script is a Python file, the Python interpreter is
automatically invoked. Similarly, shell scripts are executed using Bash. This behavior is defined in the
`guess_interpreter` function.

```bash
am -s example/counter.py
```

#### Specify a custom interpreter

If needed, you can explicitly define the interpreter using the `-i` option:

```bash
am -s example/counter.py -i python3
```

#### Start executable files directly

If you’re running the executable in the current directory, use:

```bash
./am -s example/counter.py -i python3
```

Alternatively, you can use symbolic links for starting executables:

```bash
am -s example/counter.py
```

---

### Stop an Application

Terminate a running application by using its ID:

```bash
am stop 0
```

---

## ⚙️ Advanced Parameters

### Generate Configuration

You can save the configuration for reuse with the `-g` option:

```bash
am -s example/counter.py -i python3 -g example/counter_config.json
```

### Load Configuration

To reuse a previously saved configuration file, use:

```bash
am -c example/counter_config.json
```

### Restart Keywords

Define specific keywords that trigger automatic restarts if they appear in the application output:

```bash
am -s example/counter.py -i python3 --restart_keyword "Exception XXX" "Exception YYY" -g example/counter_config.json
```

### Set Working Directory

Specify the working directory for the application:

```bash
am -s counter.py -i python3 --restart_keyword "Exception XXX" "Exception YYY" -d "/home/nate/gitRepo/am3/example/" -g example/counter_config.json
```

### Set Restart Delay

Define a delay (in seconds) before restarting the application:

```bash
am -s counter.py -i python3 --restart_keyword "Exception XXX" "Exception YYY" -d "/home/nate/gitRepo/am3/example/" -t 3 -g example/counter_config.json
```

### Use Regular Expressions for Restart Keywords

Specify regular expressions as restart keywords for more flexible matching:

```bash
am -s counter.py -i python3  --restart_keyword "Exception XXX" --restart_keyword "Exception YYY" \
  --restart_keyword_regex "| 0.00 |" --restart_keyword_regex "2\\d\\.\\d\\d KB/s" \
  -d "/home/nate/gitRepo/am3/example/" -t 3 -g example/counter_config.json
```

### Restart Check Delay

Set a delay for how often to check if the application should restart:

```bash
am -s counter.py -i python3 --restart_check_delay 0 --restart_keyword "Exception XXX" \
  --restart_keyword "Exception YYY" --restart_keyword_regex "| 0.00 |" \
  --restart_keyword_regex "2\\d\\.\\d\\d KB/s" \
  -d "/home/nate/gitRepo/am3/example/" -t 3 -g example/counter_config.json
```

### Pre-Execution Environment Check

Run a pre-check script to validate the environment before executing the main application. The script's `check` function
is automatically called every second until it returns `True`.

```bash
am -s counter.py -i python3 --restart_check_delay 0 --restart_keyword "Exception XXX" \
  --restart_keyword "Exception YYY" --restart_keyword_regex "| 0.00 |" \
  --restart_keyword_regex "2\\d\\.\\d\\d KB/s" -d "/home/nate/gitRepo/am3/example/" \
  -t 3 -b "example/counter_before_execute.py" -g example/counter_config.json
```

### Assign Application Name

You can specify a custom name for the application:

```bash
am -s counter.py -i python3 --restart_check_delay 0 --restart_keyword "Exception XXX" \
  --restart_keyword "Exception YYY" --restart_keyword_regex "| 0.00 |" \
  --restart_keyword_regex "2\\d\\.\\d\\d KB/s" -d "/home/nate/gitRepo/am3/example/" \
  -t 3 -b "example/counter_before_execute.py" --name counter -g example/counter_config.json
```

--- 

# 🙏 Thanks

Thanks for the great IDE Pycharm from Jetbrains.

[![Jetbrains](docs/jetbrains.svg)](https://jb.gg/OpenSource)
