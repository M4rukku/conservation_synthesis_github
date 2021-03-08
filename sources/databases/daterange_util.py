import datetime
from datetime import date
from typing import Set, List

class Daterange:
    """A Daterange object represents a timerange between start_date (inclusive) and end_date (exclusive). The internal dates are represented by datetime.date objects.
    
    It has overloaded functions for equality, hashes and comparison. Most operations we will do with daterange objects will be done via the Utility class DaterangeUtility.
    """  
      
    def __init__(self, start_date: date, end_date: date):
        """Creates a new daterange object from a start and end date object.

        Args:
            start_date (datetime.date): The start date of the daterange.
            end_date (datetime.date): The end date of the daterange.
        """        
        if isinstance(start_date, datetime.datetime):
            self._start_date = start_date.date()
        else:
            self._start_date = start_date
        if isinstance(end_date, datetime.datetime):
            self._end_date = end_date.date()
        else:
            self._end_date = end_date

    @staticmethod
    def from_string(start_date: str, end_date: str):
        return Daterange(date.fromisoformat(start_date),
                         date.fromisoformat(end_date))

    def __lt__(self, other):
        """Comparison operator that compares two dateranges based on start_date.

        Args:
            other (Daterange): The Daterange object to compare self to.

        Returns:
            bool : True if start_date is smaller than other.start_date, False otherwise.
        """        
        return self.start_date < other.start_date

    @property
    def start_date(self):
        return self._start_date

    @property
    def end_date(self):
        return self._end_date

    def __eq__(self, other):
        if not isinstance(other, Daterange):
            return False
        else:
            return self.start_date == other.start_date and self.end_date == \
                   other.end_date

    def __hash__(self):
        return hash((self.start_date, self.end_date))

    def __str__(self):
        return f"Daterange: From - {self.start_date.isoformat()}, " \
               f"To - {self.end_date.isoformat()} \n"


class DaterangeUtility:
    """A Utility class that provides different functions to use on Daterange objects.
    """    
    
    @staticmethod
    def intersects(date1: Daterange, date2: Daterange):
        """Intersects returns true, iff date1 and date2 intersect.

        Args:
            date1 (Daterange): The first daterange.
            date2 (Daterange): The second daterange.

        Returns:
            bool: True if date1 and date2 are intersecting, False otherwise.
        """        
        return (date1.start_date <= date2.start_date <= date1.end_date) or \
               (date2.start_date <= date1.start_date <= date2.end_date)

    @staticmethod
    def remove_interval_from_range(to_remove: Daterange, range: Daterange):
        """If there is an intersection between to_remove and range, this function will remove to_remove
        from range and return a list of subranges that define range without to_remove.
        
        Prerequisite - There must be an intersection between to_remove and range.

        Args:
            to_remove (Daterange): The Daterange to remove from range.
            range (Daterange): The daterange on which to operate.

        Returns:
            List[Daterange]: A list of subranges representing range without to_remove.
            
        Example:
            >>> DaterangeUtility().remove_interval_from_range(Daterange(date(2000, 1, 1), date(2000, 5, 1)),
            ...                                               Daterange(date(2000, 1, 1), date(2001, 1, 1)))
            [Daterange(date(2000, 5, 1), date(2001, 1, 1))]
        """        

        # 4 Cases -- R... Remove, D... Daterange
        # R..D..R..D; D..R..R..D; D..R..D..R; R..D..D..R
        if to_remove.start_date <= range.start_date:
            # R..D..R..D or R..D..D..R
            if to_remove.end_date < range.end_date:
                return [Daterange(to_remove.end_date, range.end_date)]
            else:
                return []
        else:  # D..R..R..D; D..R..D..R
            if to_remove.end_date < range.end_date:
                # D..R..R..D
                return [Daterange(range.start_date, to_remove.start_date),
                        Daterange(to_remove.end_date, range.end_date)]
            else:
                return [Daterange(range.start_date, to_remove.start_date)]

    @staticmethod
    def reduce_ranges(ranges_s: Set[Daterange]) -> Set[Daterange]:
        """Takes a set ranges containing Dateranges and combines adjacent and intersecting Dateranges to a reduced form. 
           ... The function will i.e. merge Daterange(date(2000, 1, 1), date(2000, 5, 1)) and Daterange(date(2000, 5, 1), date(2001, 1, 1)
           ... to Daterange(date(2000, 1, 1), date(2001, 1, 1)).

        Args:
            ranges (Set[Daterange]): The set of Dateranges to reduce.

        Returns:
            Set[Daterange]: The Set of reduced Dateranges.
        """        
        if len(ranges_s) == 0:
            return ranges_s
        
        ranges_l: List[Daterange] = list(ranges_s)
        ranges_l.sort()
        new_ranges = set()

        cur_range = ranges_l[0]
        i = 1
        while i < len(ranges_l):
            if cur_range.end_date >= ranges_l[i].start_date:
                cur_range = Daterange(cur_range.start_date,
                                      max(cur_range.end_date,
                                          ranges_l[i].end_date))
            else:
                new_ranges.add(cur_range)
                cur_range = ranges_l[i]
            i = i + 1

        new_ranges.add(cur_range)
        return new_ranges

    @staticmethod
    def remove_known_ranges(known_ranges: Set[Daterange], total_range: Set[Daterange]):
        """If any range in known_ranges is in total_range; this function will 
        ... remove the known_ranges from the set of total_ranges by decomposing each subrange in total_range.

        Args:
            known_ranges (Set[Daterange]): [description]
            total_range (Set[Daterange]): [description]

        Returns:
            Set[Daterange]: The Set total_ranges for which each element does not intersect with any element in known_ranges.
        """        
        known_ranges = DaterangeUtility.reduce_ranges(known_ranges)
        for kr in known_ranges:
            range_cpy = set()
            for subrange in total_range:
                if DaterangeUtility.intersects(kr, subrange):
                    range_cpy.update(
                        DaterangeUtility.
                            remove_interval_from_range(kr, subrange))
                else:
                    range_cpy.add(subrange)
            total_range = range_cpy
        return DaterangeUtility.reduce_ranges(total_range)
