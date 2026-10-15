#!/usr/bin/env python3
"""wxdf.py -- wxWidgets project scaffold / build / run / debug tool.

Usage:
    wxdf.py create-project <project-name>   generate a project skeleton in the current directory
    wxdf.py build [--debug | --release]     configure and build with cmake at the project root
    wxdf.py run                             run build/bin/<project-name> at the project root
    wxdf.py debug                           debug build/bin/<project-name> with gdb
    wxdf.py version                         print the current version number
"""

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys

VERSION = "0.07"

PLACEHOLDER = "${project-name}$"

ROOT_CMAKE_TEMPLATE = """cmake_minimum_required(VERSION 3.10)
project(${project-name}$ VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

#set global output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

find_package(wxWidgets REQUIRED COMPONENTS core base)

add_subdirectory(src)
"""

SRC_CMAKE = """set(SRC_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)

add_subdirectory(frame)

add_executable(${PROJECT_NAME} WIN32
        ${SRC_FILES}
        ${FRAME_SRC_FILES}
)

target_link_libraries(${PROJECT_NAME} PRIVATE ${wxWidgets_LIBRARIES})

target_include_directories(${PROJECT_NAME} PRIVATE 
        ${wxWidgets_INCLUDE_DIRS}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${FRAME_INCLUDE_DIRS}
)

target_compile_definitions(${PROJECT_NAME} PRIVATE 
        ${wxWidgets_DEFINITIONS}
)
"""

FRAME_CMAKE = """set(FRAME_SRC_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/MainFrame.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/MainFrame.h
    PARENT_SCOPE
)
set(FRAME_INCLUDE_DIRS
    ${CMAKE_CURRENT_SOURCE_DIR}
    PARENT_SCOPE
)
"""

MAINFRAME_H = """#pragma once

#include <wx/wx.h>

namespace frame {

class MainFrame : public wxFrame
{
public:
    MainFrame(wxString& title);

private:
};

} //frame
"""

MAINFRAME_CPP = """#include "MainFrame.h"

namespace frame{

} //namespace frame
"""

MAIN_CPP_TEMPLATE = """#include <wx/wx.h>
#include "frame/MainFrame.h"

class ${project-name}$ : public wxApp
{
public:
    virtual bool OnInit();
};

wxIMPLEMENT_APP(${project-name}$);

bool ${project-name}$::OnInit()
{
}
"""

NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
PROJECT_RE = re.compile(r"^[ \t]*project[ \t]*\([ \t]*([A-Za-z0-9_.+\-]+)", re.MULTILINE)

TREE_TEXT = """  {name}/
  ├── build
  ├── CMakeLists.txt
  └── src
      ├── CMakeLists.txt
      ├── frame
      │   ├── CMakeLists.txt
      │   ├── MainFrame.cpp
      │   └── MainFrame.h
      └── main.cpp"""


def die(message, code=1):
    print("wxdf: error: {}".format(message), file=sys.stderr)
    sys.exit(code)


def write_file(path, content=""):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def cmd_create_project(args):
    name = args.project_name

    if not NAME_RE.match(name):
        die("invalid project name '{}': only letters, digits and underscores are "
            "allowed, and it must not start with a digit "
            "(the name is also used as a C++ class name)".format(name))

    root = os.path.abspath(os.path.join(os.getcwd(), name))
    if os.path.exists(root):
        die("'{}' already exists, refusing to overwrite".format(root))

    for d in (root,
              os.path.join(root, "build"),
              os.path.join(root, "src"),
              os.path.join(root, "src", "frame")):
        os.makedirs(d)

    write_file(os.path.join(root, "CMakeLists.txt"),
               ROOT_CMAKE_TEMPLATE.replace(PLACEHOLDER, name))
    write_file(os.path.join(root, "src", "CMakeLists.txt"), SRC_CMAKE)
    write_file(os.path.join(root, "src", "frame", "CMakeLists.txt"), FRAME_CMAKE)
    write_file(os.path.join(root, "src", "frame", "MainFrame.h"), MAINFRAME_H)
    write_file(os.path.join(root, "src", "frame", "MainFrame.cpp"), MAINFRAME_CPP)
    write_file(os.path.join(root, "src", "main.cpp"),
               MAIN_CPP_TEMPLATE.replace(PLACEHOLDER, name))

    print("project created: {}".format(root))
    print(TREE_TEXT.format(name=name))
    print("\nnext step: cd {} && wxdf.py build && wxdf.py run".format(name))


def project_dir():
    """The project root: the current directory must contain CMakeLists.txt."""
    root = os.getcwd()
    if not os.path.isfile(os.path.join(root, "CMakeLists.txt")):
        die("no CMakeLists.txt found in '{}', please run this command "
            "from the wxWidgets project root".format(root))
    return root


def project_name(root):
    """Read the project name from project() in the root CMakeLists.txt,
    fall back to the directory name."""
    cmake = os.path.join(root, "CMakeLists.txt")
    try:
        with open(cmake, "r", encoding="utf-8", errors="replace") as f:
            m = PROJECT_RE.search(f.read())
    except OSError:
        m = None
    if m and m.group(1) not in ("${", ""):
        return m.group(1)
    return os.path.basename(root)


def executable_path(root):
    exe = os.path.join(root, "build", "bin", project_name(root))
    if not os.path.isfile(exe):
        hint = ""
        bin_dir = os.path.join(root, "build", "bin")
        if os.path.isdir(bin_dir):
            found = sorted(os.listdir(bin_dir))
            if found:
                hint = ", build/bin contains: {}".format(", ".join(found))
        die("executable '{}' does not exist{}, "
            "please run wxdf.py build first".format(exe, hint))
    if not os.access(exe, os.X_OK):
        os.chmod(exe, os.stat(exe).st_mode | stat.S_IXUSR)
    return exe


def run_cmd(cmd, cwd=None):
    print("wxdf: $ {}".format(" ".join(cmd)))
    return subprocess.call(cmd, cwd=cwd)


def cmd_build(args):
    root = project_dir()
    build_type = "Release" if args.release else "Debug"

    rc = run_cmd(["cmake", "-DCMAKE_BUILD_TYPE={}".format(build_type), "-B", "build"],
                 cwd=root)
    if rc != 0:
        die("cmake configuration failed (exit code {})".format(rc), rc)

    rc = run_cmd(["cmake", "--build", "build"], cwd=root)
    if rc != 0:
        die("build failed (exit code {})".format(rc), rc)

    print("wxdf: build succeeded ({}), executable at {}".format(
        build_type, os.path.join(root, "build", "bin", project_name(root))))


def cmd_run(args):
    root = project_dir()
    rc = run_cmd([executable_path(root)], cwd=root)
    if rc != 0:
        sys.exit(rc)


def cmd_debug(args):
    root = project_dir()
    exe = executable_path(root)
    gdb = shutil.which("gdb")
    if gdb is None:
        die("gdb not found in PATH, please install gdb first")
    rc = run_cmd([gdb, exe], cwd=root)
    if rc != 0:
        sys.exit(rc)


def cmd_version(args):
    print("wxdf.py version {}".format(VERSION))


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        prog="wxdf.py",
        description="wxWidgets project scaffold / build / run / debug tool")
    parser.add_argument("-v", "--version", action="store_true", dest="show_version",
                        help="print the version number and exit")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_create = sub.add_parser("create-project",
                              help="generate a wxWidgets project skeleton "
                                   "in the current directory")
    p_create.add_argument("project_name", metavar="project-name",
                          help="project name (also used as the C++ class name)")
    p_create.set_defaults(func=cmd_create_project)

    p_build = sub.add_parser("build",
                             help="configure and build with cmake at the project "
                                  "root (Debug by default)")
    p_build.add_argument("--debug", dest="debug", action="store_true",
                         help="build with CMAKE_BUILD_TYPE=Debug (default)")
    p_build.add_argument("--release", dest="release", action="store_true",
                         help="build with CMAKE_BUILD_TYPE=Release")
    p_build.set_defaults(func=cmd_build, debug=False, release=False)

    p_run = sub.add_parser("run", help="run build/bin/<project-name>")
    p_run.set_defaults(func=cmd_run)

    p_debug = sub.add_parser("debug", help="debug build/bin/<project-name> with gdb")
    p_debug.set_defaults(func=cmd_debug)

    p_version = sub.add_parser("version", help="print the current version number")
    p_version.set_defaults(func=cmd_version)

    args = parser.parse_args(argv)

    if args.show_version:
        cmd_version(args)
        return 0
    if not args.command:
        parser.print_help()
        return 1
    if args.command == "build" and args.debug and args.release:
        die("--debug and --release are mutually exclusive", 2)

    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
