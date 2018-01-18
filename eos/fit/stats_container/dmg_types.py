# ==============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2017 Anton Vorobyov
#
# This file is part of Eos.
#
# Eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Eos. If not, see <http://www.gnu.org/licenses/>.
# ==============================================================================


from numbers import Real

from eos.util.cached_property import cached_property
from eos.util.repr import make_repr_str


class DmgTypes:
    """Container for damage data stats."""

    def __init__(self, em, thermal, kinetic, explosive):
        self.__em = em
        self.__thermal = thermal
        self.__kinetic = kinetic
        self.__explosive = explosive

    @property
    def em(self):
        return self.__em

    @property
    def thermal(self):
        return self.__thermal

    @property
    def kinetic(self):
        return self.__kinetic

    @property
    def explosive(self):
        return self.__explosive

    @classmethod
    def _combine(cls, dmg_containers, tgt_resists=None):
        """Create new instance of container based on passed containers."""
        em = None
        thermal = None
        kinetic = None
        explosive = None
        # Sum up passed damage stats
        for dmg_container in dmg_containers:
            if em is None:
                em = dmg_container.em
            else:
                try:
                    em += dmg_container.em
                except TypeError:
                    pass
            if thermal is None:
                thermal = dmg_container.thermal
            else:
                try:
                    thermal += dmg_container.thermal
                except TypeError:
                    pass
            if kinetic is None:
                kinetic = dmg_container.kinetic
            else:
                try:
                    kinetic += dmg_container.kinetic
                except TypeError:
                    pass
            if explosive is None:
                explosive = dmg_container.explosive
            else:
                try:
                    explosive += dmg_container.explosive
                except TypeError:
                    pass
        # Reduce resulting damage by resists, if needed
        if tgt_resists is not None:
            try:
                em *= 1 - tgt_resists.em
            except TypeError:
                pass
            try:
                thermal *= 1 - tgt_resists.thermal
            except TypeError:
                pass
            try:
                kinetic *= 1 - tgt_resists.kinetic
            except TypeError:
                pass
            try:
                explosive *= 1 - tgt_resists.explosive
            except TypeError:
                pass
        return cls(em, thermal, kinetic, explosive)

    @classmethod
    def _derive(cls, dmg_types, func):
        """Create new damage type instance based on already existing one.

        Args:
            dmg_types: Damage type container which serves as base data.
            func: Modification to apply to each damage type value.
        """
        em = dmg_types.em
        thermal = dmg_types.thermal
        kinetic = dmg_types.kinetic
        explosive = dmg_types.explosive
        try:
            em = func(em)
        except TypeError:
            pass
        try:
            thermal = func(thermal)
        except TypeError:
            pass
        try:
            kinetic = func(kinetic)
        except TypeError:
            pass
        try:
            explosive = func(explosive)
        except TypeError:
            pass
        return cls(em, thermal, kinetic, explosive)

    # Iterator is needed to support tuple-style unpacking
    def __iter__(self):
        yield self.em
        yield self.thermal
        yield self.kinetic
        yield self.explosive

    def __eq__(self, other):
        return all((
            self.em == other.em,
            self.thermal == other.thermal,
            self.kinetic == other.kinetic,
            self.explosive == other.explosive))

    def __hash__(self):
        return hash((
            self.__class__.__name__,
            self.em,
            self.thermal,
            self.kinetic,
            self.explosive))

    def __repr__(self):
        spec = ['em', 'thermal', 'kinetic', 'explosive']
        return make_repr_str(self, spec)


class DmgTypesTotal(DmgTypes):
    """Container for damage data stats, which also calculates total damage.."""

    @cached_property
    def total(self):
        total = (
            (self.em or 0) +
            (self.thermal or 0) +
            (self.kinetic or 0) +
            (self.explosive or 0))
        if total == 0 and (
            self.em is None and
            self.thermal is None and
            self.kinetic is None and
            self.explosive is None
        ):
            return None
        return total

    def __iter__(self):
        for item in DmgTypes.__iter__(self):
            yield item
        yield self.total

    def __repr__(self):
        spec = ['em', 'thermal', 'kinetic', 'explosive', 'total']
        return make_repr_str(self, spec)


class DmgProfile(DmgTypes):
    """Stats container intended to store damage profile.

    Raises:
        TypeError: If any of passed values is not a number.
        ValueError: If any of passed values are less than zero, or if their sum
            is not strictly greater than zero.
    """

    def __init__(self, em, thermal, kinetic, explosive):
        if not all((
            isinstance(em, Real),
            isinstance(thermal, Real),
            isinstance(kinetic, Real),
            isinstance(explosive, Real)
        )):
            raise TypeError('all damage types must be numbers')
        if not all((
            em >= 0,
            thermal >= 0,
            kinetic >= 0,
            explosive >= 0,
            em + thermal + kinetic + explosive > 0
        )):
            msg = (
                'all damage types must be non-negative numbers '
                'with positive sum')
            raise ValueError(msg)
        DmgTypes.__init__(self, em, thermal, kinetic, explosive)


class ResistProfile(DmgTypes):
    """Stats container intended to store resistance profile.

    Raises:
        TypeError: If any of passed values is not a number.
        ValueError: If any of passed values are less than 0 or greater than 1.
    """

    def __init__(self, em, thermal, kinetic, explosive):
        if not all((
            isinstance(em, Real),
            isinstance(thermal, Real),
            isinstance(kinetic, Real),
            isinstance(explosive, Real)
        )):
            raise TypeError('all resistances must be numbers')
        if not all((
            0 <= em <= 1,
            0 <= thermal <= 1,
            0 <= kinetic <= 1,
            0 <= explosive <= 1
        )):
            raise ValueError('all resistances must be within range [0, 1]')
        DmgTypes.__init__(self, em, thermal, kinetic, explosive)