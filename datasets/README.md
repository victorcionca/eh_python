# Energy Harvesting traces

Obtained from
* _EnHANTs project_ [http://enhants.ee.columbia.edu/] M. Gorlatova, A. Wallwater, and G. Zussman. Networking low-power energy harvesting devices: Measurements and algorithms. In INFOCOM, 2011 Proceedings IEEE, pages 1602–1610, 2011.
* _NSRDB database_, [http://rredc.nrel.gov/solar/old data/nsrdb/1991-2010/].

Format: measurement index, value (solar irradiation in microW/cm2)

## EnHANTs data set

* columbia_irr_only_no_gaps.csv
* 198 days of uninterrupted solar irradiation measurements
* 30s intervals
* stationary measurement Setup D was used
* collected between the 5th of November 2009 until the 29th of September 2010
* position: south-facing windowsill.

## NSRDB data sets
* six weather stations spanning up to 14 years at one hour sampling rate
* weather stations used: 
  * 724125, years 2001-2005
  * 724699, years 1996-2005
  * 724776, years 1995-2002
  * 725315, years 2000-2005
  * 726830, years 1995-2005
  * 726883, years 1995-2005
  * 726930, years 1992-2005
* used the _Measured global horizontal_ feature defined as "the total amount of direct and diffuse solar radiation received on a horizontal surface" during a 60-minute period.

Pre-processing of data sets:

Some samples were missing from the data sets. Data from one year of measurements was only used if the number of missing samples was less than fifty. Then, if more than four hours of samples were missing in a single day, the entire day was removed, which happened for less than ten days for the entire data collection. Remaining gaps were corrected through interpolation. Finally, for each station, a single data set was produced concatenating all the usable years.

More information and mapping of weather station ids available in the NSRDB manual:
 S. Wilcox. National solar radiation database 1991–2010 update: User’s
manual. NREL/TP-5500-54824 NREL/TP-5500-54824, National Re-
newable Energy Laboratory, August 2012.

