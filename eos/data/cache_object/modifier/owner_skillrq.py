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


from eos.const.eos import ModifierType, ModifierDomain
from .abc import BaseModifier


class OwnerRequiredSkillModifier(BaseModifier):
    """
    Affects all items which are owner-modifiable
    and have specified skill requirement.
    """

    def __init__(self, id_, domain, state, src_attr, operator, tgt_attr, skill):
        super().__init__(id_, domain, state, src_attr, operator, tgt_attr)
        self.skill = skill

    @property
    def type(self):
        return ModifierType.owner_skillrq

    @property
    def _valid(self):
        return all((
            super()._validate(),
            isinstance(self.skill, int),
            self.domain in (ModifierDomain.ship, ModifierDomain.target)
        ))