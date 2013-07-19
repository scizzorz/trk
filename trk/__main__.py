import sys
import bumpy
from . import task

bumpy.config(cli = True, suppress = ('all',))
bumpy.main(sys.argv[1:])
