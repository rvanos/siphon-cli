
import getpass

def get_input(prompt, password=False):
    if password:
        return getpass.getpass(prompt)
    else:
        return input(prompt)  # Py3

def yn(msg):
    try:
        valid_response = False
        while not valid_response:
            response = get_input(msg) or 'y'
            if response == 'y' or response == 'Y':
                return True
            elif response == 'n' or response == 'N':
                return False
            else:
                msg = 'Please enter \'y\' or \'n\': '
    except KeyboardInterrupt:
        print()
        return False
