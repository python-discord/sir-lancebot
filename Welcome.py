try:
    Usern = input("Please Enter your name: ")
        #giving values to languages
        #France
    def France():
        print('Bonjour!',Usern)

        #English
    def English():
        print('Hello!',Usern)

        #German
    def German():
        print('Hallo!',Usern)

        #Japanese
    def Japanese():
        print('こんにちは！',Usern)
        #Estonian
    def Estonian():
        print('Tere!',Usern)
        #Dutch
    def Dutch():
        print('Hallo!',Usern)
        #hindi
    def Hindi():
        print('नमस्कार!',Usern)
        #malayalam
    def Malayalam():
        print('ഹലോ!',Usern)
        #spanish
    def Spanish():
        print('¡Hola!',Usern)
        #vietnamese
    def Vietnamese():
        print('Xin chào!',Usern)

        #user input
    Userl = int(input("1. France\n "\
                    "2. English\n "\
                    "3. German\n "\
                    "4. Japanese\n "\
                    "5. Estonian\n "\
                    "6. Dutch\n "\
                    "7. Hindi\n "\
                    "8. Malayalam\n "\
                    "9. Spanish\n "\
                    "10. Vietnamese\n "\
                    "Please enter the corresponding number of your selected language: "))

        #output
    if Userl == 1:
        France()

    if Userl == 2:
        English()

    if Userl == 3:
        German()

    if Userl == 4:
        Japanese()

    if Userl == 5:
        Estonian()

    if Userl == 6:
        Dutch()

    if Userl == 7:
        Hindi()

    if Userl == 8:
        Malayalam()

    if Userl == 9:
        Spanish()

    if Userl == 10:
        Vietnamese()

    else: print('Error: There was an error, enter the number that corresponds to the language you are selecting and try again')

except Exception as e:
    print('Error: There was an Error, please try again (You probably entered the wrong input. Try again, and enter the number that corresponds to your selected language)' )
