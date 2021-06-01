class Employee:
    hike = 1.04 #class variable
    def __init__(self, fname, lname, salary):
        """
        A constructor
        """
        self.fname = fname
        self.lname = lname
        self.salary = salary
        self.email = fname + '.' + lname + '@email.com'
    def getEmail(self):
        """
        Method to get email
        """
        return (self.fname + '.' + self.lname + '@email.com')
    def getFullName(self):
        """
        Method to get full name
        """
        return (self.fname + ' ' + self.lname)
    def applyHike(self):                        #self.salary =  self.salary * Employee.hike #class variable can 
        self.salary = self.salary * self.hike   #be accessed using object reference as well as class refrence.
        return (self.hike)                      #If this variable is not avaiable through obj then it will be
                                                # seen through class in inheritance chain.
        
    @classmethod                       #Class method recevies class object as first argument instead of obj 
    def setHikeAmount(cls, amount):    #references in case of normal methods. Class methods operates on class vars.      
        cls.hike = amount
    @staticmethod
    def is_weekend(day):                              #static methods do not operate on any classA static method is also a method which is bound to the class and not the object of the class
        if day.weekday() == 5 or day.weekday() == 6: #A static method can’t access or modify class state.
            return True                              #It is present in a class because it makes sense for the method to be present in class.
        return False                                                
                                                        