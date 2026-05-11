Using Constraints to Build Collections
======================================

Constraints are a way to specify the versions of packages that should be used
when building a collection. They are useful when you want to specify a version
of a package other than the default (usually the latest version).

Because several commands in fromager use constraints, you pass them to the base
command using the ``--constraints-file`` option.

For example, if you want to bootstrap a package that requires ``setuptools``
and you want to avoid a breaking change in ``setuptools`` you can create a
constraints file that tells fromager to avoid using the latest version of
``setuptools``:

.. code-block:: text

   setuptools<80.0.0

Then you would run the following command:

.. code-block:: console

   $ fromager --constraints-file constraints.txt bootstrap my-package

This will use the constraints in the ``constraints.txt`` file to build
``my-package``.

Use the same constraints file with ``fromager build-sequence`` when building the
production packages.

.. code-block:: console

   $ fromager --constraints-file constraints.txt build-sequence ./work-dir/build-order.json

This will use the constraints in the ``constraints.txt`` file to build the
production packages for ``my-package``.

Multiple constraints and remote constraints
-------------------------------------------

.. versionchanged:: 0.84.0
   The ``--constraints-file`` / ``-c`` option now supports an arbitrary
   number of arguments.

The ``--constraints-file`` argument can be supplied multiple times. Multiple
occurrences of the same package are merged and validated. For example
``egg>=1.0`` and ``egg!=1.1.2`` are combined into ``egg>=1.0,!=1.1.2``. An
unsatisfiable combination like ``egg<1.0`` and ``egg>2.0`` is an error.

Fromager can load constraints from `https://` URLs, too.

.. code-block:: console

   $ fromager -c constraints.txt -c local-constraints.txt -c https://company.example/security-constraints.txt bootstrap my-package

Blocking packages
-----------------

To block a package entirely so that no version is accepted, use the special
constraint ``<0`` (or equivalently ``<0.0`` or ``<0.0.0``). No valid Python
version can satisfy this specifier, so the package is effectively excluded from
the build.

.. code-block:: text

   unwanted-package<0

A blocked constraint cannot be combined with a regular constraint for the same
package. Adding both will raise an error.
