# Changelog

### v6.0.1 (25.5.2025)

- Fixed issues arising from the upgrade of the project to Python 3

Authors: Marta Kaliaeva, Lukáš Drahník

### v6.0.0 (29.4.2025)

The modifications have primarily affected the compound search functionality. However, there are also some GUI changes. The extended version of mmass (“mMassX“) includes the following new features/extensions:

-	Changes in “Adduct” column appearing in “Compound Search” panel. Format changed, now displaying for example [M+H]+ or [M+Na]+, instead of empty value for hydrogen adduct or Na+.

-	Added new buttons to panel “Compound Search” for correct annotations of 13C and 15N isotope variant or its combination, which might be useful for metabolomics studies where annotation of particular isotope is required.

-	New column “Isotope” added to panel “Compound Search”. Selected isotopes of 13C or 15N (or both) are displayed in this panel.

-	Changes in “m/z” column in “Compound Search” panel. Column renamed to “m/z database”, as the mass of the compound displayed here is theoretical value computed from formula in database (Libraries/Compounds).

-	New column “m/z measured” added to panel “Compound Search”. After matching peak m/z, mass error in ppm is given and real peak m/z value appears in this column.

-	New ion/adduct variants added. In negative mode we added [M-CH3]-, [M-C3H10N]- and [M-C5H12N]- ions which might be relevant under certain conditions for (lyso)phosphatidylcholines and (lyso)phosphatidic acids. We also added 2M type ions, both in positive and negative mode. Next, we added main ions after derivatization with FMP-10 matrix and AMPP derivatization.

-	We added “Cubic” calibration method to panel “Calibrations”.

-	We grabbed publicly available HMDB v5 database and added it into “Libraries/Compounds”. The whole database is large so we split it according to provider’s annotations into four main parts: Quantified, Detected, Expected and Predicted. We made combination of Quantified and Detected which we think might be useful. 

-	Minor formatting changes, such as adjusting decimal places, table sizes, column sizes, and text formatting.

-	The sorting system in the “Compound Search” panel has been improved so that compounds can be sorted by m/z values in ascending or descending order. Sorting by compound name in alphabetical order is also possible.

Authors: František Malinka, Marta Kaliaeva, Lukáš Kučera, Lukáš Drahník