# 写Extending Python模块的一些备忘笔记

## PyObject_GetAttrString
PyObject_GetAttrString(a, "name")相当于a.name或者getattar(a, "name")

获得的PyObject在返回前是加了引用的，因此使用完毕需要减引用。


## PyEval_CallMethod
PyEval_CallMethod(obj, "func", "()")相当于obj.func()。

获得的PyObject在返回前是加了引用的，因此使用完毕需要减引用。

第三个参数开始(示例里的"()")，后面是可变长参数列表，使用时跟Py_VaBuildValue一样

## PyArg_ParseTuple
解析参数，函数内没有增加引用计数，因此调用者也不需要额外减引用计数


