Location module
==============

Provides location information on where a Mac is physical located.

The script uses Apple's CoreLocation framework to determine the approximate latitude, and longitude of a Mac.

Author: Clayton Burlison <https://clburlison.com>  
Created: Jan. 17, 2016  

Based off of works by:  
@arubdesu - https://gist.github.com/arubdesu/b72585771a9f606ad800  
@pudquick - https://gist.github.com/pudquick/c7dd1262bd81a32663f0  
@pudquick - https://gist.github.com/pudquick/329142c1740500bd3797  
@lindes   - https://github.com/lindes/get-location/  
University of Utah, Marriott Library - https://github.com/univ-of-utah-marriott-library-apple/privacy_services_manager  


Limitations
==============

Currently this module is limited to 10.8 - 10.11. On each run Location Services will be enabled, and the system Python binary will be given access to Location Services. Due to how Location Services and the CoreLocation framework interact may take as many as six runs of this script before location data starts to consistently output results. We could resolve this in script with additional CoreLocation queues however since this is designed to be ran non-interactive the trade of additional time isn't worth it.


Notes
==============

The following data is created by this script:

* Latitude - Str, Latitude
* Longitude - Str, Longitude
* LatitudeAccuracy - Int, Latitude Accuracy
* LongitudeAccuracy - Int, Longitude Accuracy
* Altitude - Int, Altitude
* GoogleMap - Str, Pre-populated Google Maps URL
* LastRun - Str, Last run time stored in UTC time
* CurrentStatus - Str, Friendly message describing last run
* LS_Enabled - Bool, are Location Services enabled.