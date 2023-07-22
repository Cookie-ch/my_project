"""
@author: chen
@file: 面向对象-三乐购物系统.py
@time: 2023/4/13 15:55
"""
import pickle
# import json

# 购物系统类
# 实例属性 -- 商品信息、系统说明信息、当前多个用户信息
# 方法 -- 登录注册、查看商品、添加购物车、结算

# 用户类
# 实例属性 -- 名字、密码、钱、购物车
# 方法
# user class
class User:
    def __init__(self, name, passwd, init_amount):
        self.name = name
        self.passwd = passwd
        self.init_amount = init_amount
        self.shopping_car = {}


class ShoppingSystem:
    def __init__(self, goods_info, system_info):
        self.goods_info = goods_info
        self.system_info = system_info
        self.userdict = {}

    # 登录
    def register(self, name, passwd, initial_amount):
        if name not in self.userdict:
            # 创建一个新用户，实例化User类
            user = User(name, passwd, initial_amount)
            # 名字作为key，user对象作为value，存在self.userdict里面
            # {"sc":user对象}
            self.userdict[name] = user
            # 用户信息写入磁盘
            file_name = self.system_info + "_user.pickle"
            # file_name = self.system_info + "_user.json"
            with open(file_name, "wb") as fp:
                # wb  二进制写
                pickle.dump(self.userdict, fp)
            # tmp_dict = {}
            # for k, v in self.userdict.items():
            #     tmp_dict[k] = {"passwd": v.passwd, "init_amount": v.init_amount}
            # with open(file_name, "w") as fp:
            #     fp.write(json.dumps(tmp_dict))
        else:
            print("用户已存在")

    # 加载用户
    def load_user(self):
        file_name = self.system_info + "_user.pickle"
        try:
            with open(file_name, "rb") as fp:
                self.userdict = pickle.load(fp)
        except:
            pass

    # 登录
    def login(self, name, passwd):
        if name in self.userdict:
            if passwd == self.userdict[name].passwd:
                print("登录成功！".center(40, "*"))
                return False
            else:
                print("密码错误,请重新输入")
        else:
            print("没有这个用户，请重新输入")
        return True

    # 加载购物车
    def load_car(self, name):
        file_name =self.system_info + name + "_car.pickle"
        try:
            with open(file_name, "rb") as fp:
                self.userdict[name].shopping_car = pickle.load(fp)
        except:
            pass

    # 查看商品
    def show_goods(self):
        print("商品信息：".center(40, "*"))
        for i, j in self.goods_info.items():
            print(f"商品编号：{i}, 商品：{j['name']}, 价格：{j['price']}")
        # print("商品编号".ljust(10, " "), "商品名字".ljust(10, " "), "商品价格".ljust(10, " 000"))
        # for key in self.goods_info:
            # product_name = self.goods_info[key]["name"]
            # product_price = self.goods_info[key]["price"]
            # print(f"{key}".ljust(15, " "), f"{product_name}".ljust(15, " "), f"{product_price}".ljust(15, " "))

    # 查看购物车
    def show_car(self, name):
        self.load_car(name)
        car = self.userdict[name].shopping_car
        print("购物车中的商品信息：".center(40, "*"))
        for i in car:
            print(f"编号：{i}，名称：{self.goods_info[i]['name']}，价格：{self.goods_info[i]['price']} \
            数量：{self.userdict[name].shopping_car[i]['number']}个")

    # 加购商品
    def goods_add(self, purchase, num, name):
        if purchase not in self.goods_info:
            print("商品不存在".center(40, "*"))
        else:
            self.userdict[name].shopping_car[purchase] = self.goods_info[purchase]
            self.userdict[name].shopping_car[purchase]["number"] = num
            print("加购成功！".center(40, "*"))
            file_name = self.system_info + name + "_car.pickle"
            with open(file_name, "wb") as fp:
                pickle.dump(self.userdict[name].shopping_car, fp)

    # 结算购物车
    def pay_car(self, name):
        pay_money = 0
        total_money = int(self.userdict[name].init_amount)
        for i in self.userdict[name].shopping_car:
            pay_money += self.goods_info[i]["price"] * int(self.userdict[name].shopping_car[i]["number"])
        print(f"需支付{pay_money}元")
        if total_money < pay_money:
            print("余额不足，请充值".center(40, "*"))
        else:
            total_money -= pay_money
            print(f"结算成功！还剩{total_money}元".center(40, "*"))
            self.userdict[name].shopping_car.clear()
            self.userdict[name].init_amount = total_money
            file_name1 = self.system_info + name + "_car.pickle"
            file_name2 = self.system_info + "_user.pickle"
            with open(file_name1, "wb") as fp1:
                pickle.dump(self.userdict[name].shopping_car, fp1)
            with open(file_name2, "wb") as fp2:
                pickle.dump(self.userdict, fp2)

    # 金额
    def user_amount(self, name):
        print(f"您的余额为{self.userdict[name].init_amount}元")
        a = input("是否需要充值，需要按y，不需要按n:")
        if a == "y":
            money = int(self.userdict[name].init_amount)
            m = input("请输入需要充值的金额:")
            if m.isdigit():
                money += int(m)
                file_name = self.system_info + "_user.pickle"
                self.userdict[name].init_amount = money
                with open(file_name, "wb") as fp:
                    pickle.dump(self.userdict, fp)
                print(f"充值成功！余额为{self.userdict[name].init_amount}".center(30, "*"))
            else:
                print("输入字符不合法".center(40, "*"))
        elif a == "n":
            return
        else:
            print("输入不合法".center(40, "*"))

    # 从购物车中移除商品
    def remove_car(self, name, goods, num):
        if goods not in self.userdict[name].shopping_car:
            print("购物车中没有此商品".center(40, "*"))
            return
        numbers = int(self.userdict[name].shopping_car[goods]["number"])
        if num == "all":
            numbers = 0
            print("移除成功！".center(40, "*"))
        elif int(num) > numbers:
            print("购物车中此商品的数量没有这么多".center(40, "*"))
        else:
            numbers -= int(num)
            print("移除成功！".center(40, "*"))
        self.userdict[name].shopping_car[goods]["number"] = numbers
        file_name1 = self.system_info + name + "_car.pickle"
        with open(file_name1, "wb") as fp1:
            pickle.dump(self.userdict[name].shopping_car, fp1)

# 商品种类
fruit_goods = {
    'F001': {"name": "apple", "price": 8},
    'F002': {"name": "banana", "price": 4}
}
medicine_goods = {
    'M001': {"name": "奥司他韦", "price": 60},
    'M002': {"name": "抗病毒口服液", "price": 30}
}

# 购物系统
system1 = ShoppingSystem(fruit_goods, "水果购物系统")
system2 = ShoppingSystem(medicine_goods, "药品购物系统")

system = [system1, system2]

while 1:
    print("当前平台有购物系统如下：")
    for k, v in enumerate(system):
        print(f"{k}.{v.system_info} ")
    c1 = input("请输入你的选择（按q退出）：")
    if c1 == "q":
        break
    if c1.isdigit() and int(c1) < len(system):
        c1 = int(c1)
        current_system = system[c1]
        # 加载用户
        current_system.load_user()
        print(f"欢迎进入{current_system.system_info}！".center(40, "*"))
        # 当前登录用户
        current_user = None
        while 1:
            c2 = input("1.登录\n2.注册\n3.查看商品\n4.查看购物车\n5.添加商品\n6.结算购物车\n7.查看余额\n8.移除商品\n请输入你的选择（按q返回）：")
            if c2 == "q":
                break
            if c2 == "1":
                flag = 1
                while flag:
                    current_user, passwd = input("请输入名字、密码（用空白分隔），输入q 0退出").split()
                    if current_user == "q" and passwd == "0":
                        current_user = None
                        break
                    flag = current_system.login(current_user, passwd)
            elif c2 == "2":
                name, passwd, amount = input("请输入名字、密码、初始金额（用空白分隔）").split()
                current_system.register(name, passwd, amount)
            elif c2 == "3":
                current_system.show_goods()
            elif c2 == "4":
                if current_user == None:
                    print("请先登录!")
                else:
                    current_system.show_car(current_user)
            elif c2 == "5":
                if current_user == None:
                    print("请先登录".center(40, "*"))
                else:
                    while 1:
                        purchased, num = input("请输入你想添加的商品编号及数量（按q 0结束添加）：").split()
                        if purchased == "q":
                            break
                        else:
                            current_system.goods_add(purchased, num, current_user)
            elif c2 == "6":
                if current_user == None:
                    print("请先登录".center(40, "*"))
                else:
                    current_system.pay_car(current_user)
            elif c2 == "7":
                if current_user == None:
                    print("请先登录".center(40, "*"))
                else:
                    current_system.user_amount(current_user)
            elif c2 == "8":
                if current_user == None:
                    print("请先登录".center(40, "*"))
                else:
                    print("输入商品编号和数量，若输入数量为all则清空此商品的数量")
                    goods, num = input("请输入商品编号和数量（空格分开）：").split()
                    current_system.remove_car(current_user, goods, num)
    else:
        print("输入有误，请重新输入（按q退出）：")