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


from abc import ABCMeta, abstractmethod
from collections import namedtuple
from random import random

from eos.fit.calculator import MutableAttributeMap
from eos.fit.pubsub.message import InputItemAdded, InputItemRemoved, InputEffectsStatusChanged, InstrRefreshSource
from eos.fit.pubsub.subscriber import BaseSubscriber
from eos.fit.null_source import NullSourceItem


EffectData = namedtuple('EffectData', ('effect', 'chance', 'activable'))


class BaseItemMixin(BaseSubscriber, metaclass=ABCMeta):
    """
    Base item class which provides all the data needed for attribute
    calculation to work properly. Not directly subclassed by items,
    but by other mixins (which implement concrete functionality over
    it).

    Required arguments:
    type_id -- ID of eve type ID which should serve as base for this
        item

    Cooperative methods:
    __init__
    """

    def __init__(self, type_id, **kwargs):
        self._eve_type_id = type_id
        # Which container this item is placed to
        self.__container = None
        # Special dictionary subclass that holds modified attributes
        # and data related to their calculation
        self.attributes = MutableAttributeMap(self)
        # Contains IDs of effects which are prohibited to be activated on this item.
        # IDs are stored here without actual effects because we want to keep blocked
        # effect info even when item's fit switches sources
        self.__blocked_effect_ids = set()
        # Which eve type this item wraps. Use null source item by default,
        # as item doesn't have fit with source yet
        self._eve_type = NullSourceItem
        super().__init__(**kwargs)

    @property
    def _container(self):
        return self.__container

    @_container.setter
    def _container(self, new_container):
        charge = getattr(self, 'charge', None)
        old_fit = self._fit
        if old_fit is not None:
            # Unlink fit and contained items first
            if charge is not None:
                old_fit._unsubscribe(charge, charge._handler_map.keys())
                old_fit._publish(InputItemRemoved(charge))
            # Then unlink fit and item itself
            old_fit._unsubscribe(self, self._handler_map.keys())
            old_fit._publish(InputItemRemoved(self))
        self.__container = new_container
        self._refresh_source()
        if charge is not None:
            charge._refresh_source()
        # New fit
        new_fit = self._fit
        if new_fit is not None:
            # Link fit and item itself first
            new_fit._publish(InputItemAdded(self))
            new_fit._subscribe(self, self._handler_map.keys())
            # Then link fit and contained items
            if charge is not None:
                new_fit._publish(InputItemAdded(charge))
                new_fit._subscribe(charge, charge._handler_map.keys())

    @property
    def _fit(self):
        try:
            return self._container._fit
        except AttributeError:
            return None

    @property
    def _other(self):
        if isinstance(self._container, BaseItemMixin):
            return self._container
        else:
            return None

    # Properties used by attribute calculator
    @property
    @abstractmethod
    def _parent_modifier_domain(self):
        ...

    @property
    @abstractmethod
    def _owner_modifiable(self):
        ...

    # Effect methods
    @property
    def _effects_data(self):
        """
        Return map with effects and their item-specific data.

        Return data as dictionary:
        {effect ID: (effect=effect object, chance=chance to apply
            on effect activation, activable=activable flag)}
        """
        data = {}
        for effect in self._eve_type.effects.values():
            # Get chance from modified attributes, if specified
            chance_attr = effect.fitting_usage_chance_attribute
            chance = self.attributes[chance_attr] if chance_attr is not None else None
            # Get effect activable flag
            activable = effect.id not in self.__blocked_effect_ids
            data[effect.id] = EffectData(effect, chance, activable)
        return data

    def _set_effects_activability(self, effect_activability):
        """
        Set activability of effects for this item.

        Required arguments:
        effect_activability -- dictionary in the form of {effect ID:
            activability flag}. Activability flag controls if effect
            should be set as activable or blocked.
        """
        changes = {}
        for effect_id, activability in effect_activability.items():
            if activability and effect_id in self.__blocked_effect_ids:
                changes[effect_id] = activability
                self.__blocked_effect_ids.remove(effect_id)
            elif not activability and effect_id not in self.__blocked_effect_ids:
                changes[effect_id] = activability
                self.__blocked_effect_ids.add(effect_id)
        if len(changes) == 0:
            return
        fit = self._fit
        if fit is not None:
            fit._publish(InputEffectsStatusChanged(self, changes))

    def _randomize_effects_status(self, effect_filter=None):
        """
        Randomize status of effects on this item, take value of
        chance attribute into consideration when necessary.

        Optional arguments:
        effect_filter -- randomize statuses of effects whose IDs
            are in this iterable. When None, randomize all\
            effects. Default is None.
        """
        effect_activability = {}
        for effect_id, data in self._effects_data.items():
            if effect_filter is not None and effect_id not in effect_filter:
                continue
            # If effect is not chance-based, it always gets run
            if data.chance is None:
                effect_activability[effect_id] = True
                continue
            # If it is, roll the floating dice
            if random() < data.chance:
                effect_activability[effect_id] = True
            else:
                effect_activability[effect_id] = False
        self._set_effects_activability(effect_activability)

    @property
    def _activable_effects(self):
        return {eid: e for eid, e in self._eve_type.effects.items() if eid not in self.__blocked_effect_ids}

    @property
    @abstractmethod
    def _active_effects(self):
        ...

    # Message handling
    def _handle_refresh_source(self, _):
        self._refresh_source()

    _handler_map = {
        InstrRefreshSource: _handle_refresh_source
    }

    # Private methods for message handlers
    def _refresh_source(self):
        """
        Each time item's context is changed (the source it relies on,
        which may change when item switches fit or its fit switches
        source), this method should be called; it will refresh data
        which is source-dependent.
        """
        self.attributes.clear()
        try:
            type_getter = self._fit.source.cache_handler.get_type
        # When we're asked to refresh source, but we have no fit or
        # fit has no valid source assigned, we assign NullSource object
        # as eve type - it's needed to raise errors on access to source-
        # dependent stuff
        except AttributeError:
            self._eve_type = NullSourceItem
        else:
            self._eve_type = type_getter(self._eve_type_id)
