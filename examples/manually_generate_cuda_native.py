import lettuce as lt
from lettuce import cuda_native

from os.path import join, dirname, abspath, isdir, exists
from os import mkdir, listdir, remove, rmdir


def ensure_empty_dir(path):
    """
    shutil.rmtree + os.mkdir is not always working.
    Therefore, this utility ensures the expected behaviour more safely.
    """

    if exists(path):
        for filename in listdir(path):
            filepath = join(path, filename)
            if isdir(filepath):
                ensure_empty_dir(filepath)
                rmdir(filepath)
            else:
                remove(filepath)
    else:
        mkdir(path)


def main(verbose=False, install=False):
    """
    Generate a cuda_native module into a local directory to get insights.
    """

    # Step 1: Create the collision, boundary, and equilibrium objects.
    collision = cuda_native.ext.NativeBGKCollision()
    boundaries = [
        cuda_native.ext.NativeBounceBackBoundary(1),
        cuda_native.ext.NativeBounceBackBoundary(2)
    ]
    equilibrium = cuda_native.ext.NativeQuadraticEquilibrium()

    # Step 2: Initialize the generator with the D2Q9 lattice, collision, boundaries, and equilibrium.
    generator = cuda_native.Generator(lt.D2Q9(), collision, boundaries, equilibrium)

    # Step 3: Prepare the directory where the generated cuda_native module will be saved.
    generate_dir = abspath(join(dirname(__file__), 'cuda_native'))
    ensure_empty_dir(generate_dir)

    # Step 4: Generate the cuda_native module and format it into the prepared directory.
    structured_code = generator.generate()  # collect all code snippets
    generator.format(structured_code, generate_dir)  # apply code to template files

    if verbose:
        for key, buffer in structured_code.items():
            print(f"{key}:")
            for line in buffer.splitlines():
                print(f"> {line}")
            print()

    # Step 5: optionally install the generated directory
    if install:
        generator.install(generate_dir)


if __name__ == '__main__':
    main()
