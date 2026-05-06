print("hello")
a= 10
b=20
c = a*b
d = a+b+c
print(a)
print(b)
print(c)
print(d)

print(type(a))
print("My name is {}, my number is {}, and my number type is {}".format('John', 23, type(23)   )   )
print((2/4*5+(3*7+2)**3)**(0.5))
#@title Variable assignments and naming
x = 2 + 2.43
y = 2/5
z = 2!=4
u = 3>2.3
v = 2/5 == 0.5
z = 2>4 or 3>1
t = 2>4 and 3>1 or z

wQ_W_01_2 = x*y

print(x, y , z , u, v, z, t, wQ_W_01_2)
print('.....')

print("The values of x is {}, y is {}, z is {}, u is {}, v is {}, w is {} and t is {} ".format(x, y,z, u, v ,wQ_W_01_2 ,t))
print('.....')

#list demo
my_list = [1,'Bravo',True, 3.32123123, 2/45, 1!=6, 'My Number is {}'.format(2), [1,x, True, 'Hello Students']  ]
print("This is my list: \n{}".format(my_list))
print(my_list[0])

first_element = my_list[0]
last_element = my_list[-1]
range_list = my_list[0:3]
range2= my_list[-3:-1]
select_element_nest_list = my_list[-1][1]

print("first elemnt of list {}". format(first_element))
print("last elemnt of list {}". format(last_element))
print("1st to 3rd elemnt of list {}". format(range_list))
print("last 3 elemnt of list {}". format(range2))
print("second elemnt of last nested list is {}", format(select_element_nest_list))


#list appending example

my_list.append("appended string")
print(my_list)