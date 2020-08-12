d = {'Hello':'Hi', 'Bye':'Goodbye', 'List':'Array'}

x = input('Введите значение')
for key, value in d.items():
    if x == value:
        print(key)

#print(d.get(x))