# wxdf.py

`wxdf.py` 是一个用于 wxWidgets 项目的命令行工具：创建项目骨架、调用 CMake 构建、运行和调试程序。

当前版本：**0.06**

## 安装

```bash
chmod +x wxdf.py                       # 赋予执行权限
./wxdf.py --help                        # 直接使用
ln -s "$(pwd)/wxdf.py" ~/.local/bin/wxdf.py   # （可选）放入 PATH 后可直接 wxdf.py ...
```

## 环境要求

- Python 3
- CMake（>= 3.10）
- C++ 编译器（默认使用 C++17）
- wxWidgets 开发库（`core`、`base` 组件）
- gdb（`debug` 命令需要）

## 用法

```bash
wxdf.py <command> [options]
```

查看帮助：

```bash
wxdf.py --help
wxdf.py build --help
```

### create-project

```bash
wxdf.py create-project <project-name>
```

在当前目录下创建项目目录 `<project-name>/`，并生成如下结构与文件：

```text
<project-name>/
├── build
├── CMakeLists.txt
└── src
    ├── CMakeLists.txt
    ├── frame
    │   ├── CMakeLists.txt
    │   ├── MainFrame.cpp
    │   └── MainFrame.h
    └── main.cpp
```

- 根 `CMakeLists.txt`：声明项目（`project(<project-name> VERSION 1.0.0 LANGUAGES CXX)`）、C++17、可执行文件输出到 `${CMAKE_BINARY_DIR}/bin`、查找 wxWidgets 的 `core` 与 `base` 组件。
- `src/CMakeLists.txt`：收集源文件、链接 wxWidgets 库、设置头文件搜索路径与编译宏。
- `src/frame/CMakeLists.txt`：把 `MainFrame.cpp/.h` 与其所在目录通过 `PARENT_SCOPE` 暴露给上层。
- `src/frame/MainFrame.h/.cpp`：`frame` 命名空间下的 `MainFrame`（继承 `wxFrame`）骨架。
- `src/main.cpp`：以项目名命名的 `wxApp` 子类与 `wxIMPLEMENT_APP`。

项目名同时会作为 C++ 类名使用，因此只允许字母、数字和下划线，且不能以数字开头；同名目录已存在时不会覆盖。

### version

```bash
wxdf.py version
wxdf.py --version
wxdf.py -v
```

显示当前版本号。

### build

在项目根目录（含 `CMakeLists.txt` 的目录）下执行：

```bash
wxdf.py build              # Debug 构建（默认）
wxdf.py build --debug       # 同上
wxdf.py build --release     # Release 构建
```

实际调用的命令：

```bash
cmake -DCMAKE_BUILD_TYPE=Debug -B build      # 或 Release
cmake --build build
```

`--debug` 与 `--release` 互斥，同时指定会报错。

### run

在项目根目录下执行构建产物：

```bash
wxdf.py run
```

等价于：

```bash
./build/bin/<project-name>
```

### debug

在项目根目录下用 gdb 调试构建产物：

```bash
wxdf.py debug
```

等价于：

```bash
gdb ./build/bin/<project-name>
```

## 典型工作流

```bash
wxdf.py create-project MyApp
cd MyApp
wxdf.py build            # 或 wxdf.py build --release
wxdf.py run              # 需要图形环境
wxdf.py debug            # 出错时用 gdb 调试
```

## 说明

- 可执行文件名取自根 `CMakeLists.txt` 中 `project()` 声明的名字，缺失时回退为目录名。
- `build`、`run`、`debug` 必须在项目根目录执行；否则会提示找不到 `CMakeLists.txt`。
- 可执行文件不存在时（未构建或已清理），`run`/`debug` 会给出提示，并列出 `build/bin` 下的现有文件。
- 每次 `build` 都会重新执行 CMake 配置，因此切换 `--debug` / `--release` 无需手动清理 `build` 目录。

## 自定义项目

生成后可以按需修改：

- 在 `src/frame/` 下新增窗口类，并把源文件加入 `src/frame/CMakeLists.txt`。
- 程序入口逻辑写在 `src/main.cpp` 的 `<project-name>::OnInit()` 中。
- 需要更多 wxWidgets 组件（如 `adv`、`html`）时，修改根 `CMakeLists.txt` 的 `find_package(wxWidgets REQUIRED COMPONENTS ...)`。

## 作者

流浪的麦兜（GitHub：[McDoll-cn](https://github.com/McDoll-cn)）

## 许可证

本项目采用 MIT 授权，详见 [LICENSE](LICENSE)。
