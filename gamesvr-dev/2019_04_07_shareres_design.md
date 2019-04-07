esXXX数据结构设计与pack相关功能)
## 数据结构设计
### ResXXX
首先仿照Python源码，define一个ResObject_HEAD跟一个ResObject_VAR_HEAD用于表示公有数据成员。
```c
#define ResObject_HEAD   \
	INT64 ob_type;

#define ResObject_VAR_HEAD               \
    ResObject_HEAD                       \
    INT64 ob_size; /* Number of items in variable part */

```
其中ob_type用于指示结构体的类型，类似于PyObject的struct _typeobject *ob_type。

而ob_size用于表示变长数据的长度(主要是str跟tuple，dict跟set的长度表示方法跟普通的变长数据不一样，因此不采用这个成员)

然后仿照Python的相关原生类型，设计ResInt/ResStr/ResFloat/ResTuple/ResSet/ResDict六个类型

#### ResInt
对于Int类型，只需要记录一个64位整型即可
```c
typedef struct {
	ResObject_HEAD
	INT64 ob_ival;
} ResIntObject;
```

#### ResStr
String是变长的数据，因此需要使用ResObject_VAR_HEAD，同时在数据结构末尾使用变长数组。

此外，为了优化可能存在的hash运算，string的hash值也需要记录下来。
```c
typedef struct {
	ResObject_VAR_HEAD
	INT64 ob_shash;
	INT8 ob_sval[1];
} ResStrObject;
```

#### ResFloat
Float跟Int类似。
```c
typedef struct {
	ResObject_HEAD
	double ob_fval;
} ResFloatObject;
```

#### ResTuple
Tuple也是变长数据类型，因此跟也使用ResObject_VAR_HEAD。

同时使用变长数组记录数据，出于地址无关性的设计需要，变长数组里的是数据的地址偏移量(相对于整个数据区的首字节的偏移，而不是相对于所在的tuple)

```c
typedef struct {
	ResObject_VAR_HEAD
	ResObjectOffset ob_item[1];
} ResTupleObject;
```

#### ResSet
仿照PySetObject，设计ResSetEntry来表示set中的单个元素，然后用一个table来记录所有元素，mask来标记table的最大Index(也就是长度-1)

ResSetEntry中的hash是元素的hash值，key是元素的位置，同tuple中一样，也是记录相对于数据区首字节的偏移

```c
typedef struct {
	INT64 hash;
	ResObjectOffset key;
} ResSetEntry;

typedef struct {
	ResObject_HEAD;
	INT64 mask;
	ResSetEntry table[1];
} ResSetObject;
```

#### ResDict
相比set，在ResDictEntry中加入了记录value的成员变量，也是相对于数据区首字节的偏移

```c
typedef struct {
	INT64 me_hash;
	ResObjectOffset m_key;
	ResObjectOffset m_value;
} ResDictEntry;

typedef struct {
	ResObject_HEAD;
	INT64 ma_mask;
	ResDictEntry ma_table[1];
} ResDictObject;

```

## Pack功能
Pack功能是按照设计，将所有data打包到一整块连续的内存空间上。

如果pack数据的时候，已经能够知道每一个数据的偏移量，那么处理就会很方便了：
1. 对于int/str/float，就只需要按照自己的偏移量找到自己的pack的位置，然后pack自己即可
2. 对于容器类，也是找到自己的pack位置，然后先把自己的长度等数据pack上去，再遍历容器内的元素，把偏移值赋值上去即可
3. 出于对unpack时效率的要求(因为每一次读数据都需要unpack，所以还是效率重要)，pack时通过参数指定大端字节序或者小端字节序(暂时没实现，现在全按当前主机字节序)，也就是说如果目标机器不同，可能需要重新用新参数pack一遍数据。

因此采用一个辅助的python模块，这个模块先递归遍历一遍data中的所有数据，然后按照类型放到不同的list中，之后按照Dict-Tuple-Set-Int-Str-Float的顺序逐个计算跟累计偏移量，这样就能知道每一个数据的偏移量了，然后再调用按照上面方案设计的pack模块。

