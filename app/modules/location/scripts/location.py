#!/usr/bin/python
"""Enables location services (LS) globally,
Give Python access to location services,
Prints the current location to a plist.

Author: Clayton Burlison <https://clburlison.com>
Created: Jan. 17, 2016

Based off of works by:
@arubdesu - https://gist.github.com/arubdesu/b72585771a9f606ad800
@pudquick - https://gist.github.com/pudquick/c7dd1262bd81a32663f0
            https://gist.github.com/pudquick/329142c1740500bd3797
@lindes   - https://github.com/lindes/get-location/
University of Utah, Marriott Library -
            https://github.com/univ-of-utah-marriott-library-apple/privacy_services_manager
"""

from CoreLocation import CLLocationManager, kCLDistanceFilterNone, kCLLocationAccuracyThreeKilometers
from Foundation import NSRunLoop, NSDate, NSObject
import sys, os, plistlib, platform, subprocess, objc
from Foundation import NSBundle
try:
    sys.path.append('/usr/local/munki/munkilib/')
    import FoundationPlist
except ImportError as error:
    print "Could not find FoundationPlist, are munkitools installed?"
    raise error

# Skip manual check
if len(sys.argv) > 1:
    if sys.argv[1] == 'manualcheck':
        print 'Manual check: skipping'
        exit(0)

# Create cache dir if it does not exist
cachedir = '%s/cache' % os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(cachedir):
    os.makedirs(cachedir)

# Define location.plist
location = cachedir + "/location.plist"

plist = []

# Retrieve system UUID
IOKit_bundle = NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')

functions = [("IOServiceGetMatchingService", b"II@"),
             ("IOServiceMatching", b"@*"),
             ("IORegistryEntryCreateCFProperty", b"@I@@I"),
            ]

objc.loadBundleFunctions(IOKit_bundle, globals(), functions)
    
def io_key(keyname):
    return IORegistryEntryCreateCFProperty(IOServiceGetMatchingService(0, IOServiceMatching("IOPlatformExpertDevice")), keyname, None, 0)

def get_hardware_uuid():
    return io_key("IOPlatformUUID")

def root_check():
    """Check for root access."""
    if not os.geteuid() == 0:
        exit("This must be run with root access.")

def os_vers():
    """Retrieve OS version."""
    maj_os_vers = platform.mac_ver()[0].split('.')[1]
    return maj_os_vers

def os_check():
    """Only tested on 10.8 - 10.11. 10.7 should be do-able."""
    if not (8 <= int(os_vers()) <= 11):
        global plist; plist = dict(
            CurrentStatus = "Your OS is not supported at this time: %s." % platform.mac_ver()[0],
        )
        plistlib.writePlist(plist, location)
        exit("This tool only tested on 10.8 - 10.11")

def service_handler(action):
    """Loads/unloads System's location services launchd job."""
    launchctl = ['/bin/launchctl', action,
                 '/System/Library/LaunchDaemons/com.apple.locationd.plist']
    subprocess.check_output(launchctl)

def sysprefs_boxchk():
    """Enables location services in sysprefs globally."""
    uuid = get_hardware_uuid()
    # If dir doesn't exist create it here
    path_stub = "/private/var/db/locationd/Library/Preferences/ByHost/com.apple.locationd."
    das_plist = path_stub + uuid.strip() + ".plist"
    on_disk = FoundationPlist.readPlist(das_plist)
    val = on_disk.get('LocationServicesEnabled', None)
    if val != 1:
        service_handler('unload')
        on_disk['LocationServicesEnabled'] = 1
        FoundationPlist.writePlist(on_disk, das_plist)
        os.chown(das_plist, 205, 205)
        service_handler('load')

def add_python():
    """Python dict for clients.plist in locationd settings."""
    auth_plist = {}
    current_os = int(os_vers())
    if current_os == 11:
        domain = "com.apple.locationd.executable-/System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python"
        auth_plist["BundleId"] = "com.apple.locationd.executable-/System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python"
        auth_plist["Requirement"] = 'cdhash H"13780f41392c7e8f4c8f66891aa4de81b9706653" or cdhash H"4a48b0cc32594f23bbaed9302479a1266f8f6eab"'
    else:
        domain = "org.python.python"
        auth_plist["BundleId"] = "org.python.python"
        auth_plist["BundlePath"] = "/System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app"
        auth_plist["Requirement"] = 'identifier "org.python.python" and anchor apple'
    
    if current_os <= 8:
        auth_plist["RequirementString"] = 'identifier "org.python.python" and anchor apple'
    
    if current_os > 9:
        auth_plist["Registered"] = "/System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python"
    else:
        auth_plist["Registered"] = ""

    auth_plist["Authorized"] = True
    auth_plist["Executable"] = "/System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python"
    auth_plist["Hide"] = 0
    auth_plist["Whitelisted"] = False
    das_plist = '/private/var/db/locationd/clients.plist'
    clients_dict = FoundationPlist.readPlist(das_plist)
    val = clients_dict.get(domain, None)
    need_to_run = False
    try: 
        if val != auth_plist:
            need_to_run = True
    except(TypeError): 
        need_to_run = True

    if need_to_run == True:
        service_handler('unload')
        clients_dict[domain] = auth_plist
        FoundationPlist.writePlist(clients_dict, das_plist)
        os.chown(das_plist, 205, 205)
        service_handler('load')

# Access CoreLocation framework to locate Mac
is_enabled = CLLocationManager.locationServicesEnabled()
is_authorized = CLLocationManager.authorizationStatus()

class MyLocationManagerDelegate(NSObject):
    def init(self):
        self = super(MyLocationManagerDelegate, self).init()
        if not self:
            return
        self.locationManager = CLLocationManager.alloc().init()
        self.locationManager.setDelegate_(self)
        self.locationManager.setDistanceFilter_(kCLDistanceFilterNone)
        self.locationManager.setDesiredAccuracy_(kCLLocationAccuracyThreeKilometers)
        self.locationManager.startUpdatingLocation()
        return self
    def locationManager_didUpdateToLocation_fromLocation_(self, manager, newloc, oldloc):
        lat = newloc.coordinate().latitude
        lon = newloc.coordinate().longitude
        verAcc = newloc.verticalAccuracy()
        horAcc = newloc.horizontalAccuracy()
        altitude = newloc.altitude()
        time = newloc.timestamp()
        gmap = ("http://www.google.com/maps/place/" + str(lat) + "," + str(lon) +
            "/@" + str(lat) + "," + str(lon) + ",18z/data=!3m1!1e3")
        
        global plist; plist = dict(
            Latitude = str(lat),
            Longitude = str(lon),
            LatitudeAccuracy = int(verAcc),
            LongitudeAccuracy = int(horAcc),
            Altitude = int(altitude),
            GoogleMap = str(gmap),
            LastRun = str(time),
            CurrentStatus = "Successful",
            LS_Enabled = is_enabled,
        )
    def locationManager_didFailWithError_(self, manager, err):
        if (is_enabled == True):
            if (is_authorized == 3):
                status = "Unable to locate"
            if (is_authorized == 2):
                status = "Denied"
            if (is_authorized == 1):
                status = "Restricted"
            if (is_authorized == 0):
                status = "Not Determined"
        else:
            status = "Location Services Disabled"
        
        global plist; plist = dict(
            CurrentStatus = "Unsuccessful: " + status,
            LS_Enabled = is_enabled,
        )

def main():
    "Enable LS, allow Python to access to LS, and find current location."
    root_check()
    os_check()
    sysprefs_boxchk()
    add_python()
    
    finder = MyLocationManagerDelegate.alloc().init()
    for x in range(2):
         NSRunLoop.currentRunLoop(
             ).runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(1))
    plistlib.writePlist(plist, location)

if __name__ == '__main__':
    main()