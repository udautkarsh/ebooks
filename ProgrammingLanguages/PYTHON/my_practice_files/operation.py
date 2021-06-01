from modules.Employee import Employee
import datetime

emp1 = Employee('Uday', 'singh', 50000)
emp2 = Employee('priya', 'singh', 60000)

print(emp1.email)
print(emp2.email)

print(F"Full Name invoked by object: '{emp1.getFullName()}'")
print(F"Full name invoked by class: '{Employee.getFullName(emp1)}'")
emp1.applyHike()
print(F"Salary of employe1 after pay raise: {emp1.salary}") 

print(Employee.hike)
print(emp1.hike)
print(emp2.hike)
emp2.hike = 1.05
print(emp2.hike)
print(Employee.hike)
print(emp1.hike)
Employee.hike = 1.06
print(Employee.hike)
print(emp1.hike)
print(emp2.hike)

Employee.setHikeAmount(1.09) # this can also be called from an object but it does not make sense to call a class
print(Employee.hike)         # method from any object/instance
print(emp1.hike)
print(emp2.hike)

#call staticmethod
my_date = datetime.date(2021, 5, 20)
print(Employee.is_weekend(my_date))