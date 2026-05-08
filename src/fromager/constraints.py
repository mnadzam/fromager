import logging
import pathlib
from collections.abc import Generator

from packaging.requirements import Requirement
from packaging.utils import NormalizedName, canonicalize_name
from packaging.version import Version

from . import requirements_file

logger = logging.getLogger(__name__)


class InvalidConstraintError(ValueError):
    pass


class Constraints:
    def __init__(self) -> None:
        # mapping of canonical names to requirements
        # NOTE: Requirement.name is not normalized
        self._data: dict[NormalizedName, Requirement] = {}

    def __iter__(self) -> Generator[NormalizedName, None, None]:
        yield from self._data

    def __len__(self) -> int:
        return len(self._data)

    def add_constraint(self, unparsed: str) -> None:
        """Add new constraint, must not conflict with any existing constraints

        .. versionchanged: 0.83.0
           Non-conflicting constraints are now combined. Constraints with
           conflicts now raise :exc:`InvalidConstraintError`. Inputs without a
           version specifier or with extras or url are also refused.
        """
        req = Requirement(unparsed)
        canon_name = canonicalize_name(req.name)
        previous = self._data.get(canon_name)

        # validator properties: must have a specifier, must not have extras or URL
        if req.extras:
            raise InvalidConstraintError(f"Constraint {unparsed!r} has extras")
        if req.url:
            raise InvalidConstraintError(f"Constraint {unparsed!r} has an url")
        if not req.specifier:
            raise InvalidConstraintError(f"Constraint {unparsed!r} has no specifiers")

        # verify that incoming constraint is okay by itself
        if req.specifier.is_unsatisfiable():
            raise InvalidConstraintError(f"Constraint {unparsed!r} is unsatisfiable")

        if not requirements_file.evaluate_marker(req, req):
            logger.debug(f"Constraint {req} does not match environment")
            return

        if previous is not None:
            logger.debug("combining constraints %s and %s", previous, req)
            new_specifier = req.specifier & previous.specifier
            if new_specifier.is_unsatisfiable():
                raise InvalidConstraintError(
                    f"Combined specifier '{new_specifier}' is not satisfiable "
                    f"(existing: {previous}, new: {req})"
                )
            req.specifier = new_specifier
        else:
            logger.debug(f"adding constraint {req}")

        self._data[canon_name] = req

    def load_constraints_file(self, constraints_file: str | pathlib.Path) -> None:
        """Load constraints from a constraints file"""
        logger.info("loading constraints from %s", constraints_file)
        content = requirements_file.parse_requirements_file(constraints_file)
        for line in content:
            self.add_constraint(line)

    def get_constraint(self, name: str) -> Requirement | None:
        return self._data.get(canonicalize_name(name))

    def allow_prerelease(self, pkg_name: str) -> bool:
        constraint = self.get_constraint(pkg_name)
        if constraint:
            return bool(constraint.specifier.prereleases)
        return False

    def is_satisfied_by(self, pkg_name: str, version: Version) -> bool:
        constraint = self.get_constraint(pkg_name)
        if constraint:
            return constraint.specifier.contains(version, prereleases=True)
        return True
