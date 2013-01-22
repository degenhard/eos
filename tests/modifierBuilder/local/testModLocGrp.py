#===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2013 Anton Vorobyov
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
#===============================================================================


from eos.const import State, Location, EffectBuildStatus, Context, FilterType, Operator
from eos.tests.modifierBuilder.modBuilderTestCase import ModBuilderTestCase


class TestModLocGrp(ModBuilderTestCase):
    """Test parsing of trees describing modification filtered by location and group"""

    def setUp(self):
        ModBuilderTestCase.setUp(self)
        eTgtLoc = self.ef.make(1, operandId=24, expressionValue='Ship')
        eTgtGrp = self.ef.make(2, operandId=26, expressionGroupId=46)
        eTgtAttr = self.ef.make(3, operandId=22, expressionAttributeId=6)
        eOptr = self.ef.make(4, operandId=21, expressionValue='PostPercent')
        eSrcAttr = self.ef.make(5, operandId=22, expressionAttributeId=1576)
        eTgtItms = self.ef.make(6, operandId=48, arg1Id=eTgtLoc['expressionId'], arg2Id=eTgtGrp['expressionId'])
        eTgtSpec = self.ef.make(7, operandId=12, arg1Id=eTgtItms['expressionId'], arg2Id=eTgtAttr['expressionId'])
        eOptrTgt = self.ef.make(8, operandId=31, arg1Id=eOptr['expressionId'], arg2Id=eTgtSpec['expressionId'])
        self.eAddMod = self.ef.make(9, operandId=7, arg1Id=eOptrTgt['expressionId'], arg2Id=eSrcAttr['expressionId'])
        self.eRmMod = self.ef.make(10, operandId=59, arg1Id=eOptrTgt['expressionId'], arg2Id=eSrcAttr['expressionId'])

    def testGenericBuildSuccess(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 0)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.context, Context.local)
        self.assertEqual(modifier.sourceAttributeId, 1576)
        self.assertEqual(modifier.operator, Operator.postPercent)
        self.assertEqual(modifier.targetAttributeId, 6)
        self.assertEqual(modifier.location, Location.ship)
        self.assertEqual(modifier.filterType, FilterType.group)
        self.assertEqual(modifier.filterValue, 46)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryPassive(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 0)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.offline)
        self.assertEqual(modifier.context, Context.local)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryActive(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 1)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.active)
        self.assertEqual(modifier.context, Context.local)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryTarget(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 2)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.active)
        self.assertEqual(modifier.context, Context.projected)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryArea(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 3)
        self.assertEqual(status, EffectBuildStatus.error)
        self.assertEqual(len(modifiers), 0)
        self.assertEqual(len(self.log), 1)

    def testEffCategoryOnline(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 4)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.online)
        self.assertEqual(modifier.context, Context.local)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryOverload(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 5)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.overload)
        self.assertEqual(modifier.context, Context.local)
        self.assertEqual(len(self.log), 0)

    def testEffCategoryDungeon(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 6)
        self.assertEqual(status, EffectBuildStatus.error)
        self.assertEqual(len(modifiers), 0)
        self.assertEqual(len(self.log), 1)

    def testEffCategorySystem(self):
        modifiers, status = self.runBuilder(self.eAddMod['expressionId'], self.eRmMod['expressionId'], 7)
        self.assertEqual(status, EffectBuildStatus.okFull)
        self.assertEqual(len(modifiers), 1)
        modifier = modifiers[0]
        self.assertEqual(modifier.state, State.offline)
        self.assertEqual(modifier.context, Context.local)
        self.assertEqual(len(self.log), 0)
