# interface for a call set
# Python3 implementation

# IDEAS:
# done - compose methods dynamically depending on results acquired

from imp import reload

import time
import datetime
import sys
import itertools

# field value used to 'segment' sub-callsets by value
disjoin_field  = nca_result

# higher order comparison/filtering functions
def eq(field_index, value):
    return lambda container: container[field_index] == value
def neq(field_index, value):
    return lambda container: container[field_index] != value

# filter a callset by a field entry value (uses above filters)
def filter_by_field(field_index, filter_func, value):
    '''create a filtered iterable of entries by field'''
    return lambda lst: filter(filter_func(field_index, value), lst)

# example filters which can be applied to a callset._entries
# am_f = filter_by_field(5, eq, "Answering-Machine")
# human_f = filter_by_field(5, eq, "Human")

# select specific fields from an iterable
# this function will usually be applied over the 'parent' container/iterable
def field_select(index_lst):
    return lambda container: (container[index] for index in index_lst)

def iter_select(index_lst):
    return lambda iterable: (iter_select([index])(iterable) for index in index_lst)

# shorthand for list composition
def strain(iterable):
    '''compile the values from this iterable into a list'''
    return [i for i in iterable]

# returns the entries of callset in a list
def lst(callset):
    return strain(callset._entries)

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

# instantiate interface for the command-line client
def new_callset(csv_file, logs_dir):
    factory = SetFactory()

    # partition using field index 5
    cs = factory.new_super(disjoin_field, csv_file, logs_dir)
    return factory, cs

# use a factory design pattern you fool!
class SetFactory(object):

    #TODO: consider attaching the factory to the callset itself?
    def new_super(self, subset_field_tag, csv_file, logs_dir):
        cs = CallSet("super", subset_field_tag)
        add_package(cs, csv_file, logs_dir)

        # allocate subsets and attach as attributes of the callset
        for s in cs._subset_tags.keys():
            subset = self.new_subset(cs, filter_by_field(cs._subset_field_index, eq, str(s)))
            self.attach_prop(cs, s, subset)
        return cs

    def attach_prop(self, parent, name, prop):
        # remove spaces and dashes
        name = name.replace('-', '')
        name = name.replace(' ', '')
        setattr(parent, name, prop)

    # gen a new subset to wrap the superset as an attribute
    def new_subset(self, super_set, filter_f):

            # using "containment and delegation"
            class SubSet(CallSet):
                def __init__(self, super_set, filter_func):
                    self._id = 'sub'    # seems like a hack (see CallSet.stats)-> polymorphic approach?
                    self._parent = super_set
                    self._filter = filter_func

                def __getattr__(self, attr):
                   return getattr(self._parent, attr)

                # filter the parent set using the filtering function
                @property
                def _entries(self):
                    return self._filter(self._parent._entries)

            return SubSet(super_set, filter_f)

# class to package on and describe a callset
class CallSet(object):

    def __init__(self, callset_id, subset_field_tag):

        print("assigning callset id: '" + str(callset_id) + "'")
        self._id = callset_id
        self.subset_field_tag = subset_field_tag
        self._subset_field_index = int()
        self._subset_tags = {}
        self._field_mask = []   # normally map this over the 
        self.mask_indices = []

        # counters
        self.num_dup_dest = 0
        self.num_cid_unfound = 0

        # "members" of this call set
        self._fields = {}
        self._entries = []
        self._destinations = set()
        self._log_paths = {}


    def islice(self, start, *stop_step):
        """Access a row in readable form"""
        # TODO: eventually make this print pretty?
        # print('start = ', start)
        stop = 0
        step = None
        if len(stop_step) >= 1:
            stop = stop_step[0]
            if len(stop_step) == 2:
                step = stop_step[1]
        else:
            stop = start + 1

        return itertools.islice(self._entries, start, stop, step)

    def write(self):
        '''write out current data objects as to a CPA package'''
        write_package()

    # search for a call based on field, string pair
    def find(self, pos):
        return None

    def filter(self, field, filter_f, value):
        # subset = factory.subset(self, 
        return None

    @property
    def stats(self, field=None):
        if field == None and type(self) == CallSet:
            #TODO: abstract this such that we cycle through all the subsets of this callset instead of a silly dict?
            table = [[field, count, '{0:.3f} %'.format(float(100 * count/self.length))] for field, count in self._subset_tags.items()]
            table.sort(key=lambda lst: lst[1], reverse=True)
            print_20(table)
        else:
            pass
            # do crazy iterable summing stuff...

        return None

    @property
    def show(self):
        self.print_table(map(self._field_mask, self._entries))

    @property
    def fields(self):
        print_all([self._fields])

    @property
    # consider making the filter_f empty for the super and then this
    # function is defined only once
    def length(self):
        return len([i for i in self._entries])

    @property
    def column_widths(self):
        return [i for i in self._field_mask(self._field_widths)]

    @property
    def display_fields(self):
        return [name for name in self._field_mask(self._fields)]

def add_package(callset, csv_file, logs_dir):
    """ add a new logs package to a callset """

    # open csv file and return a reader/iterator
    try:
        print("opening csv file: '" + csv_file + "'")
        with open(csv_file) as csv_buffer:

            # TODO: add a csv sniffer here to determine an excell dialect?
            csv_reader = csv.reader(csv_buffer)

            # if callset is not populated with datak, gather template info
            if len(callset._entries) == 0:
                callset._title = next(csv_reader)    # first line should be the title
                callset._fields = next(csv_reader)   # second line should be the field names
                callset._field_widths = [0 for i in callset._fields]

                # gather user friendly fields (i.e. fields worth reading on the CLI)
                callset._cid_index = callset._fields.index(cid)
                callset._phone_index = callset._fields.index(phone_num)
                callset._result_index = callset._fields.index(nca_result)
                callset._detail_result_index = callset._fields.index(det_nca_result)

                # make a field mask
                callset.mask_indices = [callset._cid_index, callset._result_index, callset._detail_result_index]
                callset._field_mask = field_select(callset.mask_indices)

                # find the index of the field to use as the disjoint union tag
                callset._subset_field_index = callset._fields.index(callset.subset_field_tag)

                # create a list of indices
                callset.width = len(callset._fields)

            # compile a list of csv/call entries
            print("compiling logs index...")
            for entry in csv_reader:
                # callset._line_num = csv_reader.line_num

                # if we've already seen this phone number then skip the entry
                if entry[callset._phone_index] in callset._destinations:
                    callset.num_dup_dest += 1
                    next
                else:
                    # add destination phone number to our set
                    callset._destinations.add(entry[callset._phone_index])

                    try:
                        # search for log files using call-id field
                        logs = scan_logs(entry[callset._cid_index])

                        if len(logs) == 0:
                            print("WARNING no log files found for cid :",entry[callset._cid_index])
                            callset.num_cid_unfound += 1
                            next
                        else:
                            callset._log_paths[entry[callset._cid_index]] = LogPaths(logs)

                    except subprocess.CalledProcessError as e:
                        print("scanning logs failed with output: " + e.output)

                    # TODO: use the "collections" module here!
                    # keep track of max str lengths for each field
                    i = 0
                    for column in entry:
                        if len(column) > callset._field_widths[i]:
                            callset._field_widths[i] = len(column)
                        i += 1

                    # if all else is good add the entry to our db
                    callset._entries.append(entry)

                    # update the subset tags and compile proportions
                    # TODO: use the "collections" module here!?!?
                    val = entry[callset._subset_field_index]
                    if val not in callset._subset_tags.keys():
                        callset._subset_tags[val] = 1
                    # count up the number of entries with this tag
                    elif val in callset._subset_tags.keys():
                        callset._subset_tags[val] += 1

            # create a printer function
            callset.print_table = printer(obj=callset)

            print(str(callset.num_dup_dest), "duplicate phone number destinations found!"
                 "\n\n", callset.__class__.__name__, "instance created!\n"
                 "type: cs.<tab> to see available properties")

    except csv.Error as err:
        print('file %s, line %d: %s' % (csv_buffer, callset._reader.line_num, err))
        print("Error:", exc)
        sys.exit(1)


# CallSet utilities
def printer(obj=None, field_width=20):
    '''printing closure: use for printing tables (list of lists).
    Use this to create a printer for displaying CallSet content
    NOTE: must be passed a callset AFTER the callset set has been populated
    with data'''

    if type(obj) == CallSet:
    # but how will these update dynamically???
        callset = obj
        widths = callset.column_widths
        fields = callset.display_fields
        for w, l in zip(widths,fields):
            lg = len(l)
            if lg > w:
                widths[widths.index(w)] = lg
    else:
        # use an infinite width generator
        fields = []
        widths = iter(lambda:field_width, 1)

    def printer_function(table):

        # mark as from parent scope
        nonlocal widths
        nonlocal fields

        # print a field title row
        print('')
        print('index | ', end='')
        for f, w in zip(fields, widths):
            print('{field:<{width}}'.format(field=f, width=w), '|', end='')
        print('\n')

        # here a table is normally a list of lists or an iterable over one
        row_index = 0  # for looks
        for row in table:
            print('{0:5}'.format(str(row_index)), '| ', end='')
            for col, w in zip(row, widths):
                print('{column:<{width}}'.format(column=col, width=w), '|', end='')
            print()
            row_index += 1

    return printer_function

# default printer which prints all columns
print_all = printer(field_width=10)
print_20 = printer(field_width=20)

def write_package(callset):
    """Access to a csv writer for writing a new package"""

    # query for package name
    print("Please enter the package name (Enter will use subset name) : ")
    package_name = raw_input()

    print("this would write your new logs package with name ", package_name, "...")
    return None

# routines to be implemented
def parse_xml(logpaths_obj):
    return None
def parse_log_file(logpaths_obj):
    return None
def plot_graph(callset, entry_ranger):
    return None
def ring_in_precon(audiofile):
    return None
