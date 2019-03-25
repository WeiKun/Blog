# 单例的简单踩坑与实现
[示例代码][1]

不可避免的，经常会遇到一些场景，它们需要在main函数执行之前对某个class的某个实例完成初始化，并且这个class在整个程序的生命周期内都只存在这一个实例。这就是典型的单例模式。

普通情况下需要帮class定义一个global或者static的变量，感觉并不优雅，可以用类似"class Test : Singleton<Test>"的方式实现(模仿boost)。

## 错误的范例
想当然的，可以Singleton模板里定义一个static的类型为Test变量。

```cpp
template <class T>
class Singleton
{
public:
    Singleton();
    ~Singleton();
 
    static T instance;
};

template <class T>
T Singleton<T>::instance;
```
测试代码
```cpp
class A: public Singleton<A>
{
};

int main()
{   
    std::cout << &A::instance << std::endl;
    return 0;
}
```
运行良好啊
```shell
$ g++ test1.cpp                
$ ./a.out 
0x55d5147ec172
```

但是实际上这个模板是有问题的，如果我们没有显式对A::instance进行使用，编译器就不会展开A::instance。（如果用于静态注册，就很经常出现这种需求）

换一个测试代码试试。

```cpp
#include "Singleton.h"
#include <iostream>

class A: public Singleton<A>
{
public:
    A()
    {
        std::cout<< "A\n" << std::endl;
    }
};

int main()
{   
    return 0;
}
```
按道理应该打印下"A"才是，但是实际是不会的。
```
$ g++ test2.cpp 
$ ./a.out 
```
我们需要对static变量加上"__attribute__((used));"才能保证模板一定展开这个instance。

```cpp
template <class T>
class Singleton
{
public:
    static T &GetInstance()
    {
        return instance;
    }

    static T instance;
};

template <class T>
T Singleton<T>::instance __attribute__((used));
```

但是编译时却会报错

```
error: ‘A Singleton<A>::instance’ has incomplete type
 T Singleton<T>::instance __attribute__((used));
   ^~~~~~~~~~~~
```
虽然不明白为啥这里是incomplete type（实际上平时class带一个类型为自己的static变量也不会编译报错），但是显然是不能这样写的。也就是说static的类型必须在这里是完整的。

## 正确的姿势
那么我们就要换一个思路了。

首先，既然是单例，那么单例还是需要有地方定义这个instance的，一般来说单例有三个实现方式：函数的static变量、class的static变量、global变量，class的static变量已经验证不行，global变量没法用模板来组织所以显然也不行，那么就只能用函数的static变量来实现单例的instance了。

```cpp
    static T &GetInstance()
    {
        static T instance;
        return instance;
    }
```

如果没有地方调用GetInstance，那这个instance还是不会实例化，因此我们需要一个地方来调用它。为此，我们可以实现一个嵌套类InnerCreator，这个类在构造函数中调用GetInstance()，然后在Singleton中为InnerCreator定义一个static变量，此时的InnerCreator类肯定是完整的，因此就可以用"__attribute__((used))"来保证其会被展开。

```
template <class T>
class Singleton
{
public:
    class InnerCreator
    {
    public:
        InnerCreator()
        {
            Singleton<T>::GetInstance();
        }
        inline void do_nothing() const {}
    };

    static T &GetInstance()
    {
        static T instance;
        creator.do_nothing();
        return instance;
    }

    static InnerCreator creator;
};

template <class T>
typename Singleton<T>::InnerCreator
Singleton<T>::creator __attribute__((used));
```
[1]:https://github.com/WeiKun/Singleton.git
