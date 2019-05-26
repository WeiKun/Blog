# 入门级学习

## 最简单的
- 设置cmake的最低版本：cmake_minimum_required
- 设置项目名：project
- 增加可执行文件：add_executable

例如下面的CMakeLists代表需要最cmake低版本2.8，项目名为Demo1，用main.cc编译可执行文件Demo：
```cmake
cmake_minimum_required (VERSION 2.8)
project (Demo1)
add_executable(Demo main.cc)
```

## 引用不同路径
- 新增include目录：include_directories 
- 新增路径命名：aux_source_directory

例如我在math下有文件MathFunctions.cc跟MathFunctions.h，根目录main.cc中需要用到。那么这样即可（也可以子目录的方式）：

```
cmake_minimum_required (VERSION 2.8)
project (Demo2.5)

include_directories(math)
aux_source_directory(math MATH_DIR)

add_executable(Demo main.cc ${MATH_DIR})
```

## 子目录递归跟链接库

- 生成链接库：add_library 
- 添加子目录：add_subdirectory
- 添加链接库：target_link_libraries

还是跟上面的一样目录结构，根目录main.cc，math目录下MathFunctions.cc跟MathFunctions.h，那么可以在子目录math建立一个CMakeLists.txt，这里执行对静态链接库的生成
```
aux_source_directory(. DIR_LIB_SRCS)
add_library (MathFunctions ${DIR_LIB_SRCS})
```

根目录CMakeLists.txt，加入子目录跟链接入链接库
```
cmake_minimum_required (VERSION 2.8)
project (Demo3)
aux_source_directory(. DIR_SRCS)
add_subdirectory(math)
add_executable(Demo main.cc)
target_link_libraries(Demo MathFunctions)
```

## option跟configure_file
- option，cmake中一个编译选项，可以在CMakeLists.txt用于if判断来影响执行分支，也可以影响configure_file中某个配置是否生效，但在Makefile中不会反映出来
- configure_file，定义配置

例如下面一段CMakeList.txt(节选)

```
configure_file (
  "${PROJECT_SOURCE_DIR}/config.h.in"
  "${PROJECT_SOURCE_DIR}/config.h"
)

option (USE_MYMATH "Use provided math implementation" OFF)
message("USE_MYMATH is ${USE_MYMATH}")

if (USE_MYMATH)
  include_directories ("${PROJECT_SOURCE_DIR}/math")
  add_subdirectory (math)
  set (EXTRA_LIBS ${EXTRA_LIBS} MathFunctions)
endif (USE_MYMATH)
```

上面configure_file定义了输入文件为config.h.in(需要我们手动写)跟输出文件config.h(自动生成)。同时定义了选项USE_MYMATH，默认为OFF。并且如果USE_MYMATH为ON，则编译math子目录并将其链接库加入到EXTRA_LIBS。

config.h.in如下

```
#cmakedefine USE_MYMATH 1
```

如果普通的执行cmake，message显示USE_MYMATH为OFF，并且生成的config.h如下

```
/* #undef USE_MYMATH */
```

但是也可以cmake时加入编译选项的设置，例如"cmake ../ -DUSE_MYMATH=ON"时的message就是"USE_MYMATH is ON"，生成的config.h如下

```
#define USE_MYMATH 1
```