# am3

AM3 = Application Manager written with python 3

## 🔧 Installation

Python3 is required, which should be available on most of the modern Linux distributions.

Install am3 with this command:

```bash
pip install am3
```

Then you can use it with `am` or `am3`.

## 📖 (Basic) Usage

### List applications

List application info. Include the application name, id, etc.

```bash
am3 ls
```

### Start an application

You can specify command and the params.

```bash
am --start "ping" --params "127.0.0.1 -c 5"
```

By default am3 will automatically restart the application if it exits.

There will be an id assigned to the application. You can interact with the application by this id.

### Stop an application

Stop

```bash
am stop 0
```

# 🙏 Thanks

Thanks for the great IDE Pycharm from Jetbrains.

[![Jetbrains](docs/jetbrains.svg)](https://jb.gg/OpenSource)
