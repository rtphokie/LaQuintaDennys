The late great philosopher Mitch Hedberg once said (actually he probably said it may time) "LaQuinta is Spanish for next to Denny's". Fortunately, both LaQuinta and Dennys embed Google Maps on their websites (at differing granularities) including latitudes and longitudes (no geocoding needed), making this very testable.  A SAS blogger took this question on a year ago, but I wanted to see it from more of a heat map approach with a histogram to see how true Hedberg's joke is.
Results:
There are  912 Inns, 152 (17%) are within a mile of a Denny's, 60 (6%) are within 2/10th of a mile, essentially next to.

Data sources:
- lq.com
- dennys.com

Tools used:
- Python (data retrieval, calculation, map and graph generation)
 - pandas (dataframe)
 - matplotlib (histogram, map)
 - geopy (distances between coordinates)
- Photoshop (compositing)

Interesting bits:
- Coordinates for La Quinta Inns are stored to 6 decimal places on its website.  That's an accuracy of ~10 cm or about 10 of the Fruit Loops at the free breakfast buffet (6:00 to 9:30 weekdays and 7:00 to 10:00)
- 57 LaQuinta's have their closest Denny's in another state. This is most common in TN, AL, and NJ
- The LaQuinta is Glendive, MT is 175 miles from the Denny's in Minot, ND, the furthest
