import pytest
from typing import Union
from PIL import Image
import os 
import combine_postfits

# Base path
path = os.path.dirname(os.path.dirname(combine_postfits.__path__[0]))

# Get file names
name_dict = {example: os.listdir(f'{path}/tests/baseline/{example}/prefit') for example in os.listdir(f'{path}/tests/baseline')}

# Generate all permutations
test_tuples = []
for example, names in name_dict.items():
    for fittype in ['prefit', 'fit_s']:
        for name in names:
            test_tuples.append((example, fittype, name))
            
# Skip missing
test_tuples = [pytest.param(example, fittype, name, 
                            marks=pytest.mark.skipif(not os.path.exists(f"{path}/tests/outs/{example}/{fittype}/{name.replace('prefit', fittype)}"), 
                            reason=f"Path 'outs/{example}/{fittype}/{name.replace('prefit', fittype)}' is missing."))
               for example, fittype, name in test_tuples]

@pytest.mark.parametrize(("example", "fittype", "name"), test_tuples)
def test_image(image_diff, example, name, fittype):
    image: Image or str or bytes = f"{path}/tests/baseline/{example}/{fittype}/{name.replace('prefit', fittype)}"
    image2: Image or str or bytes = f"{path}/tests/outs/{example}/{fittype}/{name.replace('prefit', fittype)}"
    assert image_diff(image, image2, threshold=0.2)            
            