# 02Chap allocator——空间配置器

顾名思义，allocator就是在STL中封装了一层的空间分配器，虽然绝大多数时候都是隐藏在背后工作，但是如果有需要也可以自己实现一个，然后在各种容器中使用，例如

```
vector<int, std::allocator<int> > xxx;
```

## 标准中的allocator
[参考](https://en.cppreference.com/w/cpp/memory/allocator)

allocator是一个模板

```cpp
template< class T >
struct allocator;
```

按照标准，应该定义如下类型

```
    typedef T           value_type;
    typedef T*          pointer;
    typedef const T*    const_pointer;
    typedef T&          reference;
    typedef const T&    const_reference;
    typedef size_t      size_type;
    typedef ptrdiff_t   difference_type;
    
    template<typename T1>
	struct rebind
	{
	    typedef allocator<T1> other;
	};

```

和下列函数

```cpp

//返回对象地址
pointer address( reference x ) const;
const_pointer address( const_reference x ) const;

//配置空间，hint预留位，无用
pointer allocate( size_type n, const void * hint = 0 );

//返回配置的空间
void deallocate( T* p, std::size_t n );

//返回可以成功配置的最大量
size_type max_size() const throw();

//以val为参数为p执行构造函数，类似于placement new
void construct( pointer p, const_reference val );

//执行析构函数
void destroy( pointer p );
```
## SGI的allocator

按照书里写的，SGI并没有使用自己实现的不完整的allocator。但是从最新代码看，应该是迭代了这部分，现在默认是使用的allocator，但是allocator的基类__allocator_base由配置指定，并且提供了五个可选：

```shell
  case ${enable_libstdcxx_allocator_flag} in
    bitmap)
      ALLOCATOR_H=config/allocator/bitmap_allocator_base.h
      ALLOCATOR_NAME=__gnu_cxx::bitmap_allocator
      ;;
    malloc)
      ALLOCATOR_H=config/allocator/malloc_allocator_base.h
      ALLOCATOR_NAME=__gnu_cxx::malloc_allocator
      ;;
    mt)
      ALLOCATOR_H=config/allocator/mt_allocator_base.h
      ALLOCATOR_NAME=__gnu_cxx::__mt_alloc
      ;;
    new)
      ALLOCATOR_H=config/allocator/new_allocator_base.h
      ALLOCATOR_NAME=__gnu_cxx::new_allocator
      ;;
    pool)
      ALLOCATOR_H=config/allocator/pool_allocator_base.h
      ALLOCATOR_NAME=__gnu_cxx::__pool_alloc
      ;;
  esac
```
除了rebind外其他的方法都是在基类实现。

## new_allocator
new_allocator是最简单的实现，就是对operator new跟operator delete做了简单的封装

## malloc_allocator
malloc_allocator跟new_allocator的差别就是用malloc/free替换了operator new/delete

## pool_allocator

原文中的SGI两级allocator，在现有版本中被迭代了，作为几种可选的alloc之一的pool_allocator供选择，但是大体实现还是按照书中的介绍。(一些变量名被迭代了，malloc也用operator new替代了，下面按照最新版本)

pool_allocator比较类似slab分配器，在allocator中保留一个_S_free_list，将空闲的内存块存在里面

```cpp
    union _Obj
    {
        union _Obj* _M_free_list_link;
        char        _M_client_data[1];    // The client sees this.
    };
    
    static _Obj* volatile         _S_free_list[_S_free_list_size];
```
其中，大小相同的内存块用union _Obj链接成一个链表，然后_S_free_list中不同下标的元素指向这些内存块链表的头节点。

不同链表之间的内存块大小差为_S_align(8)。(也就是_S_free_list[0]指向大小为8,_S_free_list[1]指向12,_S_free_list[15]指向128)

allocate __bytes大小的空间时：
1. 如果__bytes超过_S_max_bytes(128)则直接调用operator new分配，否则
2. 找到_S_free_list中对应__bytes的节点__free_list，如果__free_list不为空就取下第一个内存块返回，否则
3. 调用_M_refill重新填充，而_M_refill又会调用_M_allocate_chunk尝试去allocator中去取20个相同大小的节点
4. 如果allocator能分配20个就直接分配20个；否则如果能分配1个以上但是不满20个，就按照剩余空间大小分配；如果一个都无法分配，就调用operator new去系统拿(也可能是上一级配置器)；如果系统分配失败，就遍历_S_free_list大小超过__bytes的节点，看有没有可以供分配的内存块，如果还没有就最后抛出异常。

deallocate时很简单：
1. 如果__bytes超过_S_max_bytes(128)，调用operator delete销毁，否则
2. 找到_S_free_list中对应的节点，塞入链表

