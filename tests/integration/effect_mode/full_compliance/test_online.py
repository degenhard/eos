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


from eos import *
from eos.const.eve import EffectCategoryId, EffectId
from tests.integration.effect_mode.effect_mode_testcase import (
    EffectModeTestCase)


class TestFullComplianceOnline(EffectModeTestCase):

    def test_running_normal(self):
        effect = self.ch.effect(
            category_id=EffectCategoryId.online, modifiers=[self.modifier])
        online_effect = self.ch.effect(
            effect_id=EffectId.online, category_id=EffectCategoryId.online)
        item = ModuleHigh(
            self.ch.type(
                attributes={self.tgt_attr.id: 10, self.src_attr.id: 2},
                effects=[effect, online_effect]).id,
            state=State.online)
        # Action
        self.fit.modules.high.append(item)
        # Verification
        self.assertAlmostEqual(item.attributes[self.tgt_attr.id], 12)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_stopped_no_online_effect(self):
        effect = self.ch.effect(
            category_id=EffectCategoryId.online, modifiers=[self.modifier])
        item = ModuleHigh(
            self.ch.type(
                attributes={self.tgt_attr.id: 10, self.src_attr.id: 2},
                effects=[effect]).id,
            state=State.online)
        # Action
        self.fit.modules.high.append(item)
        # Verification
        self.assertAlmostEqual(item.attributes[self.tgt_attr.id], 10)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)
