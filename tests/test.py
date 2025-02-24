import pytest
from typing import Union
from PIL import Image
import os
import combine_postfits
import matplotlib.pyplot as plt
from matplotlib.testing.compare import compare_images

# Base path
path = os.path.dirname(os.path.dirname(combine_postfits.__path__[0]))

# Get file names
name_dict = {
    example: os.listdir(f"{path}/tests/baseline/{example}/prefit")
    for example in os.listdir(f"{path}/tests/baseline")
}

# Generate all permutations
test_tuples = []
for example, names in name_dict.items():
    for fittype in ["prefit", "fit_s"]:
        for name in names:
            test_tuples.append((example, fittype, name))

# Skip missing
test_tuples = [
    pytest.param(
        example,
        fittype,
        name,
        marks=pytest.mark.skipif(
            not os.path.exists(
                f"{path}/tests/outs/{example}/{fittype}/{name.replace('prefit', fittype)}"
            ),
            reason=f"Path 'outs/{example}/{fittype}/{name.replace('prefit', fittype)}' is missing.",
        ),
    )
    for example, fittype, name in test_tuples
]
print(test_tuples[:2])


@pytest.mark.parametrize(("example", "fittype", "name"), test_tuples)
def test_image(example, name, fittype):
    baseline_image_path = f"{path}/tests/baseline/{example}/{fittype}/{name.replace('prefit', fittype)}"
    test_image_path = f"{path}/tests/outs/{example}/{fittype}/{name.replace('prefit', fittype)}"

    # Use pytest-mpl to compare images
    result = compare_images(baseline_image_path, test_image_path, tol=0, in_decorator=True)

    if result is not None:
        import os
        os.makedirs(f"{path}/tests/failed", exist_ok=True)
        shutil.copy(result['diff'], f"{path}/tests/failed/")
        shutil.copy(result['baseline'], f"{path}/tests/failed/")
        shutil.copy(result['test'], f"{path}/tests/failed/")

    assert result is None, (result['rms'], result['diff'])