try:
    #setting values
    #Addition
    def Add(num1,num2):
        return num1 + num2

    #Subtraction
    def subtract(num1,num2):
        return num1 - num2

    #Multiplication
    def multiply(num1,num2):
        return num1 * num2

    #division
    def divide(num1,num2):
        return num1 / num2

    #taking the numbers
    try:
        select = int(input( "1.Add\n "\
                            "2.Subtract\n "\
                            "3.Multiply\n "\
                            "4.divide\n "\
                            "5.All\n "\
                            "Select the operation you want to use by entering its corresponding number( 1, 2, 3, 4, etc.) :"))

        num1 = int(input('Enter your first number: '))
        num2 = int(input('Enter your second number: '))

        #calculation
        #addition
        if select == 1:
            print('Answer is',num1,"+",num2,"=",
                        Add(num1,num2))
        #Subtraction
        if select == 2:
            print('Answer is',num1,"-",num2,"=",
                        subtract(num1,num2))
        #Multiplication
        if select == 3:
            print('Answer is',num1,"*",num2,"=",
                        multiply(num1,num2))
        #division
        if select == 4:
            print('Answer is',num1,"/",num2,"=",
                        divide(num1,num2))
        if select == 5:
            print('1. Answer in Addition is',num1,"+",num2,"=",
                        Add(num1,num2),'\n'\
                        '2. Answer in Subtraction is',num1,"-",num2,"=",
                                    subtract(num1,num2),'\n'\
                                    '3. Answer in Multiplication is',num1,"*",num2,"=",
                                                multiply(num1,num2),'\n'\
                                                '4. Answer in Division is',num1,"/",num2,"=",
                                                            divide(num1,num2))

except Exception as e:print("Error: There was an error, please try again")
