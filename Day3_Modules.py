print('''This is Day3_Modules file
      Info: www.google.com''')

def typecasting(what):
            what=str(what)
            return what

def check_palindromes(word:str):
    if type(word)==str:
        word=word.upper()
        if word==word[::-1]:
            return "a Palindrome"
        else:
            return "not a Palindrome"
    else:
        print("Type casting to String")
        new_word=typecasting(word)
        returning_from_here=check_palindromes(new_word)
        return returning_from_here
    
def fibo_no(how_many):
    fibo=[0,1]
    for i in range (how_many-2):
        last_number=fibo[-1]
        second_last_number=fibo[-2]
        next_number=last_number+second_last_number
        fibo.append(next_number)
    return fibo

def prime_number(number):
    for i in range (2,number):
        if number%i==0:
            print(f"{number} is not a Prime Number ")
            break
        # else:
        #     print("It is a Prime Number")
    
    else: #if for loop is completely checked but not divisible by anything then else will start
        print(f"{number} is a prime number")

def sum_of_natural_numbers(n):
    result=0
    for i in range(1,n+1):
        result+=i
    return result


def factorial(n):
    result=1
    for i in range(1,n+1):
        result*=i
    print(f"Combinations of {n} digits are {result}")

def args_example(*args): #*args take multiple values and store it as a tuple
    print(args, type(args))
          
def total_sales(*args):
    #result=sum(args) #This is the same usinf sum() method
    result=0
    for i in args:
        result+=i
    return result

def minimum(*args):
    min_element=args[0]
    for i in args[1:]:
        if min_element>i:
            min_element=i
    return min_element

def maximum(*args):
    max_element=args[0]
    for i in args[1:]:
        if max_element<i:
            max_element=i
    return max_element

def add_hashtag(*names):
    result=[]
    for i in names:
        result.append('#'+i.upper())
    return result

def student_records(**kwargs):
    #keys=list(kwargs) #Type Casting will provide us the keys of the dictionary
    
    try:
        result=pd.DataFrame(kwargs)
        return result
    except:
        result=pd.DataFrame(kwargs, index=[1])
        return result
    
def show_time():
    try:
        while True:
            print(time.asctime())
            time.sleep(1)
            display(clear=True)
    except:
        print("Timer Stopped")