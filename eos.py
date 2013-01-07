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


from eos.eve.const import Type
from eos.data.cacheHandler.jsonCacheHandler import JsonCacheHandler
from eos.data.cacheUpdater.updater import CacheUpdater
from eos.fit.fit import Fit
from eos.fit.item.character import Character
from eos.fit.item.ship import Ship
from eos.fit.item.module import Module
from eos.fit.item.charge import Charge
from eos.fit.item.drone import Drone
from eos.fit.item.implant import Implant
from eos.fit.item.rig import Rig
from eos.fit.item.skill import Skill
from eos.fit.item.booster import Booster
from eos.util.logger import Logger


eosVersion = 'git'


class Eos:
    def __init__(self, dataHandler, name='eos'):
        self._logger = Logger(name)
        self._logger.info('session started')
        self._cacheHandler = JsonCacheHandler('/home/dfx/src/pyfa/eos/dataFolder/cache/', name, self._logger)
        # Compare fingerprints from data and cache
        cacheFp = self._cacheHandler.getFingerprint()
        dataVersion = dataHandler.getVersion()
        currentFp = '{}_{}_{}'.format(name, dataVersion, eosVersion)
        # If data version is corrupt or fingerprints mismatch,
        # update cache
        if dataVersion is None or cacheFp != currentFp:
            if dataVersion is None:
                msg = 'data version is None, updating cache'
            else:
                msg = 'fingerprint mismatch: cache "{}", data "{}", updating cache'.format(cacheFp, currentFp)
            self._logger.info(msg)
            # Run cache updater to convert data into eos format
            cacheUpdater = CacheUpdater(self._logger)
            cacheData = cacheUpdater.run(dataHandler)
            self._cacheHandler.updateCache(cacheData, currentFp)

    def makeFit(self):
        fit = Fit(self)
        return fit

    def makeCharacter(self):
        characterType = self._cacheHandler.getType(Type.characterStatic)
        character = Character(characterType)
        return character

    def makeShip(self, typeId):
        shipType = self._cacheHandler.getType(typeId)
        ship = Ship(shipType)
        return ship

    def makeModule(self, typeId):
        moduleType = self._cacheHandler.getType(typeId)
        module = Module(moduleType)
        return module

    def makeCharge(self, typeId):
        chargeType = self._cacheHandler.getType(typeId)
        charge = Charge(chargeType)
        return charge

    def makeDrone(self, typeId):
        droneType = self._cacheHandler.getType(typeId)
        drone = Drone(droneType)
        return drone

    def makeImplant(self, typeId):
        implantType = self._cacheHandler.getType(typeId)
        implant = Implant(implantType)
        return implant

    def makeSkill(self, typeId):
        skillType = self._cacheHandler.getType(typeId)
        skill = Skill(skillType)
        return skill

    def makeRig(self, typeId):
        rigType = self._cacheHandler.getType(typeId)
        rig = Rig(rigType)
        return rig

    def makeBooster(self, typeId):
        boosterType = self._cacheHandler.getType(typeId)
        booster = Booster(boosterType)
        return booster
