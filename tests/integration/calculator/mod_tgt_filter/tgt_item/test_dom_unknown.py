# ==============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2018 Anton Vorobyov
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


from eos import Ship
from eos.const.eos import ModDomain
from eos.const.eos import ModOperator
from eos.const.eos import ModTgtFilter
from eos.const.eve import EffectCategoryId
from tests.integration.calculator.testcase import CalculatorTestCase


class TestTgtItemDomainUnknown(CalculatorTestCase):

    def test_combination(self):
        tgt_attr = self.mkattr()
        src_attr = self.mkattr()
        invalid_modifier = self.mkmod(
            tgt_filter=ModTgtFilter.item,
            tgt_domain=1972,
            tgt_attr_id=tgt_attr.id,
            operator=ModOperator.post_percent,
            src_attr_id=src_attr.id)
        valid_modifier = self.mkmod(
            tgt_filter=ModTgtFilter.item,
            tgt_domain=ModDomain.self,
            tgt_attr_id=tgt_attr.id,
            operator=ModOperator.post_percent,
            src_attr_id=src_attr.id)
        effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=(invalid_modifier, valid_modifier))
        item = Ship(self.mktype(
            attrs={src_attr.id: 20, tgt_attr.id: 100},
            effects=[effect]).id)
        # Action
        self.fit.ship = item
        # Verification
        self.assertAlmostEqual(item.attrs[tgt_attr.id], 120)
        # Cleanup
        self.assert_solsys_buffers_empty(self.fit.solar_system)
        self.assert_log_entries(0)
