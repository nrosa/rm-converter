# How to run

## Creating a Rockmaker xml file

`python3 create_rxml.py --design-xml DESIGN_FILE_LOCATION --recipe-xml RECIPE_FILE_LOCATION --output-xml OUTPUT_FILE_LOCATION`

By default aliases are not imported this can be changed adding the flag --include-aliases

eg.
`python3 create_rxml.py --design-xml Shotgun.xml --recipe-xml Shotgun_recipe.xml --output-xml Shotgun_rxml.xml`

## Creating a CrystalTrak recipe file

python3 