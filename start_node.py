from Orses_Administrator_Core.Administrator import Admin
from getpass import getpass


# loads or, if not yet created, creates new admin details. Also Creates the necessary database for running node
admin_name = input("admin name: ")
password = getpass("password: ")

admin = Admin(admin_name=admin_name, password=password, newAdmin=False).load_user()
if admin is None:
    ans = input("No admin id under that admin name, would you like to create a new admin id? y/N ")
    if ans.lower() == "y":
        admin = Admin(admin_name=admin_name, password=password, newAdmin=True)

