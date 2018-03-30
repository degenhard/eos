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


from copy import copy

from eos.eve_object.modifier import DogmaModifier
from eos.source import Source
from eos.source import SourceManager
from tests.testcase import EosTestCase
from .environment import CacheHandler


class IntegrationTestCase(EosTestCase):
    """Test case class is used by integration tests.

    Supports almost end-to-end testing of Eos, leaving only data handler, cache
    handler and eve object builder outside of scope.

    Sets up two sources for fit, src1 (default) and src2.
    """

    def setUp(self):
        EosTestCase.setUp(self)
        # Replace existing sources with test source
        self.__backup_sources = copy(SourceManager._sources)
        self.__backup_default_source = SourceManager.default
        SourceManager._sources.clear()
        self._make_source('src1', CacheHandler(), make_default=True)

    def tearDown(self):
        # Revert source change
        SourceManager._sources.clear()
        SourceManager._sources.update(self.__backup_sources)
        SourceManager.default = self.__backup_default_source
        EosTestCase.tearDown(self)

    def _make_source(self, alias, cache_handler, make_default=False):
        source = Source(alias, cache_handler)
        # Add source 'manually' to avoid building cache
        SourceManager._sources[alias] = source
        if make_default is True:
            SourceManager.default = source
        return source

    def mktype(self, *args, src=None, **kwargs):
        """Make item type and add it to source.

        Args:
            src (optional): Source alias to which type should be added. Default
                source is used by default.
            *args: Arguments which will be used to instantiate item type.
            **kwargs: Keyword arguments which will be used to instantiate item
                type.

        Returns:
            Item type.
        """
        if src is None:
            src = SourceManager.default
        else:
            src = SourceManager.get(src)
        return src.cache_handler.mktype(*args, **kwargs)

    def mkattr(self, *args, src=None, **kwargs):
        """Make attribute and add it to default source.

        Args:
            src (optional): Source alias to which attribute should be added.
                Default source is used by default.
            *args: Arguments which will be used to instantiate attribute.
            **kwargs: Keyword arguments which will be used to instantiate
                attribute.

        Returns:
            Attribute.
        """
        if src is None:
            src = SourceManager.default
        else:
            src = SourceManager.get(src)
        return src.cache_handler.mkattr(*args, **kwargs)

    def mkeffect(self, *args, src=None, **kwargs):
        """Make effect and add it to default source.

        Args:
            src (optional): Source alias to which effect should be added.
                Default source is used by default.
            *args: Arguments which will be used to instantiate effect.
            **kwargs: Keyword arguments which will be used to instantiate
                effect.

        Returns:
            Effect.
        """
        if src is None:
            src = SourceManager.default
        else:
            src = SourceManager.get(src)
        return src.cache_handler.mkeffect(*args, **kwargs)

    def mkmod(self, *args, **kwargs):
        """Shortcut to instantiating dogma modifier.

        Args:
            *args: Arguments which will be used to instantiate modifier.
            **kwargs: Keyword arguments which will be used to instantiate
                modifier.

        Returns:
            Dogma modifier.
        """
        return DogmaModifier(*args, **kwargs)

    def allocate_type_id(self, *srcs):
        """Allocate item type ID which is not taken in specified sources.

        Args:
            *srcs: List of source aliases.

        Returns:
            Allocated item type ID.
        """
        if not srcs:
            srcs = [SourceManager.default.alias]
        return max(
            SourceManager.get(src).cache_handler.allocate_type_id()
            for src in srcs)

    def allocate_attr_id(self, *srcs):
        """Allocate attribute ID which is not taken in specified sources.

        Args:
            *srcs: List of source aliases.

        Returns:
            Allocated attribute ID.
        """
        if not srcs:
            srcs = [SourceManager.default.alias]
        return max(
            SourceManager.get(src).cache_handler.allocate_attr_id()
            for src in srcs)

    def allocate_effect_id(self, *srcs):
        """Allocate effect ID which is not taken in specified sources.

        Args:
            *srcs: List of source aliases.

        Returns:
            Allocated effect ID.
        """
        if not srcs:
            srcs = [SourceManager.default.alias]
        return max(
            SourceManager.get(src).cache_handler.allocate_effect_id()
            for src in srcs)

    def assert_fit_buffers_empty(self, fit, clear=True):
        """Checks if fit contains anything in object containers.

        Args:
            fit: Fit to verify.
            clear (optional): Before checking, by default fit has all its items
                removed. If necessary, they can be kept.

        Only containers which are designed to hold temporary data are checked.
        """
        self.__clear_fit(fit, clear)
        entry_num = 0
        entry_num += self._get_obj_buffer_entry_count(
            fit,
            ignore_objs=[fit],
            ignore_attrs=(
                ('Fit', '_Fit__source'),
                ('Fit', '_Fit__incoming_dmg_default'),
                ('Fit', '_Fit__incoming_dmg_rah'),
                ('Fit', '_MsgBroker__subscribers'),
                ('RestrictionService', '_RestrictionService__restrictions')))
        if entry_num:
            plu = 'y' if entry_num == 1 else 'ies'
            msg = '{} entr{} in buffers: buffers must be empty'.format(
                entry_num, plu)
            self.fail(msg=msg)

    def __clear_fit(self, fit, clear_all):
        if clear_all:
            fit.character = None
            fit.ship = None
            fit.stance = None
            fit.effect_beacon = None
            fit.subsystems.clear(),
            fit.modules.high.clear(),
            fit.modules.mid.clear(),
            fit.modules.low.clear(),
            fit.rigs.clear(),
            fit.drones.clear(),
            fit.fighters.clear(),
            fit.skills.clear(),
            fit.implants.clear(),
            fit.boosters.clear()
