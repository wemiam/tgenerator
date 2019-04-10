echo "start build"

react-scripts build

source_path=./build
target_path_templates=../TaxonomyBE_0914/templates
target_path_static=../TaxonomyBE_0914/static

rm $target_path_static/js/*.*
rm $target_path_static/css/*.*

cp -Rf $source_path/static/ $target_path_static/
cp $source_path/asset-manifest.json $target_path_static/
cp $source_path/favicon.ico $target_path_static/
cp $source_path/index.html $target_path_templates/
cp $source_path/manifest.json $target_path_static/

echo "end build"
