from setuptools import setup, find_packages

setup(name='inome-aws-utils',
      version='0.1',
      description='Collection of AWS utils for inomes use',
      url='http://github.com/inome/utils',
      author='Deepak Konidena, Micah Huff',
      author_email='dkonidena@inome.com,mhuff@inome.com',
      license='N/A',
      requires=['boto>=2.29.1', 'psutil>=2.1.1', 'argparse>=1.1', 'requests>=2.2.1'],
      packages=find_packages(),
      zip_safe=True)

