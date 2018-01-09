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


from eos.const.eve import AttrId
from eos.const.eve import EffectId
from eos.eve_object.effect import EffectFactory
from eos.fit.stats_container import DmgTypesTotal
from .base import DmgDealerEffect


class EmpWave(DmgDealerEffect):

    id = EffectId.emp_wave

    def get_volley(self, item):
        em = item.attrs.get(AttrId.em_dmg)
        thermal = item.attrs.get(AttrId.thermal_dmg)
        kinetic = item.attrs.get(AttrId.kinetic_dmg)
        explosive = item.attrs.get(AttrId.explosive_dmg)
        return DmgTypesTotal(em, thermal, kinetic, explosive)

    def get_dps(self, item, reload):
        cycle_time = self.get_cycle_parameters(item, reload).average_time_inf
        if cycle_time is None:
            return DmgTypesTotal(None, None, None, None)
        volley = self.get_volley(item)
        em = volley.em
        thermal = volley.thermal
        kinetic = volley.kinetic
        explosive = volley.explosive
        try:
            em /= cycle_time
        except TypeError:
            pass
        try:
            thermal /= cycle_time
        except TypeError:
            pass
        try:
            kinetic /= cycle_time
        except TypeError:
            pass
        try:
            explosive /= cycle_time
        except TypeError:
            pass
        return DmgTypesTotal(em, thermal, kinetic, explosive)

    def get_applied_volley(self, item, tgt_data):
        return

    def get_applied_dps(self, item, tgt_data, reload):
        return


EffectFactory.reg_cust_class_by_id(EmpWave)
