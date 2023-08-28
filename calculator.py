import math, sys
import logging

class MyCalculator:
    def __init__(self):
        self.choice = ""
        self.ans = 0

    def logger(self, file_name):
        formatter = logging.Formatter(fmt='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
                                    datefmt='%Y/%m/%d %H:%M:%S') # %I:%M:%S %p AM|PM format
        logging.basicConfig(filename = '%s.log' %(file_name),format= '%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
                                    datefmt='%Y/%m/%d %H:%M:%S', filemode = 'w', level = logging.INFO)
        log_obj = logging.getLogger()
        log_obj.setLevel(logging.DEBUG)
        # log_obj = logging.getLogger().addHandler(logging.StreamHandler())

        # console printer
        screen_handler = logging.StreamHandler(stream=sys.stdout) #stream=sys.stdout is similar to normal print
        screen_handler.setFormatter(formatter)
        logging.getLogger().addHandler(screen_handler)

        #log_obj.info("Logger object created successfully.")
        return log_obj

    def __sum(self, x, y):
        return int(x) + int(y)

    def __subtract(self, x, y):
        return int(x) - int(y)

    def __division(self, x, y):
        return float(x) / float(y)

    def __multiply(self, x, y):
        return int(x) * int(y)

    def __square(self, x):
        return int(x) * int(x)

    def __reciprocal(self, x):
        return 1 / float(x)

    def __square_root(self, x):
        return math.sqrt(x)
    
    def calculator(self):

        log_obj = self.logger("logging")

        while True:
            log_obj.info(f"Welcome to calculator!!")
            log_obj.info(f"Choice: \n" +
                "1. sum\n" +
                "2. subtract\n" +
                "3. division\n" +
                "4. multiply\n" +
                "5. square\n" +
                "6. reciprocal\n" +
                "7. square root\n" + 
                "E. Exit"
                )
            
            calc.choice = input("Please select a choice:")
            log_obj.info(f"User selection: {calc.choice}")

            if self.choice.lower() == "e":
                log_obj.info("Goodbye")
                exit(0)
            else:
                first_number = input("Input 1st number:")
                log_obj.info(f"1st number: {first_number}")
                if self.choice == "1" or self.choice =="2" or self.choice =="3" or self.choice == "4":
                    second_number = input("Input 2nd number:")
                    log_obj.info(f"2nd number: {second_number}")

            if self.choice == "1":
                ans = self.__sum(first_number, second_number)
            elif self.choice == "2":
                ans = self.__subtract(first_number, second_number)
            elif self.choice == "3":
                ans = self.__division(first_number, second_number)
            elif self.choice == "4":
                ans = self.__multiply(first_number, second_number)
            elif self.choice == "5":
                ans = self.__square(first_number)
            elif self.choice == "6":
                ans = self.__reciprocal(first_number)
            elif self.choice == "7":
                ans = self.__square_root(first_number)

            log_obj.info(f"Answer: {ans}")


if __name__ == "__main__":
    calc = MyCalculator()
    calc.calculator()


