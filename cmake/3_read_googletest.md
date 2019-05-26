# 实战解读CMakeList
通过之前的学习，对cmake语法有了一定的了解，进一步尝试阅读解析一些开源项目的CMakeLists.txt，验证思路

## googletest
### 根目录CMakeLists.txt
```
# Note: CMake support is community-based. The maintainers do not use CMake
# internally.

cmake_minimum_required(VERSION 2.8.8)

project(googletest-distribution)
set(GOOGLETEST_VERSION 1.9.0)

if (CMAKE_VERSION VERSION_LESS "3.1")
  add_definitions(-std=c++11)
else()
  set(CMAKE_CXX_STANDARD 11)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  if(NOT CYGWIN)
    set(CMAKE_CXX_EXTENSIONS OFF)
  endif()
endif()

if (POLICY CMP0048)
  cmake_policy(SET CMP0048 NEW)
endif (POLICY CMP0048)

enable_testing()

include(CMakeDependentOption)
include(GNUInstallDirs)

#Note that googlemock target already builds googletest
option(BUILD_GMOCK "Builds the googlemock subproject" ON)
option(INSTALL_GTEST "Enable installation of googletest. (Projects embedding googletest may want to turn this OFF.)" ON)

if(BUILD_GMOCK)
  add_subdirectory( googlemock )
else()
  add_subdirectory( googletest )
endif()
```
- cmake_minimum_required(VERSION 2.8.8)表示最低cmake版本2.8.8
- project(googletest-distribution)设置项目名为googletest-distribution
- set(GOOGLETEST_VERSION 1.9.0)设置版本号GOOGLETEST_VERSION为1.9.0(其实就是一个变量)
- if (CMAKE_VERSION VERSION_LESS "3.1")...endif()检查cmake版本，3.1以下增加预编译选项 -std=c++11，否则设置CMAKE_CXX_STANDARD为11等
- if (POLICY CMP0048)...endif (POLICY CMP0048)如果当前语法标准是CMP0048，设置CMP0048为NEW
- enable_testing()允许各级目录add_test
- include(CMakeDependentOption)以及include(GNUInstallDirs)，include默认的/usr/share/cmake-3.7/Modules下的模块(我是cmake3.7，如果其他版本应该地址也会调整)CMakeDependentOption.cmake跟GNUInstallDirs.cmake，CMakeDependentOption.cmake比较简单，就是引入一个宏CMAKE_DEPENDENT_OPTION
- option(BUILD_GMOCK)以及option(INSTALL_GTEST)，两个选项BUILD_GMOCK跟INSTALL_GTEST，默认都是ON
- if(BUILD_GMOCK)...endif()根据option选择子项目googlemock还是googletest

==所以根目录的CMakeLists主要就是决定用哪一个子项目。==

### 子项目googletest/googlemock/CMakeLists.txt
文件太长，截断为4个部分逐个分析

#### 第一部分
```
option(gmock_build_tests "Build all of Google Mock's own tests." OFF)

# A directory to find Google Test sources.
if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/gtest/CMakeLists.txt")
  set(gtest_dir gtest)
else()
  set(gtest_dir ../googletest)
endif()

# Defines pre_project_set_up_hermetic_build() and set_up_hermetic_build().
include("${gtest_dir}/cmake/hermetic_build.cmake" OPTIONAL)

if (COMMAND pre_project_set_up_hermetic_build)
  # Google Test also calls hermetic setup functions from add_subdirectory,
  # although its changes will not affect things at the current scope.
  pre_project_set_up_hermetic_build()
endif()
```
- 新增gmock_build_tests，默认为OFF的option
- 如果文件${CMAKE_CURRENT_SOURCE_DIR}/gtest/CMakeLists.txt存在，设置gtest_dir为gtest，否则../googletest
- 如果gtest_dir目录下有cmake/hermetic_build.cmake，将其include
- 如果命令pre_project_set_up_hermetic_build存在，执行pre_project_set_up_hermetic_build()

#### 第二部分
```
if (CMAKE_VERSION VERSION_LESS 3.0)
  project(gmock CXX C)
else()
  cmake_policy(SET CMP0048 NEW)
  project(gmock VERSION ${GOOGLETEST_VERSION} LANGUAGES CXX C)
endif()
cmake_minimum_required(VERSION 2.6.4)

if (COMMAND set_up_hermetic_build)
  set_up_hermetic_build()
endif()

add_subdirectory("${gtest_dir}" "${gmock_BINARY_DIR}/${gtest_dir}")

if(CMAKE_PROJECT_NAME STREQUAL "gmock" OR CMAKE_PROJECT_NAME STREQUAL "googletest-distribution")
  option(BUILD_SHARED_LIBS "Build shared libraries (DLLs)." OFF)
else()
  mark_as_advanced(gmock_build_tests)
endif()

config_compiler_and_linker()  # from ${gtest_dir}/cmake/internal_utils.cmake

set(gmock_build_include_dirs
  "${gmock_SOURCE_DIR}/include"
  "${gmock_SOURCE_DIR}"
  "${gtest_SOURCE_DIR}/include"
  "${gtest_SOURCE_DIR}")
include_directories(${gmock_build_include_dirs})
```
- 判断cmake版本，小于3.0设置项目为gmock(语言C/C++)，否则设置策略CMP0048为新，并且设置项目为gmock(版本取GOOGLETEST_VERSION语言C/C++)
- cmake版本最低需要2.6.4
- 如果命令set_up_hermetic_build存在，执行set_up_hermetic_build()
- 添加项目，路径为${gtest_dir}，执行路径为${gmock_BINARY_DIR}/${gtest_dir}
- 如果项目名为gmock或者googletest-distribution，新增option BUILD_SHARED_LIBS，默认OFF；否则标记缓冲变量gmock_build_tests为高级变量
- 调用${gtest_dir}/cmake/internal_utils.cmake的宏config_compiler_and_linker
- 设置gmock_build_include_dirs为一串目录，并且设置gmock_build_include_dirs为include路径

#### 第三部分
```
if (MSVC)
  cxx_library(gmock
              "${cxx_strict}"
              "${gtest_dir}/src/gtest-all.cc"
              src/gmock-all.cc)

  cxx_library(gmock_main
              "${cxx_strict}"
              "${gtest_dir}/src/gtest-all.cc"
              src/gmock-all.cc
              src/gmock_main.cc)
else()
  cxx_library(gmock "${cxx_strict}" src/gmock-all.cc)
  target_link_libraries(gmock PUBLIC gtest)
  cxx_library(gmock_main "${cxx_strict}" src/gmock_main.cc)
  target_link_libraries(gmock_main PUBLIC gmock)
endif()

if (DEFINED CMAKE_VERSION AND NOT "${CMAKE_VERSION}" VERSION_LESS "2.8.11")
  target_include_directories(gmock SYSTEM INTERFACE
    "$<BUILD_INTERFACE:${gmock_build_include_dirs}>"
    "$<INSTALL_INTERFACE:$<INSTALL_PREFIX>/${CMAKE_INSTALL_INCLUDEDIR}>")
  target_include_directories(gmock_main SYSTEM INTERFACE
    "$<BUILD_INTERFACE:${gmock_build_include_dirs}>"
    "$<INSTALL_INTERFACE:$<INSTALL_PREFIX>/${CMAKE_INSTALL_INCLUDEDIR}>")
endif()

install_project(gmock gmock_main)

```
- 根据是否MSVC选择对cxx_library的调用参数(函数在相对路径../googletest/cmake/internal_utils.cmake文件中)，主要是设置对gmock跟gmock_main两个链接库的一些参数
- 如果CMAKE版本不低于2.8.11，用target_include_directories标记gmock与gmock_main的include路径，其中BUILD_INTERFACE是build时的include路径，INSTALL_INTERFACE是安装时拷贝include文件的目标路径
- 调用internal_utils.cmake中的install_project安装gmock与gmock_main

#### 第四部分
```
if (gmock_build_tests)
  # This must be set in the root directory for the tests to be run by
  # 'make test' or ctest.
  enable_testing()

  if (WIN32)
    file(GENERATE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>/RunTest.ps1"
         CONTENT
"$project_bin = \"${CMAKE_BINARY_DIR}/bin/$<CONFIG>\"
$env:Path = \"$project_bin;$env:Path\"
& $args")
  elseif (MINGW)
    file(GENERATE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/RunTest.ps1"
         CONTENT
"$project_bin = (cygpath --windows ${CMAKE_BINARY_DIR}/bin)
$env:Path = \"$project_bin;$env:Path\"
& $args")
  endif()
  
  cxx_test(gmock-actions_test gmock_main)
  cxx_test(gmock-cardinalities_test gmock_main)
  cxx_test(gmock_ex_test gmock_main)
  cxx_test(gmock-function-mocker_test gmock_main)
  cxx_test(gmock-generated-actions_test gmock_main)
  cxx_test(gmock-generated-function-mockers_test gmock_main)
  cxx_test(gmock-generated-matchers_test gmock_main)
  cxx_test(gmock-internal-utils_test gmock_main)
  cxx_test(gmock-matchers_test gmock_main)
  if (MINGW)
    target_compile_options(gmock-matchers_test PRIVATE "-Wa,-mbig-obj")
  endif()
  cxx_test(gmock-more-actions_test gmock_main)
  cxx_test(gmock-nice-strict_test gmock_main)
  cxx_test(gmock-port_test gmock_main)
  cxx_test(gmock-spec-builders_test gmock_main)
  cxx_test(gmock_link_test gmock_main test/gmock_link2_test.cc)
  cxx_test(gmock_test gmock_main)

  if (DEFINED GTEST_HAS_PTHREAD)
    cxx_test(gmock_stress_test gmock)
  endif()

  if (MSVC)
    cxx_library(gmock_main_no_exception "${cxx_no_exception}"
      "${gtest_dir}/src/gtest-all.cc" src/gmock-all.cc src/gmock_main.cc)

    cxx_library(gmock_main_no_rtti "${cxx_no_rtti}"
      "${gtest_dir}/src/gtest-all.cc" src/gmock-all.cc src/gmock_main.cc)

  else()
    cxx_library(gmock_main_no_exception "${cxx_no_exception}" src/gmock_main.cc)
    target_link_libraries(gmock_main_no_exception PUBLIC gmock)

    cxx_library(gmock_main_no_rtti "${cxx_no_rtti}" src/gmock_main.cc)
    target_link_libraries(gmock_main_no_rtti PUBLIC gmock)
  endif()
  cxx_test_with_flags(gmock-more-actions_no_exception_test "${cxx_no_exception}"
    gmock_main_no_exception test/gmock-more-actions_test.cc)

  cxx_test_with_flags(gmock_no_rtti_test "${cxx_no_rtti}"
    gmock_main_no_rtti test/gmock-spec-builders_test.cc)

  cxx_shared_library(shared_gmock_main "${cxx_default}"
    "${gtest_dir}/src/gtest-all.cc" src/gmock-all.cc src/gmock_main.cc)

  cxx_executable_with_flags(shared_gmock_test_ "${cxx_default}"
    shared_gmock_main test/gmock-spec-builders_test.cc)
  set_target_properties(shared_gmock_test_
    PROPERTIES
    COMPILE_DEFINITIONS "GTEST_LINKED_AS_SHARED_LIBRARY=1")
    
  cxx_executable(gmock_leak_test_ test gmock_main)
  py_test(gmock_leak_test)

  cxx_executable(gmock_output_test_ test gmock)
  py_test(gmock_output_test)
endif()

```
- 这一部分主要是用于配置测试，函数cxx_test也在internal_utils.cmake中，主要是配置一些测试的公共参数，最里面会调用到add_test

==gmock主要的目标是编译并安装gmock跟gmock_main，并且会递归执行gtest==

### 子项目googletest/googletest/CMakeLists.txt 
跟gmock差不多，而且太长，就不贴出来了，大致流程：
- 设置option
- 尝试include hermetic_build.cmake
- 尝试执行pre_project_set_up_hermetic_build()
- 根据cmake版本设置项目属性
- 根据gtest是否当前主项目设置是否build链接库的option
- 将一些option配置为高级
- 如果gtest_hide_internal_symbols配置为ON，设置CMAKE_CXX_VISIBILITY_PRESET跟CMAKE_VISIBILITY_INLINES_HIDDEN
- 执行config_compiler_and_linker()
- 如果配置了INSTALL_GTEST，执行一些参数设置
- 配置include路径gtest_build_include_dirs
- 用cxx_library配置链接库gtest跟gtest_main的生成
- 如果cmake版本不在2.8.11以下，跟gmock一样加入include路径
- 调用install_project
- 一堆test

==gtest的主要目标是编译并安装gtest跟gtest_main==