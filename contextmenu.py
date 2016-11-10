import sys
import xbmc
 
if __name__ == '__main__':
    # message = "Clicked on '%s'" % sys.listitem.getLabel()
    message = "This function is not yet implemented!"
    xbmc.executebuiltin("Notification(\"TeamWatch\", \"%s\")" % message)