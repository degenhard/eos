#===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2012 Anton Vorobyov
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


from .register.highSlot import HighSlotRegister
from .register.shipItemSize import ShipItemSizeRegister
from .exception import HighSlotException, ShipItemSizeException


class RestrictionTracker:
    def __init__(self, fit):
        self.__fit = fit
        self.__highSlotRegister = HighSlotRegister(fit)
        self.__shipItemSizeRegister = ShipItemSizeRegister(fit)

    def addHolder(self, holder):
        try:
            self.__highSlotRegister.registerHolder(holder)
        except HighSlotException:
            self.__highSlotRegister.unregisterHolder(holder)
            raise
        try:
            self.__shipItemSizeRegister.registerHolder(holder)
        except ShipItemSizeException:
            self.__shipItemSizeRegister.unregisterHolder(holder)
            raise

    def removeHolder(self, holder):
        self.__highSlotRegister.unregisterHolder(holder)
        self.__shipItemSizeRegister.unregisterHolder(holder)

    def validate(self):
        self.__highSlotRegister.validate()
        self.__shipItemSizeRegister.validate()
