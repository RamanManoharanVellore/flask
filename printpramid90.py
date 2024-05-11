pattern = int(input("Enter the Value to Print:"))


for i in range (0,pattern):
    for j in range (0, i+1):
        print("* ", end = '')
    print(' ')

print("\nInverse Triangle at 90-degree angle:")
for i in range(pattern, 0,-1):
    for j in range(0, i):
        print("* ", end='')
    print()

print("\n Traiangle")

for i in range(0, pattern):
    for k in range(0, pattern-i-1):
        print(' ', end ='')
    for j in range(0, i+1):
        print('* ', end = '')
    print('')

for i in range(pattern, 0, -1):
    for k in range(0, pattern-i-1):
        print(' ', end ='')
    for j in range(0, i+1):
        print('* ', end = '')
    print('')

    