# How to run

## Creating a Rockmaker xml file

`python3 create_rxml.py --design-xml DESIGN_FILE_LOCATION --recipe-xml RECIPE_FILE_LOCATION --output-xml OUTPUT_FILE_LOCATION`

`--recipe-xml` The file location of the xtaltrak recipe to be converted.
`--design-xml` The file location of the xtaltrak design to be converted.
`--output-xml` The file location of the created rockmacker design. A default value of `rockmaker_design.xml` is used if no value is supplied.
`--data-dir` The location of a directory that holds all the required datafiles. A default value of `data` is used if no value is supplied.


By default aliases are not imported this can be changed adding the flag --include-aliases

eg.
`python3 -m rmconverter.create_rxml --design-xml Shotgun.xml --recipe-xml Shotgun_recipe.xml --output-xml Shotgun_rxml.xml`

## Creating a CrystalTrak recipe file

`python3 -m rmconverter.create_xtaltrak_recipe --rmxml RMXML_FILE_LOCATION --volume VOLUME --output-xml OUTPUT_FILE_LOCATION`

`--rmxml` The file location of the Rockmaker XML file to be converted.
`--volume` The desired volume of the recipe, supplied in microlitres (uL). A default value of 1500 is used if no volume is supplied.
`--output-xml` The file location of the created recipe. A default value of `xtaltrak_recipe.xml` is used if no value is supplied.

eg.
`python3 -m rmconverter.create_xtaltrak_recipe --rmxml Shotgun_rmxml.xml --volume 1500 --output-xml Shogun_recipe.xml`
