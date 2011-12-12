#===============================================================================
# Copyright (C) 2010-2011 Anton Vorobyov
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

import cPickle
import itertools
import os.path
import sys
from ConfigParser import ConfigParser

from reverence import blue

class DataMiner(object):
    """
    Class responsible for getting data out of EVE client
    """
    def __init__(self, evedb, evepath, cachepath, server, release):
        # Will be used by other components in other methods
        self.evepath = evepath
        self.release = release
        # Initialize Reverence cache manager
        try:
            self.eve = blue.EVE(evepath, cachepath=cachepath, server=server)
        except RuntimeError:
            sys.stderr.write("Unable to find EVE cache or it's corrupted, please log into EVE to fix this.\n")
            sys.exit()
        self.cfg = self.eve.getconfigmgr()
        # Set storage container for tables
        self.evedb = evedb

    def run(self):
        """Controls actual data mining workflow"""
        print("Getting data from EVE Client")
        # Add tables from bulkdata and cache
        self.__get_bulkdata()
        # Read localization stuff files
        self.__get_localization()
        # Create metadata table
        self.__add_metadata()
        return

    def __get_bulkdata(self):
        """Read bulkdata"""
        # Assign to local variables for ease of use
        eve = self.eve
        cfg = self.cfg
        evedb = self.evedb
        # Dictionary with data for custom tables, which are not generally available in cache
        customtables = {"dgmoperands":
                            (eve.RemoteSvc('dogma').GetOperandsForChar,
                             "dogma operands data is unavailable"),
                        "invmarketgroups":
                            (eve.RemoteSvc("marketProxy").GetMarketGroups,
                             "market tree data is unavailable; to cache it, open Browse tab of EVE market browser") }
        for tablename in itertools.chain(cfg.tables, customtables.iterkeys()):
            # Create new table object
            table = evedb.add_table(tablename)
            # Get source data object from reverence
            try:
                srcdata = getattr(cfg, tablename)
            except AttributeError:
                try:
                    srcdata = customtables[tablename][0]()
                except IOError:
                    print("Warning: processing table {0} failed: {1}.".format(tablename, customtables[tablename][1]))
                    evedb.remove(table)
                    continue
                except:
                    sys.stderr.write("Error: unable to get data for one of the tables, most likely due to wrong path to EVE client.\n")
                    sys.exit()
            except TypeError:
                sys.stderr.write("Error: unable to get data for one of the tables, most likely due to wrong path to EVE client.\n")
                sys.exit()
            # Get all the data from it
            self.__get_source_data(srcdata, table)
            # If no data was found for this table, remove it
            if len(table.datarows) == 0:
                print("  Warning: skipping table {0} as it doesn't have data rows".format(table.name))
                evedb.remove(table)
        return

    def __get_source_data(self, sourcedata, table):
        """Pull data from the source data structure"""
        # Temporary storage for data rows
        dictdatarows = []
        # Try dumb method of accessing header data (usually works for
        # IndexRowset, CIndexedRowset and FilterRowset)
        try:
            headobj = sourcedata.header
            # Sometimes header data represents itself row descriptor
            # (for CIndexedRowset), get actual list
            try:
                headers = headobj.Keys()
            # Use list itself if such data is unavailable
            except AttributeError:
                headers = headobj
            # For CIndexedRowsets, do some additional things
            else:
                # Reverse keys and values (it's in dbrow : key format)
                sourcedata = dict(zip(sourcedata.itervalues(),sourcedata.iterkeys()))
                # And raise error to go to recursive data seek
                raise AttributeError
        # Try something else (for structures like IndexedRowLists)
        except AttributeError:
            headers = []
            # IndexedRowLists structure may differ from table to table,
            # run recursion on it
            self.__recursive_data_seek(sourcedata, headers, dictdatarows)
        # We got our headers, now get the data
        else:
            # Try to use efficient getter right away, should work for IndexRowset
            try:
                sourcedatalines = sourcedata.Select(*headers)
            # Other method for FilterRowsets
            except AttributeError:
                # Iterate through their keys
                for key in sourcedata.iterkeys():
                    # Grab row sets
                    rowset = sourcedata[key]
                    rowsetdatalines = rowset.Select(*headers)
                    # And process each data row
                    for dataline in rowsetdatalines:
                        datarow = {}
                        for i in range(len(headers)):
                            datarow[headers[i]] = dataline[i]
                        dictdatarows.append(datarow)
            # Process data returned by getter
            else:
                for dataline in sourcedatalines:
                    datarow = {}
                    for i in range(len(headers)):
                        datarow[headers[i]] = dataline[i]
                    dictdatarows.append(datarow)
        # Add columns into table object
        for header in headers:
            table.add_column(header)
        # Cycle through all the data we got
        for dictdatarow in dictdatarows:
            # Also convert ASCII strings to unicode using CCP's default encoding
            for k, v in dictdatarow.iteritems():
                if isinstance(v, str):
                    dictdatarow[k] = unicode(v, "cp1252")
                # Also convert container data types to unicode string
                elif isinstance(v, (tuple, list, set)):
                    dictdatarow[k] = u",".join(unicode(entry) for entry in v)
            # Convert it into tuples
            datarow = tuple(dictdatarow.get(column.name) for column in table)
            # And add to the row set
            table.datarows.add(datarow)
        return

    def __recursive_data_seek(self, sourcedata, headerlist, datarows):
        """Recursively seek for data containers and pull data out of them"""
        # Cycle through top-level data structure
        for iterentity in sourcedata:
            # Check if entities enclosed in it have header data
            try:
                headerdata = iterentity.__header__
            # If there's no such data, then we're dealing with dictionary keys
            except AttributeError:
                dictval = sourcedata[iterentity]
                # Check if these values have header data
                try:
                    headerdata = dictval.__header__
                # If they don't, we're dealing with dictionary or list
                except AttributeError:
                    # Let recursion run on it
                    self.__recursive_data_seek(dictval, headerlist, datarows)
                # Or pull data from dictionary value
                else:
                    datarow = {}
                    for header in headerdata.Keys():
                        datarow[header] = dictval[header]
                        if header not in headerlist:
                            headerlist.append(header)
                    datarows.append(datarow)
            # If top-level data was list, get our data here
            else:
                datarow = {}
                for header in headerdata.Keys():
                    datarow[header] = iterentity[header]
                    if header not in headerlist:
                        headerlist.append(header)
                datarows.append(datarow)
        return

    def __get_localization(self):
        """Read localization stuff files"""
        evedb = self.evedb
        # Read main localization file and unpickle it
        main = cPickle.loads(self.eve.readstuff("res:/localization/localization_main.pickle"))

        # Check for added/removed fields
        known_main_fields = {"maxRevision", "languages", "labels", "mapping", "registration", "types"}
        main_fields = set(main.iterkeys())
        removed = known_main_fields.difference(main_fields)
        if len(removed) > 0:
            plu = "y" if len(removed) == 1 else "ies"
            entries = ", ".join(removed)
            print("  Cannot find entr{0} in main localization file: {1}".format(plu, entries))
        new = main_fields.difference(known_main_fields)
        if len(new) > 0:
            plu = "y" if len(new) == 1 else "ies"
            entries = ", ".join(new)
            print("  New entr{0} in main localization file: {1}".format(plu, entries))

        # maxRevision is not processed
        # Just integer
        # main_types = main["maxRevision"]

        # Process registration table
        # Simple dictionary
        main_registration = main["registration"]
        table = evedb.add_table("trntabcols")
        table.add_column("tcID")
        table.add_column("tcName")
        for tcName, tcID in main_registration.iteritems():
            table.datarows.add((tcID, tcName))

        # Process mapping table
        # Dictionary, where keys are tuples with 2 values
        main_mapping = main["mapping"]
        table = evedb.add_table("trnmapping")
        table.add_column("tcID")
        table.add_column("keyID")
        table.add_column("textID")
        for (tcID, keyID), textID in main_mapping.iteritems():
            table.datarows.add((tcID, keyID, textID))

        # Process labels table
        # Keyed data rows, where each row is dictionary itself
        main_labels = main["labels"]
        table = evedb.add_table("trnlabels")
        # Gather header data (list of column names) and row data
        # (list of dictionaries-rows)
        headers = []
        dictrow_data = []
        for key, dictrow in main_labels.iteritems():
            dictrow = main_labels[key]
            for header in dictrow:
                if not header in headers:
                    headers.append(header)
            dictrow_data.append(dictrow)
        # Create actual columns according to the data we got
        for header in headers:
            table.add_column(header)
        # Form data rows according to our header layout and add them to table
        for dictrow in dictrow_data:
            datarow = tuple(dictrow.get(header) for header in headers)
            table.datarows.add(datarow)

        # Process languages table
        # Layout is same as in previous table
        main_languages = main["languages"]
        table = evedb.add_table("trnlanguages")
        headers = []
        dictrow_data = []
        for key, dictrow in main_languages.iteritems():
            for header in dictrow:
                if not header in headers:
                    headers.append(header)
            dictrow_data.append(dictrow)
        for header in headers:
            table.add_column(header)
        for dictrow in dictrow_data:
            datarow = tuple(dictrow.get(header) for header in headers)
            table.datarows.add(datarow)

        # Process types table
        # Dictionary of dictionaries of lists
        main_types = main["types"]
        table = evedb.add_table("trntypes")
        table.add_column("nounType")
        table.add_column("languageID")
        table.add_column("nounAttribute")
        for entity, langdata in main_types.iteritems():
            for langID, langspec in langdata.iteritems():
                langspec_joined = u",".join(langspec)
                table.datarows.add((entity, langID, langspec_joined))

        # Finally, merge our data tables with actual texts into single super-table
        main_languages = main["languages"]
        table = evedb.add_table("trntexts")
        # First, gather list of available languages
        languages = set()
        for langID in main_languages:
            languages.add(main_languages[langID]["languageID"])
        # Containers for actual table data
        textdata = {}
        for langID in languages:
            # Load data for given language key
            try:
                langpickle = self.eve.readstuff("res:/localization/localization_{0}.pickle".format(langID))
            except IndexError:
                print("  Unable to find data for {0} language, skipping it".format(langID))
                continue
            langdata = cPickle.loads(langpickle)
            # Set of checks on each: first, see if top-level
            # dictionary has just 3 entries
            if len(langdata) != 3:
                print("  Unexpected dictionary size for {0} language data".format(langID))
            if langID != langdata[0]:
                print("  Language key mismatch for {0}, skipping language".format(langID))
                continue
            if langdata[2] != {}:
                print("  Unexpected value in unknown container for {0} language".format(langID))
            # Actual string data for given language
            langtext = langdata[1]
            for textID, text in langtext.iteritems():
                # If ID is not available in generic container, create it and empty
                # dictionary as value (will be data row)
                if not textID in textdata:
                    textdata[textID] = {}
                # Fill our data row
                textdata[textID][langID] = text
        # Now, as we finished gathering data, compose header list
        headers = []
        for dictrow in textdata.itervalues():
            for langID in dictrow:
                if not langID in headers:
                    headers.append(langID)
        # Sort headers and prepend ID column name
        headers.sort()
        headers.insert(0, "textID")
        # Add columns to table
        for header in headers:
            table.add_column(header)
        # Transform rows to include row ID and add them to table as well
        for textID, dictrow in textdata.iteritems():
            dictrow["textID"] = textID
            datarow = tuple(dictrow.get(header) for header in headers)
            table.datarows.add(datarow)
        return

    def __add_metadata(self):
        """Adds metadata table to table structure"""
        # Compose metadata table; first, read client version
        config = ConfigParser()
        config.read(os.path.join(self.evepath, "common.ini"))
        # Convert it to Unicode to make sure columns are detected as text
        evever = unicode(config.getint("main", "build"))
        # Create table object itself
        metatable = self.evedb.add_table("metadata")
        # Add columns to it
        metatable.add_column("fieldName")
        metatable.add_column("fieldValue")
        # Add data
        metatable.datarows.add(("version", evever))
        metatable.datarows.add(("release", self.release))
        return
