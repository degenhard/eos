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


from eos import *
from eos.const.eos import ModifierTargetFilter, ModifierDomain, ModifierOperator
from eos.const.eve import EffectCategory
from eos.data.cache_object.modifier import DogmaModifier
from tests.integration.calculator.calculator_testcase import CalculatorTestCase


class TestCleanupChainAddition(CalculatorTestCase):
    """Check that added item damages all attributes which are now relying on its attributes"""

    def test_attribute(self):
        # Setup
        attr1 = self.ch.attribute()
        attr2 = self.ch.attribute()
        attr3 = self.ch.attribute()
        modifier1 = DogmaModifier(
            tgt_filter=ModifierTargetFilter.item,
            tgt_domain=ModifierDomain.ship,
            tgt_attr=attr2.id,
            operator=ModifierOperator.post_mul,
            src_attr=attr1.id
        )
        effect1 = self.ch.effect(category=EffectCategory.passive, modifiers=[modifier1])
        modifier2 = DogmaModifier(
            tgt_filter=ModifierTargetFilter.domain,
            tgt_domain=ModifierDomain.ship,
            tgt_attr=attr3.id,
            operator=ModifierOperator.post_percent,
            src_attr=attr2.id
        )
        effect2 = self.ch.effect(category=EffectCategory.passive, modifiers=[modifier2])
        implant_item = Implant(self.ch.type(effects=[effect1], attributes={attr1.id: 5}).id)
        ship_item = Ship(self.ch.type(effects=[effect2], attributes={attr2.id: 7.5}).id)
        rig_item = Rig(self.ch.type(attributes={attr3.id: 0.5}).id)
        self.fit.ship = ship_item
        self.fit.rigs.add(rig_item)
        self.assertAlmostEqual(rig_item.attributes[attr3.id], 0.5375)
        # Action
        self.fit.implants.add(implant_item)
        # Verification
        # Added item must clean all already calculated attributes
        # which are now affected by it, to allow recalculation
        self.assertAlmostEqual(rig_item.attributes[attr3.id], 0.6875)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(self.fit)