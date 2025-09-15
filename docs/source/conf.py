# Configuration file for the Sphinx documentation builder.
import pathlib
import sys

sys.path.insert(0, pathlib.Path(__file__).parents[2].resolve().as_posix())

# -- Project information

project = 'Mobility'
copyright = '2023, MIT Licence'
author = 'Multiple authors'

release = '0.1'
version = '0.1'

# -- General configuration

html_theme = "sphinx_rtd_theme"

extensions = [
    'myst_parser',
    'sphinx_copybutton',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
]
