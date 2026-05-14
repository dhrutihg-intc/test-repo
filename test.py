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

#@title Develop a tuple
my_tuple = (1,'Bravo',True,  'My Number is {}'.format(2), [1,x, True, 'Hello Students'])
print("This is my tuple: \n{}".format(my_tuple))

#@title Different ways of indexing
x = my_tuple[0]
y = my_tuple[2]
z = my_tuple[-1] 
u = my_tuple[0:3]
v = my_tuple[3:]
t = my_tuple[:2]
w = my_tuple[-3:-1]
q = my_tuple[-1][2]

#@title Print variables
print('x is: ', x)
print('y is: ', y)
print('z is: ', z)
print('u is: ', u)
print('v is: ', v)
print('t is: ', t)
print('w is: ', w)
print('q is: ', q)

#@title Tuples are not appendable!
# Tuples are not appendable!
#@title Append a tuple into a list 
my_list.append(my_tuple)
print("tuple appended to list")
print(my_list)

#@title Built-in function "list"
my_list_2 = list(my_tuple)
print(my_list_2)

#@title Built-in function "tuple"
my_tuple_2 = tuple(my_list)
print("Tuple 2")
print(my_tuple_2)

#@title Built-in function "len"
my_list_size  = len(my_list)
my_tuple_size = len(my_tuple)

print("Number of elemenets of my list is {}".format(my_list_size))
print("Number of elemenets of my tuple is {}".format(my_tuple_size))


#@title Develop a dictionary
my_dictionary = {'key_name_1' : my_list, 'key_name_2':my_tuple, 'key_name_3': type(23)}
print(my_dictionary)

#@title Built-in "key" function
my_dictionary_keys = my_dictionary.keys()
print("my_dictionary_keys are: \n{}".format(my_dictionary_keys))

#@title List of keys
my_dictionary_keys = list(my_dictionary_keys)
print("my_dictionary_keys are: \n{}".format(my_dictionary_keys))

#@title Indexing by key string
print(my_dictionary['key_name_2'])

#@title Indexing by element of key list
print(my_dictionary[my_dictionary_keys[2]])

#@title Loop over elements of a list
my_list_01 = [3,1,7,3,9,1]
my_list_02 = []

for i0 in my_list_01:
  my_list_02.append(i0 ** 2)
  print(my_list_02)

#@title Develop a function
def fun_test_02(start_val = 0, stop_val = 10, step_val = 1):
  for i0 in range(start_val, stop_val, step_val):
    if i0%4 == 0:
      print("{} is dividable by '4'".format(i0))
    elif i0%2 == 0:
      print("{} is NOT dividable by '4' but is dividable by 2".format(i0))
    else:
      print('we have no comment for {}'.format(i0))
      
fun_test_02(start_val = -5, stop_val = 20)