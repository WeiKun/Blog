## cmake
gflags采用camke来做项目的编译管理。

gflags本身经常作为其他项目的子项目，用add_subdirectory加入到其他项目的cmake序列中。

预料到这种情况，为了避免namespace的冲突以及一些比较常用的编译选项的冲突（尤其跟google其他开源项目共存在项目中的时候），gflags的CMakeList中对是否作为子项目就行了分别处理，很多默认编译选项不一样，所以用系统路径的gflags跟用子项目中的gflags是不一样。

例如用系统路径下的gflags的namespace是google，子项目却是gflags。还有默认编译目标，两者也是不一样的。


## 源码文件特点
从CMakeList中可以看出，文件分为PUBLIC_HDRS/PRIVATE_HDRS/GFLAGS_SRCS三种

其中PUBLIC_HDRS都是src目录下的.h.in文件，cmake时通过cmake语法configure_file出相应的.h文件到build目录下的include目录。

PRIVATE_HDRS跟GFLAGS_SRCS都是直接在src目录下。

因此如果用作子项目时，include的路径实际是由build的路径来决定的，而不是在项目的src或者include（当然也没有include）路径下

## 数据结构特点

### FlagValue
FlagValue是保存

```cpp
enum ValueType {
    FV_BOOL = 0,
    FV_INT32 = 1,
    FV_UINT32 = 2,
    FV_INT64 = 3,
    FV_UINT64 = 4,
    FV_DOUBLE = 5,
    FV_STRING = 6,
    FV_MAX_INDEX = 6,
};

template <typename FlagType> struct FlagValueTraits;
  
#define DEFINE_FLAG_TRAITS(type, value)        \
  template <>                                  \
  struct FlagValue::FlagValueTraits<type> {    \
    static const ValueType kValueType = value; \
  }
  
DEFINE_FLAG_TRAITS(bool, FV_BOOL);
DEFINE_FLAG_TRAITS(int32, FV_INT32);
DEFINE_FLAG_TRAITS(uint32, FV_UINT32);
DEFINE_FLAG_TRAITS(int64, FV_INT64);
DEFINE_FLAG_TRAITS(uint64, FV_UINT64);
DEFINE_FLAG_TRAITS(double, FV_DOUBLE);
DEFINE_FLAG_TRAITS(std::string, FV_STRING);
```
这样结合就可以做从type映射到整型

```
template <typename FlagType>
FlagValue::FlagValue(FlagType* valbuf,
                     bool transfer_ownership_of_value)
    : value_buffer_(valbuf),
      type_(FlagValueTraits<FlagType>::kValueType),
      owns_value_(transfer_ownership_of_value) {
}

```
然后这样就可以做到类似多态的效果，但是不需要在原来class里定义这些函数（这样就可以随便在任何文件通过DEFINE_FLAG_TRAITS实例化，保证代码良好的局部性）


```cpp

class FlagValue {
  template <typename FlagType>
  FlagValue(FlagType* valbuf, bool transfer_ownership_of_value);
  
  void* const value_buffer_;          // points to the buffer holding our data
  const int8 type_;                   // how to interpret value_
  const bool owns_value_;             // whether to free value on destruct
};

template <typename FlagType>
FlagValue::FlagValue(FlagType* valbuf,
                     bool transfer_ownership_of_value)
    : value_buffer_(valbuf),
      type_(FlagValueTraits<FlagType>::kValueType),
      owns_value_(transfer_ownership_of_value) {
}
```
结合模板构造函数，就可以优雅地兼容不同类型了，不过析构函数还是要保持原样

### FlagRegisterer
FlagRegisterer会new两个FlagValue分别代指当前value跟default value，然后调用RegisterCommandLineFlag进行注册

而RegisterCommandLineFlag中会new一个CommandLineFlag并实际注册到FlagRegistry::GlobalRegistry()

### DEFINE_xxxx

对于每一个Flag，在fl##shorttype的namespace中，存在三个跟value值相等的变量，对外只暴露第二个
```cpp
#define DEFINE_VARIABLE(type, shorttype, name, value, help)             \
  namespace fL##shorttype {                                             \
    static const type FLAGS_nono##name = value;                         \
    /* We always want to export defined variables, dll or no */         \
    GFLAGS_DLL_DEFINE_FLAG type FLAGS_##name = FLAGS_nono##name;        \
    type FLAGS_no##name = FLAGS_nono##name;                             \
    static GFLAGS_NAMESPACE::FlagRegisterer o_##name(                   \
      #name, MAYBE_STRIPPED_HELP(help), __FILE__,                       \
      &FLAGS_##name, &FLAGS_no##name);                                  \
  }                                                                     \
  using fL##shorttype::FLAGS_##name
```
FlagRegisterer的构造函数传入的是第二个跟第三个value的指针，第一个value的存在意义在于保证在global变量构造前，已经有初始化好的FLAG_##value可以使用。其中前者用于记录当前值，后者用于记录default值

string比较特殊，没有用通用的DEFINE_VARIABLE

## 运行
一般在main函数里调用google::ParseCommandLineFlags(&argc,&argv,true)来对进行参数运行。

ParseCommandLineFlags又会通过ParseCommandLineFlagsInternal先后调用ProcessFlagfileLocked跟ProcessFromenvLocked，后者会调用2次，然后才会调用ParseNewCommandLineFlags从argc中解析参数

无论是ProcessFlagfileLocked、ProcessFromenvLocked还是ParseNewCommandLineFlags，最终都会调用ProcessSingleOptionLocked来完成基础的每一个Flag的处理。具体SetFlagLocked里的处理不细表。

值得注意的是，ProcessSingleOptionLocked在完成解析之后还会考虑本次解析的flag是不是flagfile、fromenv、tryfromenv之一，如果是则执行相关处理。

另外，如果是--help式的参数格式，进程会在HandleCommandLineHelpFlags里exit。
