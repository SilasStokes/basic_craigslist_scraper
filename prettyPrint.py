class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def printError(*args):
    print(bcolors.FAIL, bcolors.BOLD, 'ERROR: ',
          bcolors.ENDC, *args, sep='', end='\n')


def printInfo(*args):
    print(bcolors.OKCYAN, 'INFO: ', bcolors.ENDC, *args, sep='', end='\n')


def printSuccess(*args):
    print(bcolors.OKGREEN, 'OK: ', bcolors.ENDC, *args, sep='', end='\n')


def welcome_message():
    print(f'''
    {bcolors.BOLD}{bcolors.HEADER}Welcome to the craigslist free alert bot  {bcolors.ENDC}
    Every 3 minutes this script will query cl for free items and then print the new items to the terminal and send you a text and/or email.
    cheers!
    ''')
