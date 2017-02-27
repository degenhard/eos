# ===============================================================================
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
# ===============================================================================


from copy import copy
from itertools import chain

from eos.const.eve import Type
from eos.data.source import SourceManager, Source
from tests.eos_testcase import EosTestCase


class IntegrationTestCase(EosTestCase):
    """
    Additional functionality provided:

    self.assert_fit_buffers_empty -- checks if fit contains anything
        in object containers which are designed to hold temporary data
    """

    def setUp(self):
        super().setUp()
        # Replace existing sources with test source
        self.__sources = copy(SourceManager._sources)
        self.__default_source = SourceManager.default
        SourceManager._sources.clear()
        test_source = Source('test', self.ch)
        SourceManager._sources['test'] = test_source
        SourceManager.default = test_source
        # Instantiate character type, as it's used in every test
        self.ch.type(type_id=Type.character_static)

    def tearDown(self):
        # Revert source change
        SourceManager._sources.clear()
        SourceManager._sources.update(self.__sources)
        SourceManager.default = self.__default_source
        super().tearDown()

    def assert_fit_buffers_empty(self, fit):
        # Temporarily remove all objects which fit has built into it and which
        # are too hard to handle via ignore
        fit_char = fit.character
        fit.character = None
        entry_num = 0
        # Fit itself
        entry_num += self._get_object_buffer_entry_amount(fit, ignore=(
            '_Fit__source', '_Fit__default_incoming_damage', '_MessageBroker__subscribers'
        ))
        # Volatile manager. As volatile manager always has one entry added to it
        # (stats service), make sure it's ignored for assertion purposes
        fit._volatile_mgr._FitVolatileManager__volatile_objects.remove(fit.stats)
        entry_num += self._get_object_buffer_entry_amount(fit._volatile_mgr)
        fit._volatile_mgr._FitVolatileManager__volatile_objects.add(fit.stats)
        # Calculator service
        entry_num += self._get_object_buffer_entry_amount(fit._calculator._CalculationService__affections)
        entry_num += len(fit._calculator._CalculationService__subscribed_affectors)
        # Restriction service
        for restriction in chain(
            fit._restriction._RestrictionService__rests,
            fit._restriction._RestrictionService__rest_regs_stateless,
            *fit._restriction._RestrictionService__rest_regs_stateful.values()
        ):
            entry_num += self._get_object_buffer_entry_amount(restriction)
        # Stats service
        for register in chain(
            fit.stats._StatService__regs_stateless,
            *fit.stats._StatService__regs_stateful.values()
        ):
            entry_num += self._get_object_buffer_entry_amount(register)
        # RAH simulator
        entry_num += self._get_object_buffer_entry_amount(fit._Fit__rah_sim)
        # Restore removed objects
        fit.character = fit_char
        if entry_num > 0:
            plu = 'y' if entry_num == 1 else 'ies'
            msg = '{} entr{} in buffers: buffers must be empty'.format(entry_num, plu)
            self.fail(msg=msg)