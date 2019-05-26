# 脚本语法
cmake本身也是一种比较特殊的脚本，一些内建的命令见[官方文档](https://cmake.org/cmake/help/v3.14/manual/cmake-commands.7.html)。也可以通过cmake --help-command-list跟cmake --help-command查询。

下面是一些基础的语法实例，具体测试代码在demo0：
## set跟message
set就相当于普通的赋值语法，message就是简单的打印
```
#普通的赋值
set(VAR 1) 
message("VAR = ${VAR}")

#list赋值
set(listVAR 1 1 1)
message("listVAR = ${listVAR}")
```

上面这段的输出结果：
```
VAR = 1
listVAR = 1;1;1
```

## if-elseif-else-endif
熟练掌握if-else是程序员最重要的技能，cmake也不例外

```
if(expression1)
    #...
elseif(expression2)
    #...
else()
    #...
endif()
```
对于expression：
- 如果是1、ON、YES、TRUE、Y、非0的数则表示真(不区分大小写)
- 0、OFF、NO、FALSE、N、IGNORE、空字符串、以-NOTFOUND 结尾的字符串则表示假(不区分大小写)
- 如果不是上述情况，则被认为是一个变量的名字。变量的值为第二条所述的各值则表示假，否则表示真。

## foreach
遍历循环
```
set(VAR a b c)
foreach(f ${VAR})
  message("for ${f}")
endforeach()
```
输出
```
for a
for b
for c
```

## while 
循环
```
set(VAR 5)
while(${VAR} GREATER 0)
  message("while ${VAR}")
  math(EXPR VAR "${VAR} - 1")
endwhile()
```
输出
```
while 5
while 4
while 3
while 2
while 1
```

## macro跟function
### 定义
定义macro
```
macro(hellomacro MESSAGE)
  message("hellomacro:${MESSAGE}")
endmacro()
```

定义function
```
function(hellofunction MESSAGE)
  message("hellofunction:${MESSAGE}")
endfunction()
```

调用
```
hellomacro("hello 1")
hellofunction("hello 2")
```

输出

```
hellomacro:hello 1
hellofunction:hello 2
```

### 验证区别
验证macro跟function的区别是否与普通开发语言一致
```
macro(hellomacro2 BASE)
        message("hellomacro2: ${BASE}")
        set(BASE "macro")
endmacro()

function(hellofunction2 BASE)
  message("hellofunction2: ${BASE}")
  set(BASE "function")
  message("hellofunction2 after: ${BASE}")
endfunction()

set(BASE "None")
message("before hellomacro2 BASE = ${BASE}")
hellomacro2(BASE)
message("before hellofunction2 BASE = ${BASE}")
hellofunction2(BASE)
message("after hellofunction2 BASE = ${BASE}")
```

输出
```
before hellomacro2 BASE = None
hellomacro2: None
before hellofunction2 BASE = macro
hellofunction2: macro
hellofunction2 after: function
after hellofunction2 BASE = macro
```

验证发现跟普通开发语言一样，宏是没有自己的环境的，修改会直接改到global环境，函数则不会。

但是宏跟函数均可以对参数进行写操作
```
macro(hellomacro3 ARG)
  message("hellomacro3: ${ARG}")
  set(${ARG} "macro")
endmacro()

function(hellofunction3 ARG)
  message("hellofunction2: ${ARG}")
  set(${ARG} "function" PARENT_SCOPE)
  message("hellofunction2 after: ${ARG}")
endfunction()

set(BASE "None")
message("before hellomacro3 BASE = ${BASE}")
hellomacro3(BASE)
message("before hellofunction3 BASE = ${BASE}")
hellofunction3(BASE)
message("after hellofunction3 BASE = ${BASE}")
```
输出

```
before hellomacro3 BASE = None
hellomacro3: BASE
before hellofunction3 BASE = macro
hellofunction2: BASE
hellofunction2 after: BASE
after hellofunction3 BASE = function
```

==注意：调用函数或者宏时，hello(ARG)传入的是ARG这个变量，hello(${ARG})传入的是ARG的值，有点类似C++的引用传递跟值传递。因此如果希望在函数或者宏内进行修改，不能传值，而应该传变量==

### 作用域
function的作用域也是local比global优先

```
set(GLOBAL "Global")
set(LOCAL "Global")
function(hellofunction3)
  set(LOCAL "Local")
  message("hellofunction3 GLOBAL:${GLOBAL} LOCAL:${LOCAL}")
endfunction()
hellofunction3()
message("hellofunction3 out GLOBAL:${GLOBAL} LOCAL:${LOCAL}")
```
输出

```
hellofunction3 GLOBAL:Global LOCAL:Local
hellofunction3 out GLOBAL:Global LOCAL:Global
```


## 判断操作符
expression还可以包含操作符
- 一元操作符，例如：EXISTS、COMMAND、DEFINED 等
- 二元操作符，例如：EQUAL、LESS、GREATER、STRLESS、STRGREATER 等
- 操作符优先级：一元操作符 > 二元操作符 > NOT > AND/OR

具体的操作符详细列表可以在[官网](https://cmake.org/cmake/help/v3.14/command/if.html)查到，while跟if共享所有操作符，下面是一些常用的

### COMMAND
- if(COMMAND command-name)
- 为真的前提是存在 command-name 命令、宏或函数且能够被调用

### EXISTS
- if(EXISTS name)
- 为真的前提是存在 name 的文件或者目录（应该使用绝对路径）

### IS_DIRECTORY
- if(IS_DIRECTORY directory-name)
- 为真的前提是 directory-name 表示的是一个目录（应该使用绝对路径）

### IS_NEWER_THAN
- if(file1 IS_NEWER_THAN file2)
- 为真的前提是 file1 比 file2 新或者 file1、file2 中有一个文件不存在（应该使用绝对路径）

### DEFINED
- if(DEFINED variable)
- 为真的前提是 variable 表示的变量被定义了。

## 其他查询途径
首先，cmake可以通过下列指令来进行查询
- cmake --help-command-list可以列出所有cmake的command
- cmake --help-command cmd可以针对单个cmd查询使用方法
- cmake --help-property-list列出所有属性
- cmake --help-property prop查询单个prop
- cmake --help-variable-list列出所有变量
- cmake --help-variable var查询单个变量
